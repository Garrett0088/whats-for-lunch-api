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


# Each entry is a restaurant dict with a nested list of 4-tuples:
#   (dish_name, category, is_vegetarian, is_spicy)
# zip_code is set to "95134" for all restaurants per project requirements.
SEED_DATA = [
    {
        "name": "BJ's Restaurant",
        "cuisine_tag": "american",
        "address": "3294 Stevens Creek Blvd, San Jose, CA 95134",
        "dishes": [
            # (name, category, is_vegetarian, is_spicy)
            # sides
            ("Caesar Salad",                            "side", False, False),
            ("Chocolate Chunk Cookies",                 "side", True,  False),
            ("Garlic Knots",                            "side", True,  False),
            ("House Salad",                             "side", True,  False),
            ("Seasonal Fresh Fruit Platter",            "side", True,  False),
            ("Tray of Potato Chips",                    "side", True,  False),
            # meals
            ("3 Large Deep Dish Pizzas",                "meal", False, False),
            ("Barbeque Chicken Deep Dish Pizza",        "meal", False, False),
            ("BJ's Favorite Deep Dish Pizza",           "meal", False, False),
            ("Burger Sliders",                          "meal", False, False),
            ("California Chicken Club Mini Sandwiches", "meal", False, False),
            ("Fresh Atlantic Salmon",                   "meal", False, False),
            ("Greek Veggie Mini Sandwiches",            "meal", True,  False),
            ("Grilled Chicken Alfredo Pasta",           "meal", False, False),
            ("No meat Alfredo Pasta",                   "meal", True,  False),
            ("Sal's Brewhouse Chicken",                 "meal", False, False),
            ("Vegetarian Deep Dish Pizza",              "meal", True,  False),
            ("Veggie Pasta",                            "meal", True,  True),
        ],
    },
    {
        "name": "Chipotle",
        "cuisine_tag": "mexican",
        "address": "510 Brokaw Rd, San Jose, CA 95134",
        "dishes": [
            # sides
            ("Black Beans and Pinto Beans",                 "side", True,  False),
            ("Chips",                                       "side", True,  False),
            ("Cilantro-Lime White Rice and Brown Rice",     "side", True,  False),
            ("Dips (Guacamole, Queso Blanco, Salsas)",      "side", True,  True),
            ("Fajita Veggies",                              "side", True,  False),
            ("Flour Tortillas",                             "side", True,  False),
            ("Salad Lettuce and Taco Lettuce",              "side", True,  False),
            ("Shredded Cheese",                             "side", True,  False),
            ("Sour Cream",                                  "side", True,  False),
            # meals
            ("Chicken",                                     "meal", False, False),
            ("Sofritas Plant-Based Protein",                "meal", True,  False),
            ("Steak",                                       "meal", False, False),
        ],
    },
    {
        "name": "Dishdash",
        "cuisine_tag": "mediterranean",
        "address": "190 S Murphy Ave, Sunnyvale, CA 95134",
        "dishes": [
            # sides
            ("Basil Pesto Shells",                          "side", True,  False),
            ("Basmati Rice",                                "side", True,  False),
            ("House Salad",                                 "side", True,  False),
            ("Hummus",                                      "side", True,  False),
            ("Pita Bread",                                  "side", True,  False),
            ("Spicy Garlic-Yogurt and Cilantro Mint Sauces","side", True,  True),
            # meals
            ("Chicken Kebab",                               "meal", False, False),
            ("Chicken Shawarma Wrap",                       "meal", False, False),
            ("Falafel Wrap",                                "meal", True,  False),
            ("Kufta Kebab",                                 "meal", False, False),
        ],
    },
    {
        "name": "King Eggroll",
        "cuisine_tag": "chinese",
        "address": "1560 Berryessa Rd, San Jose, CA 95133",
        "dishes": [
            # sides
            ("Chicken Eggrolls",    "side", False, False),
            ("Veggie Eggrolls",     "side", True,  False),
            # meals
            ("Beef Broccoli",       "meal", False, False),
            ("Orange Chicken",      "meal", False, False),
            ("Shaken Tofu",         "meal", True,  False),
            ("Veggie Chow Mein",    "meal", True,  False),
            ("Veggie Fried Rice",   "meal", True,  False),
        ],
    },
    {
        "name": "Mendocino Farms",
        "cuisine_tag": "sandwich",
        "address": "3970 Freedom Circle, Santa Clara, CA 95054",
        "dishes": [
            # sides
            ("Assorted Cookies",                        "side", True,  False),
            ("Basil Pesto Shells",                      "side", True,  False),
            # meals
            ("Chicken Pesto Caprese Sandwich",          "meal", False, False),
            ("Chimichurri Steak and Bacon Sandwich",    "meal", False, False),
            ("Mario's Caprese Sandwich",                "meal", True,  False),
            ("Not so Fried Chicken Sandwich",           "meal", False, False),
            ("Pink Lady Apple and Goat Cheese Salad",   "meal", True,  False),
            ("Prosciutto and Chicken Sandwich",         "meal", False, False),
            ("The Farm Club Sandwich",                  "meal", False, False),
            ("Turkey Avo Salsa Verde Sandwich",         "meal", False, False),
        ],
    },
    {
        "name": "Panera",
        "cuisine_tag": "bakery-cafe",
        "address": "3055 Olin Ave, San Jose, CA 95128",
        "dishes": [
            # sides
            ("Butter",                          "side", True, False),
            ("Cream Cheese",                    "side", True, False),
            ("Large Fruit Bowl",                "side", True, False),
            # meals
            ("Assorted Bagels and Pastries",    "meal", True, False),
            ("Greek Yogurt w/Berries Parfait",  "meal", True, False),
            # drinks
            ("Coffee",                          "drink", True, False),
            ("Orange Juice",                    "drink", True, False),
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
            for dish_name, category, is_vegi, is_spicy in entry["dishes"]:
                dish = Dish(
                    name=dish_name,
                    restaurant_id=restaurant.id,    # FK set after flush populated the PK
                    category=category,
                    is_vegetarian=is_vegi,          # sourced directly from seed table
                    is_spicy=is_spicy,              # sourced directly from seed table
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
