from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Restaurant schemas ────────────────────────────────────────────────────────

class RestaurantCreate(BaseModel):
    # All fields the client sends when adding a new restaurant
    name: str
    address: Optional[str] = None
    zip_code: Optional[str] = None
    cuisine_tag: Optional[str] = None
    user_rating: Optional[float] = None   # null until the user rates it
    visit_count: int = 0                  # starts at zero on creation
    notes: Optional[str] = None


class RestaurantUpdate(BaseModel):
    # Every field is optional so the client can send only what changed
    name: Optional[str] = None
    address: Optional[str] = None
    zip_code: Optional[str] = None
    cuisine_tag: Optional[str] = None
    user_rating: Optional[float] = None
    visit_count: Optional[int] = None
    notes: Optional[str] = None


class RestaurantResponse(BaseModel):
    # Full representation returned to the client, including DB-generated fields
    id: int
    name: str
    address: Optional[str]
    zip_code: Optional[str]
    cuisine_tag: Optional[str]
    user_rating: Optional[float]
    visit_count: int
    notes: Optional[str]
    created_at: datetime

    # Allows Pydantic to read values from SQLAlchemy ORM objects (not just dicts)
    model_config = {"from_attributes": True}


# ── Dish schemas ──────────────────────────────────────────────────────────────

class DishCreate(BaseModel):
    # All fields the client sends when adding a new dish
    name: str
    restaurant_id: int                    # must reference an existing restaurant
    category: Optional[str] = None
    price_range: Optional[str] = None
    user_rating: Optional[float] = None   # null until the user rates it
    times_ordered: int = 0                # starts at zero on creation
    notes: Optional[str] = None
    is_vegetarian: bool = False           # True if the dish contains no meat or animal products
    is_spicy: bool = False                # True if the dish is notably spicy


class DishUpdate(BaseModel):
    # Every field is optional so the client can send only what changed
    name: Optional[str] = None
    category: Optional[str] = None
    price_range: Optional[str] = None
    user_rating: Optional[float] = None
    times_ordered: Optional[int] = None
    notes: Optional[str] = None
    is_vegetarian: Optional[bool] = None  # True if the dish contains no meat or animal products
    is_spicy: Optional[bool] = None       # True if the dish is notably spicy


class DishResponse(BaseModel):
    # Full representation returned to the client, including DB-generated fields
    id: int
    name: str
    restaurant_id: int
    category: Optional[str]
    price_range: Optional[str]
    user_rating: Optional[float]
    times_ordered: int
    notes: Optional[str]
    is_vegetarian: bool                   # True if the dish contains no meat or animal products
    is_spicy: bool                        # True if the dish is notably spicy
    created_at: datetime

    # Allows Pydantic to read values from SQLAlchemy ORM objects (not just dicts)
    model_config = {"from_attributes": True}


# ── AI request schema ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    # The user's latest message to send to Claude
    message: str
    # All previous turns in the conversation so Claude has full context
    # Each dict has "role" ("user" or "assistant") and "content" (the text)
    conversation_history: list[dict] = []

# Request schema for the agent endpoint — same shape as ChatRequest,
# kept separate in case agent-specific fields are added later
class AgentRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []