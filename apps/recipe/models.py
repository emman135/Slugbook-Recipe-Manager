from pydal.validators import *
from .common import Field, db, auth
import requests
import re
import random
from fractions import Fraction


db.define_table(
    "ingredients",
    Field("name", type="string", requires=IS_NOT_EMPTY()),
    Field("unit", type="string"),
    Field("calories_per_unit", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
    Field("description", type="string", requires=IS_NOT_EMPTY()),
)

db.define_table(
    "recipes",
    Field("name", type="string", requires=IS_NOT_EMPTY()),
    Field("type", type="string", requires=IS_NOT_EMPTY()),
    Field("description", type="string", requires=IS_NOT_EMPTY()),
    Field("image", type="upload"),
    Field("instruction_steps",type="string", requires=IS_NOT_EMPTY()),
    Field("servings", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
    Field("author", "reference auth_user", readable=False, writable=False),
)

db.define_table(
    "link",
    Field("recipe_id", "reference recipes", requires=IS_NOT_EMPTY()),
    Field("ingredient_id", "reference ingredients", requires=IS_NOT_EMPTY()),
    Field("quantity_per_serving", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
)

def parse_measure(measure_str):
    """
    Parses a measurement string (e.g., "1 1/2 tsp") into an integer quantity and a string unit.
    Returns: (integer, string), for example (1, "tsp")
    """
    if not measure_str or not isinstance(measure_str, str):
        return 0, "" # Return defaults if input is invalid

    measure_str = measure_str.strip()
    
    # Regex to find an initial number (including fractions/spaces) and the text that follows.
    # Group 1: The numerical part (e.g., "1 1/2", "200", "1/4")
    # Group 2: The unit part (e.g., "tsp", "g", "can")
    match = re.match(r'([\d\s\.\/]+)\s*(.*)', measure_str)

    quantity = 1
    unit = ""

    if match:
        quantity_str = match.group(1).strip()
        unit_str = match.group(2).strip()
        
        # Safely convert the quantity string (like "1 1/2") to a number
        try:
            # Handle mixed numbers like "1 1/2" by splitting and summing
            if ' ' in quantity_str:
                total_fraction = sum(Fraction(part) for part in quantity_str.split())
                quantity = float(total_fraction)
            else: 
                quantity = float(Fraction(quantity_str))
        except (ValueError, ZeroDivisionError):
            quantity = 1
        
        # Clean up the unit string, taking only the first word
        unit = unit_str.split(' ')[0]

    else:
        # If no number is found, the whole string is the unit (ex: "to serve")
        unit = measure_str
    
    # Remove Unicode - if unit contains it change the unit to 'to serve'
    if not unit.isascii():
        unit = 'to serve'
    return int(quantity), unit

# Connects to TheMealDB API and fills the database with recipes
def populate_db():
    base_api_url = "https://www.themealdb.com/api/json/v1/1/search.php?f="
    all_meals = []

    print("Accessing TheMealDB API")
    for letter in "abcdefghijklmnopqrstuvwxyz":
        print("Requesting Letter: " + base_api_url+letter)
        try:
            response = requests.get(base_api_url + letter)
            response.raise_for_status()
            data = response.json()
            if (data["meals"]):
                all_meals.extend(data["meals"])
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch recipes for letter '{letter}': {e}")

    for meal in all_meals:
        recipe_id = db.recipes.insert(
            name=meal.get("strMeal"),
            type=meal.get("strCategory"),
            description=f'{meal.get("strArea")} cuisine',
            image=meal.get("strMealThumb"),
            instruction_steps=meal.get("strInstructions"),
            servings=1,
            author=None,  # No author, imported from API
        )

        for i in range(1,21):
            ingredient_name = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")

            if ingredient_name and ingredient_name.strip():
                    quantity, unit_str = parse_measure(measure)
                    ingredient = db.ingredients.insert(
                        name=ingredient_name,
                        unit=unit_str,
                        calories_per_unit=random.randint(1, 50),
                        description="imported",
                    )
                    
                    db.link.insert(
                        recipe_id=recipe_id,
                        ingredient_id=ingredient.id,
                        quantity_per_serving=quantity,
                    )

if db(db.recipes).count() == 0:
    populate_db()
    db.commit()
    print("Database population complete.")

'''
db.link.truncate()
db.recipes.truncate()
db.ingredients.truncate()
'''


db.commit()
