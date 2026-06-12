# test_agent.py — standalone smoke test for agent.py, before wiring into main.py
from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal  # adjust if your session factory has a different name
from agent import tools, run_agent, get_dishes_fn, update_dish_fn, delete_dish_fn

db = SessionLocal()

def get_dishes_wrapper(restaurant_id=None):
    return get_dishes_fn(db, restaurant_id)

def update_dish_wrapper(id, **updates):
    return update_dish_fn(db, id, **updates)

def delete_dish_wrapper(id):
    return delete_dish_fn(db, id)

tool_functions = {
    "get_dishes": get_dishes_wrapper,
    "update_dish": update_dish_wrapper,
    "delete_dish": delete_dish_wrapper,
}

# Test 1 — simple read
text, steps, history = run_agent("What dishes does Dishdash have?", [], tools, tool_functions)
print("REPLY:", text)
print("STEPS:", steps)

db.close()

# Test 2 — update_dish: bump a rating, verify previous_value is captured
print("\n--- TEST 2: update_dish ---")
text, steps, history = run_agent(
    "Set the rating for Garlic Knots to 5 and add a note that I loved it... "
    "actually skip the note, just update the rating to 5.",
    [],
    tools,
    tool_functions,
)
print("REPLY:", text)
print("STEPS:", steps)

# Test 3 — delete_dish: lookup-then-act, same shape as Week 6 Test 4
print("\n--- TEST 3: delete_dish ---")
text, steps, history = run_agent(
    "Delete the dish called 'Plain Rice' if it exists, otherwise tell me it doesn't exist.",
    [],
    tools,
    tool_functions,
)
print("REPLY:", text)
print("STEPS:", steps)

# Test 4 — restaurant_context injection: does Claude resolve "Dishdash" directly now?
print("\n--- TEST 4: restaurant_context injection ---")

# Hardcoded for testing — inferred from Test 1's dish patterns + DISTANCES_FROM_CSTU
# (restaurant 3 = Middle Eastern dishes = likely Dishdash)
fake_restaurant_context = (
    "1: BJ's Restaurant\n"
    "2: Chipotle\n"
    "3: Dishdash\n"
    "4: King Eggroll\n"
    "5: Mendocino Farms\n"
    "6: Panera"
)

text, steps, history = run_agent(
    "What dishes does Dishdash have?",
    [],
    tools,
    tool_functions,
    restaurant_context=fake_restaurant_context,  # NEW param
)
print("REPLY:", text)
print("STEPS (tool names only):", [s["tool"] for s in steps])