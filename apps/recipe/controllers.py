
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
@action.uses("index.html", auth.user, T)
def index():
    user = auth.get_user()
    ingredients_form = Form(db.ingredients)
    # Recipe form without allowing author field to be editable
    recipes_form = Form(
        db.recipes,
        fields=["name", "type", "description", "image", "instruction_steps", "servings"],
        dbio=False #disables automatic inserts
    )
    
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

# SEARCH API - can search by recipe name and/or type (not case sensitive)
@action("/recipe/api/recipes",method=["GET"])
def get_recipes():
    # get all recipies
    query = db.recipes.id > 0

    # Get parameters from the request
    recipe_type = request.params.get('type')
    recipe_name = request.params.get('name')

    if recipe_type:
        query &= (db.recipes.type.lower() == recipe_type.lower())

    if recipe_name:
        query &= (db.recipes.name.ilike(f"%{recipe_name}%"))

    rows = db(query).select().as_list()
    return {"recipes": rows}

@action("/recipe/api/ingredients",method=["GET"])
@action.uses(db)
def add_bird():
    rows = db(db.ingredients).select().as_list()
    return {"ingredients": rows}

@action("/recipe/api/links",method=["GET"])
@action.uses(db)
def add_bird():
    rows = db(db.link).select().as_list()
    return {"links": rows}

