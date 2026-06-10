from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone


# Base class for all SQLAlchemy models — every model inherits from this
class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    # Maps this class to the "restaurants" table in PostgreSQL
    __tablename__ = "restaurants"

    # Primary key — auto-incremented by the database
    id = Column(Integer, primary_key=True, index=True)

    # Restaurant name, required
    name = Column(String, nullable=False)

    # Street address, e.g. "1355 N 1st St"
    address = Column(String, nullable=True)

    # Zip code scoped to the user's workplace area
    zip_code = Column(String, nullable=True)

    # Broad food type, e.g. "sandwich", "Vietnamese", "deli"
    cuisine_tag = Column(String, nullable=True)

    # User's personal 1.0–5.0 rating; null until they rate it
    user_rating = Column(Float, nullable=True)

    # Total number of times the user has logged a visit; starts at 0
    visit_count = Column(Integer, default=0)

    # Free-text personal notes, e.g. "ask for extra pickles"
    notes = Column(Text, nullable=True)

    # Automatically set to the current UTC time when the row is first inserted
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One restaurant can have many dishes; cascade delete removes dishes when restaurant is deleted
    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")


class Dish(Base):
    # Maps this class to the "dishes" table in PostgreSQL
    __tablename__ = "dishes"

    # Primary key — auto-incremented by the database
    id = Column(Integer, primary_key=True, index=True)

    # Dish name, required, e.g. "Turkey Club"
    name = Column(String, nullable=False)

    # Foreign key linking this dish to its parent restaurant
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    # Food category, e.g. "sandwich", "salad", "soup"
    category = Column(String, nullable=True)

    # Rough price tier: "$" or "$$"
    price_range = Column(String, nullable=True)

    # User's personal 1.0–5.0 rating; null until they rate it
    user_rating = Column(Float, nullable=True)

    # How many times the user has ordered this dish; starts at 0
    times_ordered = Column(Integer, default=0)

    # Free-text personal notes, e.g. "get it spicy"
    notes = Column(Text, nullable=True)

    # True if the dish contains no meat or animal products
    is_vegetarian = Column(Boolean, default=False)

    # True if the dish is notably spicy
    is_spicy = Column(Boolean, default=False)

    # Automatically set to current UTC time on insert
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Back-reference to the parent Restaurant object
    restaurant = relationship("Restaurant", back_populates="dishes")
