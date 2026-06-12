from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Restaurant, Dish, Base
from schemas import (
    RestaurantCreate, RestaurantUpdate, RestaurantResponse,
    DishCreate, DishUpdate, DishResponse,
    ChatRequest, AgentRequest,
)

import anthropic
from dotenv import load_dotenv
# Agent tools and loop — Dish-focused AI agent (Week 6 pattern, scoped to dishes)
from agent import tools, run_agent, get_dishes_fn, update_dish_fn, delete_dish_fn

# Load ANTHROPIC_API_KEY and DATABASE_URL from .env before the app starts
load_dotenv()

# Create all tables defined in models.py if they don't already exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="What's for Lunch API", version="1.0.0")

# Initialize the Anthropic client — reads ANTHROPIC_API_KEY from the environment
ai_client = anthropic.Anthropic()

# CORS — allows the Next.js frontend running on port 3000 to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    # Simple smoke-test endpoint to confirm the API is running
    return {"message": "What's for Lunch API is running"}

@app.get("/health")
def health():
    # Used by monitoring and docker-compose readiness checks
    return {"status": "ok"}


# ── Restaurant CRUD endpoints ─────────────────────────────────────────────────

@app.get("/restaurants", response_model=list[RestaurantResponse])
def get_restaurants(db: Session = Depends(get_db)):
    # Fetch every restaurant row from the database and return as a list
    return db.query(Restaurant).all()


@app.post("/restaurants", response_model=RestaurantResponse, status_code=201)
def create_restaurant(data: RestaurantCreate, db: Session = Depends(get_db)):
    # Unpack the validated request body into a new Restaurant ORM object
    restaurant = Restaurant(**data.model_dump())
    db.add(restaurant)
    db.commit()
    # Refresh loads the DB-generated fields (id, created_at) back onto the object
    db.refresh(restaurant)
    return restaurant


@app.put("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(restaurant_id: int, updates: RestaurantUpdate, db: Session = Depends(get_db)):
    # Look up the restaurant; return 404 if it doesn't exist
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Apply only the fields the client actually sent (skip None values)
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)
    return restaurant


# ── Dish CRUD endpoints ───────────────────────────────────────────────────────

@app.get("/dishes", response_model=list[DishResponse])
def get_dishes(restaurant_id: int | None = None, db: Session = Depends(get_db)):
    # Start with all dishes; optionally narrow to a single restaurant
    query = db.query(Dish)
    if restaurant_id is not None:
        # Filter by foreign key so the client can show dishes per restaurant
        query = query.filter(Dish.restaurant_id == restaurant_id)
    return query.all()


@app.post("/dishes", response_model=DishResponse, status_code=201)
def create_dish(data: DishCreate, db: Session = Depends(get_db)):
    # Verify the parent restaurant exists before inserting the dish
    restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Unpack the validated request body into a new Dish ORM object
    dish = Dish(**data.model_dump())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


@app.put("/dishes/{dish_id}", response_model=DishResponse)
def update_dish(dish_id: int, updates: DishUpdate, db: Session = Depends(get_db)):
    # Look up the dish; return 404 if it doesn't exist
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    # Apply only the fields the client actually sent (skip None values)
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(dish, field, value)

    db.commit()
    db.refresh(dish)
    return dish

@app.delete("/dishes/{dish_id}", status_code=204)
def delete_dish_endpoint(dish_id: int, db: Session = Depends(get_db)):
    # Look up the dish; return 404 if it doesn't exist
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    db.delete(dish)
    db.commit()
    # 204 No Content — successful delete, nothing to return
    return None

# ── AI helper: build context string from the user's data ─────────────────────

def build_lunch_context(db: Session) -> str:
    # Pull every restaurant from the database
    restaurants = db.query(Restaurant).all()
    # Pull every dish from the database
    dishes = db.query(Dish).all()

    # Build the restaurant section of the context string
    context = "Here are the restaurants the user has tracked:\n"
    if restaurants:
        for r in restaurants:
            rating_str = f"{r.user_rating}/5" if r.user_rating else "not yet rated"
            notes_str = f' Notes: "{r.notes}"' if r.notes else ""
            context += f"- {r.name}: {rating_str}, visited {r.visit_count} times.{notes_str}\n"
    else:
        # Let Claude know there's no data yet so it can handle the empty state gracefully
        context += "- No restaurants tracked yet.\n"

    # Build the dish section of the context string
    context += "\nHere are the dishes the user has tracked:\n"
    if dishes:
        # Build a lookup so we can show the restaurant name next to each dish
        restaurant_map = {r.id: r.name for r in restaurants}
        for d in dishes:
            rating_str = f"{d.user_rating}/5" if d.user_rating else "not yet rated"
            restaurant_name = restaurant_map.get(d.restaurant_id, "unknown restaurant")
            notes_str = f' Notes: "{d.notes}"' if d.notes else ""
            context += (
                f"- {d.name} at {restaurant_name}: {rating_str}, "
                f"ordered {d.times_ordered} times.{notes_str}\n"
            )
    else:
        context += "- No dishes tracked yet.\n"

    return context


def build_system_prompt(context: str) -> str:
    # Assembles the full system prompt that is injected into every AI call
    return f"""You are a personal lunch advisor for an office worker near zip code 95134 (North San Jose).
Your job is to give fast, specific, personalized lunch recommendations based on the user's own history.

{context}

When making recommendations:
- Reference specific restaurants and dishes the user has rated highly
- Mention how long it has been since they visited (use visit counts as a proxy)
- Suggest something they haven't tried recently if they've been going to the same place repeatedly
- Keep your answer concise — one clear recommendation with a one-sentence reason is ideal
- If no data exists yet, suggest they start tracking a few visits so you can personalize advice"""


# ── AI endpoint: single recommendation ───────────────────────────────────────

@app.post("/ai/recommend")
def get_recommendation(request: ChatRequest, db: Session = Depends(get_db)):
    # Build a plain-text summary of the user's entire rating history
    context = build_lunch_context(db)
    # Inject the context into the system prompt so Claude knows the user's data
    system_prompt = build_system_prompt(context)

    # Combine prior conversation turns with the new message
    messages = request.conversation_history + [
        {"role": "user", "content": request.message}
    ]

    # Send to Claude — claude-sonnet-4-6 gives high-quality, context-aware answers
    response = ai_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system_prompt,
        messages=messages,
    )

    # Extract the text content from Claude's response object
    reply = response.content[0].text

    # Return the reply and the full updated history so the frontend can store it
    return {
        "reply": reply,
        "updated_history": messages + [{"role": "assistant", "content": reply}],
    }


# ── AI endpoint: multi-turn conversational assistant ─────────────────────────

@app.post("/ai/chat")
def chat_with_assistant(request: ChatRequest, db: Session = Depends(get_db)):
    # Same context injection as /ai/recommend — every chat turn knows the user's data
    context = build_lunch_context(db)
    system_prompt = build_system_prompt(context)

    # Combine the stored conversation history with the new user message
    messages = request.conversation_history + [
        {"role": "user", "content": request.message}
    ]

    # Larger max_tokens here allows richer back-and-forth conversation
    response = ai_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    # Extract the text content from Claude's response object
    reply = response.content[0].text

    # Return the reply and the updated history for the frontend to store and send next turn
    return {
        "reply": reply,
        "updated_history": messages + [{"role": "assistant", "content": reply}],
    }

# ── AI endpoint: action-taking agent (dish CRUD via tool use) ────────────────

@app.post("/ai/agent")
def run_dish_agent(request: AgentRequest, db: Session = Depends(get_db)):
    # Build "1: BJ's Restaurant\n2: Chipotle\n..." so Claude can resolve
    # restaurant names without an extra tool call (dishes only store restaurant_id)
    restaurants = db.query(Restaurant).all()
    restaurant_context = "\n".join(f"{r.id}: {r.name}" for r in restaurants)

    # Wrapper functions close over `db` so agent.py's *_fn functions
    # (which are generic and take db as their first argument) can be
    # called by run_agent with just the arguments Claude provides
    def get_dishes_wrapper(restaurant_id: int | None = None):
        return get_dishes_fn(db, restaurant_id)

    def update_dish_wrapper(id: int, **updates):
        return update_dish_fn(db, id, **updates)

    def delete_dish_wrapper(id: int):
        return delete_dish_fn(db, id)

    # Keys MUST match the "name" fields in agent.py's tools list exactly
    tool_functions = {
        "get_dishes": get_dishes_wrapper,
        "update_dish": update_dish_wrapper,
        "delete_dish": delete_dish_wrapper,
    }

    reply, agent_steps, updated_history = run_agent(
        request.message,
        request.conversation_history,
        tools,
        tool_functions,
        restaurant_context=restaurant_context,
    )

    return {
        "response": reply,
        "agent_steps": agent_steps,
        "updated_history": updated_history,
    }