# agent.py
# Dish-focused AI agent for What's For Lunch — Week 6 pattern, scoped down.
# Provides: tool schemas, tool functions (get/update/delete dish), and the agent loop.

import json
import anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models import Dish

# Defensive load — works even if this file is imported standalone for testing
load_dotenv()
client = anthropic.Anthropic()


# ── PART 1: Tool schemas ────────────────────────────────────────────────────
# These are sent to Claude with every /ai/agent request. Claude reads the
# "description" fields as BEHAVIORAL INSTRUCTIONS, not just documentation —
# the disambiguation wording below is doing real work (Week 6 lesson §5.1).

tools = [
    {
        "name": "get_dishes",
        "description": (
            "List dishes, optionally filtered to one restaurant. Use this first "
            "whenever the user refers to a dish by name rather than by id — "
            "you need the id before you can update or delete anything."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {
                    "type": "integer",
                    "description": "Optional — limit results to dishes at this restaurant."
                }
            },
            "required": []
        }
    },
    {
        "name": "update_dish",
        "description": (
            "Update a dish's rating, times ordered, category, or vegetarian/spicy tags. "
            "Requires the dish's id — call get_dishes first if you only know the name. "
            "If multiple dishes could match what the user described, ask which one "
            "they mean before updating."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The dish's integer id — must come from a get_dishes result in this same turn. Never use a placeholder or a value from memory."},
                "user_rating": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "New rating, 1-5."
                },
                "times_ordered": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "New times-ordered count."
                },
                "category": {"type": "string", "description": "New category, e.g. 'meal' or 'drink'."},
                "is_vegetarian": {"type": "boolean"},
                "is_spicy": {"type": "boolean"}
            },
            "required": ["id"]
        }
    },
    {
        "name": "delete_dish",
        "description": (
            "Permanently delete a dish by id. Call get_dishes first to find the id. "
            "If multiple dishes could match the user's description (e.g. two dishes "
            "with similar names), ask which one they mean before deleting."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The dish's id to delete."}
            },
            "required": ["id"]
        }
    },
]


# ── PART 2: Tool functions ──────────────────────────────────────────────────
# Each function takes a `db` session (the endpoint will close over it) plus
# whatever arguments Claude supplies, and returns a plain dict — never an
# ORM object directly, since that can't be JSON-serialized back to Claude.

def get_dishes_fn(db: Session, restaurant_id: int | None = None) -> dict:
    # Start with every dish, narrow down if a restaurant_id was given
    query = db.query(Dish)
    if restaurant_id is not None:
        query = query.filter(Dish.restaurant_id == restaurant_id)
    dishes = query.all()

    # Return plain dicts — SQLAlchemy objects aren't JSON-serializable
    return {
        "dishes": [
            {
                "id": d.id,
                "name": d.name,
                "restaurant_id": d.restaurant_id,
                "category": d.category,
                "user_rating": d.user_rating,
                "times_ordered": d.times_ordered,
                "is_vegetarian": d.is_vegetarian,
                "is_spicy": d.is_spicy,
            }
            for d in dishes
        ]
    }


def update_dish_fn(db: Session, id: int, **updates) -> dict:
    # Look up the dish — if it doesn't exist, tell Claude (don't crash)
    dish = db.query(Dish).filter(Dish.id == id).first()
    if not dish:
        return {"error": f"No dish found with id {id}"}

    # Defense in depth (Week 6 §5.2): the JSON Schema "minimum"/"maximum" only
    # GUIDES Claude — this Python check is the actual server-side guard.
    if "user_rating" in updates and updates["user_rating"] is not None:
        rating = updates["user_rating"]
        if not (1 <= rating <= 5):
            return {"error": "user_rating must be between 1 and 5 — no changes made."}

    # Capture the OLD value of every field we're about to overwrite.
    # This is what powers the frontend "Undo" button — without this dict,
    # there'd be no way to revert the change later.
    previous_value = {}
    for field, value in updates.items():
        if value is not None:
            previous_value[field] = getattr(dish, field)
            setattr(dish, field, value)

    # No fields to update (all None) — nothing changed, report that clearly
    if not previous_value:
        return {"error": "No updatable fields were provided."}

    db.commit()
    db.refresh(dish)

    return {
        "id": dish.id,
        "name": dish.name,
        "updated_fields": list(previous_value.keys()),
        "previous_value": previous_value,  # <-- frontend Undo button uses this
        "current_value": {field: getattr(dish, field) for field in previous_value},
    }


def delete_dish_fn(db: Session, id: int) -> dict:
    # Look up the dish — if it doesn't exist, tell Claude (don't crash)
    dish = db.query(Dish).filter(Dish.id == id).first()
    if not dish:
        return {"error": f"No dish found with id {id}"}

    # Save the name before deleting — needed for the agent_steps action log
    name = dish.name
    db.delete(dish)
    db.commit()

    return {"id": id, "name": name, "deleted": True}


# ── PART 3: The agent loop ──────────────────────────────────────────────────

def run_agent(
    user_message: str,
    conversation_history: list[dict],
    tools: list[dict],
    tool_functions: dict,
    restaurant_context: str = "",   # NEW — e.g. "1: BJ's Restaurant\n2: Chipotle\n..."
    max_iterations: int = 10,
):
    """
    Runs Claude in a tool-use loop until it produces a final text answer.

    conversation_history: simple [{role, content: str}, ...] — SAME shape as
    /ai/chat and /ai/recommend use. This function builds its own internal
    working list (with tool_use/tool_result blocks) for the API calls, but
    returns updated_history in the same simple shape so the frontend doesn't
    need any new types.

    Returns: (final_text, agent_steps, updated_history)
    """

    system_prompt = (
        "You are an action-taking assistant for a lunch tracker app. "
        "You can look up, update, and delete dishes. "
        "Be concise in your final response — confirm what you did in one "
        "or two sentences.\n\n"
        "WORKFLOW — follow this exact sequence for every update or delete request:\n"
        "1. Call get_dishes to retrieve the current dish list.\n"
        "2. Identify the correct dish by matching name and restaurant from the result.\n"
        "3. Extract its integer `id` field from that result.\n"
        "4. Call update_dish or delete_dish using ONLY that integer id.\n"
        "NEVER call update_dish or delete_dish without completing steps 1-3 in the SAME turn. "
        "NEVER assume you already know a dish's id from previous conversation turns — "
        "ids must always come from a fresh get_dishes call.\n\n"
        "Formatting rules:\n"
        "- Never use markdown pipe-table syntax (| columns | like | this |). "
        "Use plain prose or dash-bullet lists instead.\n"
        "- When listing multiple dishes, always group them by category in this order: "
        "Meals first, then Sides, then Drinks. Use a bold header for each group "
        "(e.g. **Meals**, **Sides / Bakery**, **Drinks**). "
        "Within each group, sort by rating descending (highest first). "
        "Example entry: - Garlic Knots (BJ's Restaurant) — 5.0★, ordered 3 times\n\n"
        "Category semantics — every dish has one of three category values:\n"
        "- 'meal': main dishes (pizza, sandwiches, burritos, kebabs, pasta, etc.)\n"
        "- 'side': accompaniments AND bakery/dessert items (salads, cookies, muffins, chips, bread, sauces, etc.)\n"
        "- 'drink': beverages only (coffee, juice, latte, cold brew, etc.)\n\n"
        "Filtering rules — apply these strictly and NEVER mix categories across a filter boundary:\n"
        "- DRINKS ONLY: if the user mentions coffee, tea, latte, cold brew, juice, drinks, or beverages → "
        "show category == 'drink' only. Do not include any meals or sides.\n"
        "- MEALS ONLY: if the user asks for a dish, food, something to eat, lunch, or a main → "
        "show category == 'meal' only. Do not include sides (cookies, salads, chips) or drinks.\n"
        "- SIDES ONLY: if the user asks for a dessert, snack, bakery item, or side → "
        "show category == 'side' only.\n"
        "- SPICY / VEGETARIAN: these are attributes of food, never beverages. "
        "When the user asks for something spicy or vegetarian, filter by category == 'meal' or 'side' only. "
        "Never suggest a drink as a spicy or vegetarian option.\n"
        "- When no category is implied, show all categories grouped as described above.\n\n"
        f"Restaurant id-to-name mapping (dishes reference restaurants by id only):\n"
        f"{restaurant_context}"
    )

    # Internal working messages — starts from the plain history, converted
    # to the format the Anthropic API expects (content as plain strings is fine
    # for prior turns; tool blocks only get added for THIS turn's reasoning)
    messages = [
        {"role": turn["role"], "content": turn["content"]}
        for turn in conversation_history
    ] + [{"role": "user", "content": user_message}]

    # agent_steps is built INCREMENTALLY inside the loop (Week 6 §5.3 "paper trail")
    agent_steps: list[dict] = []

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # Always append Claude's response to the working messages so it has
        # context for the next loop iteration if more tool calls are needed
        messages.append({"role": "assistant", "content": response.content})

        # If Claude is done (not asking for a tool), find its text and return
        if response.stop_reason != "tool_use":
            for block in response.content:
                if block.type == "text":
                    updated_history = conversation_history + [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": block.text},
                    ]
                    return block.text, agent_steps, updated_history

            # Fallback per Week 6 §6 — avoid an infinite-spin if no text block exists
            updated_history = conversation_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": "Done."},
            ]
            return "Agent finished with no text response.", agent_steps, updated_history

        # Claude wants to use one or more tools — run each one and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = tool_functions.get(block.name)
                if fn:
                    try:
                        result = fn(**block.input)
                    except Exception as exc:
                        # Surface the exception as an error dict so Claude can
                        # tell the user what went wrong instead of crashing the request
                        result = {"error": f"Tool '{block.name}' raised an exception: {exc}"}
                else:
                    result = {"error": f"Unknown tool: {block.name}"}

                # Record this step in the paper trail — visible in the
                # frontend's "Agent Actions" panel
                agent_steps.append({
                    "tool": block.name,
                    "input": block.input,
                    "result": result,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        # Feed the tool results back to Claude as the next "user" turn
        messages.append({"role": "user", "content": tool_results})

    # Safety valve — if we somehow loop max_iterations times without a final answer
    updated_history = conversation_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": "Reached the step limit before finishing."},
    ]
    return "Agent reached the maximum number of steps.", agent_steps, updated_history