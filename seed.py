import random
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Restaurant, Dish

# Load DATABASE_URL from the .env file into the process environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine and session factory — same pattern as database.py
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def random_rating():
    # Returns a float between 1.0 and 5.0 rounded to one decimal place
    return round(random.uniform(1.0, 5.0), 1)


def random_visits():
    # Returns an integer between 1 and 8 representing how many times the user visited
    return random.randint(1, 8)


def random_ordered():
    # Returns an integer between 1 and 5 representing how many times the user ordered the dish
    return random.randint(1, 5)


# Each entry is a restaurant dict with a nested list of (dish_name, category) tuples.
# zip_code is set to "95134" for all restaurants per project requirements.
SEED_DATA = [
    {
        "name": "BJ's Restaurant",
        "cuisine_tag": "american",
        "address": "3294 Stevens Creek Blvd, San Jose, CA 95134",
        "dishes": [
            # sides
            ("Caesar Salad",                        "side"),
            ("Chocolate Chunk Cookies",              "side"),
            ("Garlic Knots",                         "side"),
            ("House Salad",                          "side"),
            ("Seasonal Fresh Fruit Platter",         "side"),
            ("Tray of Potato Chips",                 "side"),
            # meals
            ("3 Large Deep Dish Pizzas",             "meal"),
            ("Barbeque Chicken Deep Dish Pizza",     "meal"),
            ("BJ's Favorite Deep Dish Pizza",        "meal"),
            ("Burger Sliders",                       "meal"),
            ("California Chicken Club Mini Sandwiches", "meal"),
            ("Fresh Atlantic Salmon",                "meal"),
            ("Greek Veggie Mini Sandwiches",         "meal"),
            ("Grilled Chicken Alfredo Pasta",        "meal"),
            ("No Meat Alfredo Pasta",                "meal"),
            ("Sal's Brewhouse Chicken",              "meal"),
            ("Vegetarian Deep Dish Pizza",           "meal"),
            ("Veggie Pasta",                         "meal"),
        ],
    },
    {
        "name": "Chipotle",
        "cuisine_tag": "mexican",
        "address": "510 Brokaw Rd, San Jose, CA 95134",
        "dishes": [
            # sides
            ("Black Beans and Pinto Beans",                         "side"),
            ("Chips",                                               "side"),
            ("Cilantro-Lime White Rice and Brown Rice",             "side"),
            ("Dips (Guacamole Queso Blanco Salsas)",                "side"),
            ("Fajita Veggies",                                      "side"),
            ("Flour Tortillas",                                     "side"),
            ("Salad Lettuce and Taco Lettuce",                      "side"),
            ("Shredded Cheese",                                     "side"),
            ("Sour Cream",                                          "side"),
            # meals
            ("Chicken",                                             "meal"),
            ("Sofritas Plant-Based Protein",                        "meal"),
            ("Steak",                                               "meal"),
        ],
    },
    {
        "name": "Dishdash",
        "cuisine_tag": "mediterranean",
        "address": "190 S Murphy Ave, Sunnyvale, CA 95134",
        "dishes": [
            # sides
            ("Basil Pesto Shells",                              "side"),
            ("Basmati Rice",                                    "side"),
            ("House Salad",                                     "side"),
            ("Hummus",                                          "side"),
            ("Pita Bread",                                      "side"),
            ("Spicy Garlic-Yogurt and Cilantro Mint Sauces",   "side"),
            # meals
            ("Chicken Kebab",           "meal"),
            ("Chicken Shawarma Wrap",   "meal"),
            ("Falafel Wrap",            "meal"),
            ("Kufta Kebab",             "meal"),
        ],
    },
    {
        "name": "King Eggroll",
        "cuisine_tag": "chinese",
        "address": "1560 Berryessa Rd, San Jose, CA 95133",
        "dishes": [
            # sides
            ("Chicken Eggrolls",    "side"),
            ("Veggie Eggrolls",     "side"),
            # meals
            ("Beef Broccoli",       "meal"),
            ("Orange Chicken",      "meal"),
            ("Shaken Tofu",         "meal"),
            ("Veggie Chow Mein",    "meal"),
            ("Veggie Fried Rice",   "meal"),
        ],
    },
    {
        "name": "Mendocino Farms",
        "cuisine_tag": "sandwich",
        "address": "3970 Freedom Circle, Santa Clara, CA 95054",
        "dishes": [
            # sides
            ("Assorted Cookies",    "side"),
            ("Basil Pesto Shells",  "side"),
            # meals
            ("Chicken Pesto Caprese Sandwich",          "meal"),
            ("Chimichurri Steak and Bacon Sandwich",    "meal"),
            ("Mario's Caprese Sandwich",                "meal"),
            ("Not So Fried Chicken Sandwich",           "meal"),
            ("Pink Lady Apple and Goat Cheese Salad",   "meal"),
            ("Prosciutto and Chicken Sandwich",         "meal"),
            ("The Farm Club Sandwich",                  "meal"),
            ("Turkey Avo Salsa Verde Sandwich",         "meal"),
        ],
    },
    {
        "name": "Panera",
        "cuisine_tag": "bakery-cafe",
        "address": "3055 Olin Ave, San Jose, CA 95128",
        "dishes": [
            # sides
            ("Butter",              "side"),
            ("Cream Cheese",        "side"),
            ("Large Fruit Bowl",    "side"),
            # meals
            ("Assorted Bagels and Pastries",    "meal"),
            ("Greek Yogurt with Berries Parfait", "meal"),
            # drinks
            ("Coffee",          "drink"),
            ("Orange Juice",    "drink"),
        ],
    },
]


def seed():
    db = SessionLocal()
    try:
        # ── Clear existing data ──────────────────────────────────────────────
        # Delete dishes before restaurants to avoid foreign key constraint errors
        db.query(Dish).delete()
        db.query(Restaurant).delete()
        db.commit()
        print("Cleared existing dishes and restaurants.")

        # ── Insert restaurants and their dishes ──────────────────────────────
        for entry in SEED_DATA:
            # Create the restaurant row with a random rating and visit count
            restaurant = Restaurant(
                name=entry["name"],
                address=entry["address"],
                zip_code="95134",           # project scope: all tagged to 95134
                cuisine_tag=entry["cuisine_tag"],
                user_rating=random_rating(),
                visit_count=random_visits(),
            )
            db.add(restaurant)
            # Flush writes the row and populates restaurant.id without committing yet
            db.flush()
            print(f"  Inserted restaurant: {restaurant.name} "
                  f"(rating={restaurant.user_rating}, visits={restaurant.visit_count})")

            # Insert every dish linked to this restaurant
            for dish_name, category in entry["dishes"]:
                dish = Dish(
                    name=dish_name,
                    restaurant_id=restaurant.id,    # FK set after flush populated the PK
                    category=category,
                    user_rating=random_rating(),
                    times_ordered=random_ordered(),
                )
                db.add(dish)

            # Flush the dish batch so the print below reflects what's staged
            db.flush()
            dish_count = len(entry["dishes"])
            print(f"    Inserted {dish_count} dishes for {restaurant.name}.")

        # Commit all inserts in one transaction
        db.commit()
        print("\nSeed complete. All restaurants and dishes inserted.")

    except Exception as e:
        # Roll back the entire transaction if anything went wrong
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
