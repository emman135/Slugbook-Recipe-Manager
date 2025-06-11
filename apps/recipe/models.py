from pydal.validators import *
from .common import Field, db, auth
import requests
import re

db.define_table(
    "ingredients",
    Field("name", type="string", requires=IS_NOT_EMPTY()),
    Field("unit", type="string", requires=IS_NOT_EMPTY()),
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

# Connects to TheMealDB API and fills the database with recipes
def populate_db():
    base_api_url = "www.themealdb.com/api/json/v1/1/search.php?f="
    all_meals = []

    print("Accessing TheMealDB API")
    for letter in "abcdefghijklmnopqrstuvwxyz":
        try:
            response = requests.get(base_api_url + letter)
            response.raise_for_status()
            data = response.json()
            if (data.get(meals)):
                all_meals.extend(data["meals"])
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch recipes for letter '{letter}': {e}")

    for meal in meals:
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
                ingredient = db.ingredients.get_or_insert(
                    name=ingredient_name,
                    defaults={
                        "unit": 0, "calories_per_unit": 0, "description": "Imported"
                    }
                )
                
                quantity = 0
                if measure and measure.strip():
                    num_search = re.match(r'[\d\.\/]+', measure.strip())
                    if num_search:
                        num_str = num_search.group(0)
                        try:
                            if "/" in num_str:
                                parts = num_str.split("/")
                                if len(parts) == 2 and float(parts[1]) != 0:
                                    quantity = int(float(parts[0]) / float(parts[1]))
                            else:
                                quantity = int(float(num_str))
                        except (ValueError, ZeroDivisionError):
                            quantity = 0
                
                db.link.insert(
                    recipe_id=recipe_id,
                    ingredient_id=ingredient.id,
                    quantity_per_serving=quantity,
                )


db.commit()
