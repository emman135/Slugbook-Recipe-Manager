
from yatl.helpers import A

from py4web import URL, abort, action, redirect, request, Field
from py4web.core import Template
from py4web.utils.form import Form

from .common import (
    T,
    auth,
    authenticated,
    cache,
    db,
    flash,
    logger,
    session,
    unauthenticated,
)

import re

from py4web import action, request, abort, redirect
from .common import auth

@action("index")
@action("/")
@action.uses("index.html", auth.user, T)
def index():
    user = auth.get_user()
    ingredients_form = Form(
        db.ingredients,
        fields=["name", "unit", "calories_per_unit", "description"],
        dbio=False
    )
    # Recipe form without allowing author field to be editable
    recipes_form = Form(
        db.recipes,
        fields=["name", "type", "description", "image", "instruction_steps", "servings"],
        dbio=False #disables automatic inserts
    )
    
    if ingredients_form.accepted:
        print("Inserting ingredients:", ingredients_form.vars["name"])
        db.ingredients.insert(
            name=ingredients_form.vars["name"],
            unit=ingredients_form.vars["unit"],
            calories_per_unit=ingredients_form.vars["calories_per_unit"],
            description=ingredients_form.vars["description"],
        )
        redirect(URL("index"))
    
    if recipes_form.accepted:
        print("Inserting recipe:", recipes_form.vars["name"])
        db.recipes.insert(
            name=recipes_form.vars["name"],
            type=recipes_form.vars["type"],
            description=recipes_form.vars["description"],
            image=recipes_form.vars["image"],
            instruction_steps=recipes_form.vars["instruction_steps"],
            servings=recipes_form.vars["servings"],
            author=user["id"]
        )
        redirect(URL("index"))
    return {"user": user, "ingredients_form": ingredients_form, "recipes_form": recipes_form}

@action("/recipe/api/recipes",method=["GET"])
@action.uses(db)
def add_recipe():
    # returns all recipes in the database
    rows = db(db.recipes).select().as_list()
    print("returning recipes: ", rows)
    return {"recipes": rows}

@action("/recipe/api/ingredients",method=["GET"])
@action.uses(db)
def add_ingredients():
    # returns all recipes in the database
    rows = db(db.ingredients).select().as_list()
    print("returning ingredients: ", rows)
    return {"ingredients": rows}
