import json

from py4web import action, URL, abort, redirect, request
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

# Home page – shows ingredient form + lists (Vue handles recipe form)
@action("index")
@action("/")
@action.uses("index.html", auth.user, T)
def index():
    user = auth.get_user()

    # form to add ingredients
    ing_form = Form(
        db.ingredients,
        fields=["name", "unit", "calories_per_unit", "description"],
        dbio=False,
    )

    if ing_form.accepted:
        db.ingredients.insert(
            name=ing_form.vars["name"],
            unit=ing_form.vars["unit"],
            calories_per_unit=ing_form.vars["calories_per_unit"],
            description=ing_form.vars["description"],
        )
        flash.set("Ingredient added")
        redirect(URL("index"))

    # send full ingredient + recipe lists for the Vue app
    ingredients = db(db.ingredients).select().as_list()
    recipes     = db(db.recipes).select().as_list()

    return dict(user=user,
                ingredients_form=ing_form,
                ingredients=ingredients,
                recipes=recipes)

# EXTRA CREDIT - Ability to search by ingredients
# SEARCH API for recipes - can search by recipe name and/or type (not case sensitive)
@action("/recipe/api/recipes",method=["GET"])
def get_recipes():
    # get all recipies
    query = db.recipes.id > 0

    # Get parameters from the request
    recipe_type = request.params.get('type')
    recipe_name = request.params.get('name')
    ingredients_str = request.params.get('ingredients')

    if recipe_type:
        query &= (db.recipes.type.lower() == recipe_type.lower())

    if recipe_name:
        query &= (db.recipes.name.ilike(f"%{recipe_name}%"))

    if ingredients_str:
        # Parse ingredients seperated by commas
        ingredient_list = [name.strip().lower() for name in ingredients_str.split(',') if name.strip()]

        matching_ingredient_ids = db(
            db.ingredients.name.lower().belongs(ingredient_list)
        )._select(db.ingredients.id)

        # Find matching recipe ids
        recipe_ids_with_ingredients = db(
            db.link.ingredient_id.belongs(matching_ingredient_ids)
        )._select(db.link.recipe_id, distinct=True)

        query &= db.recipes.id.belongs(recipe_ids_with_ingredients)


    rows = db(query).select().as_list()
    return {"recipes": rows}

# EXTRA CREDIT
# PUBLIC SEARCH API Ingredients - params: name, unit, description
@action("/recipe/api/ingredients",method=["GET"])
@action.uses(db)
def get_ingredients():
    query = db.ingredients.id > 0

    ingredient_name = request.params.get('name')
    ingredient_unit = request.params.get('unit')
    ingredient_description = request.params.get('description')

    if ingredient_name:
        query &= (db.ingredients.name.ilike(f"%{ingredient_name}%"))

    if ingredient_unit:
        query &= (db.ingredients.unit.lower() == ingredient_unit.lower())

    if ingredient_description:
        query &= (db.ingredients.description.ilike(f"%{ingredient_description}%"))

    rows = db(query).select().as_list()
    return {"ingredients": rows}


@action("/recipe/api/links",method=["GET"])
@action.uses(db)
def add_bird():
    rows = db(db.link).select().as_list()
    return {"links": rows}

# For edit function (CHECKS IF USER ID IS THE AUTHOR OF RECIPE)
@action("api/recipe/<rid:int>", method=["GET"])
@action.uses(db, auth.user)
def api_one_recipe(rid):
    rec = db.recipes[rid] or abort(404)

    # Check uid is right
    if rec.author != auth.user_id:
        abort(403, "You are not allowed to view this recipe")

    links = db(db.link.recipe_id == rid).select().as_list() 
    return dict(recipe=rec, ingredients=links)

# create or update
@action("api/recipe", method=["POST", "PUT"])
@action.uses(db, auth.user)
def api_save_recipe():
    # ----- detect payload type ---------------------------------------
    is_json = request.headers.get("content-type", "").startswith("application/json")
    if is_json:
        data = request.json or abort(400, "Missing JSON")
        ingredients_payload = data.get("ingredients", [])
        image_file = None
        recipe_fields = {k: data.get(k) for k in (
            "name", "type", "description",
            "instruction_steps", "servings")}
    else:                                              # multipart/form-data
        # normal fields live in request.POST
        recipe_fields = {k: request.POST.get(k) for k in (
            "name", "type", "description",
            "instruction_steps", "servings")}
        recipe_fields["servings"] = int(recipe_fields["servings"])
        ingredients_payload = json.loads(request.POST.get("ingredients", "[]"))
        image_file = request.files.get("image")

    recipe_fields["author"] = auth.user_id

    # -------- create/update recipe row -------------------------------
    if request.method == "POST":
        rid = db.recipes.insert(**recipe_fields, image=image_file)
    else:
        rid = (request.json or request.POST).get("id") or abort(400, "Missing id")
        rec = db.recipes[rid] or abort(404)
        if rec.author != auth.user_id:
            abort(403, "Not your recipe")
        rec.update_record(**recipe_fields, image=image_file or rec.image)
        db(db.link.recipe_id == rid).delete()

    # -------- link ingredients & calc calories -----------------------
    total = 0
    for link in ingredients_payload:            # [{id, qty}, …]
        ing = db.ingredients[link["id"]] or abort(400, "Bad ingredient")
        qty = int(link["qty"])
        db.link.insert(recipe_id=rid,
                       ingredient_id=ing.id,
                       quantity_per_serving=qty)
        total += qty * ing.calories_per_unit

    total *= int(recipe_fields["servings"])
    db.recipes[rid].update_record(total_calories=total)

    return dict(status="ok", recipe_id=rid, total_calories=total)

@action("api/internalrecipes", method=["GET"])
@action.uses(db)
def api_recipes():
    # plain dicts
    recs  = db(db.recipes).select().as_list()
    links = db(db.link).select().as_list()
    ings  = db(db.ingredients).select().as_list()

    # quick lookup: ingredient_id → {name, unit}
    ing_map = {row["id"]: row for row in ings}

    # gather links by recipe
    by_recipe = {}
    for l in links:
        rid = l["recipe_id"]
        by_recipe.setdefault(rid, []).append({
            "id":   l["ingredient_id"],
            "name": ing_map[l["ingredient_id"]]["name"],
            "unit": ing_map[l["ingredient_id"]]["unit"],
            "qty":  l["quantity_per_serving"],
        })

    # attach to each recipe
    for r in recs:
        r["ingredients"] = by_recipe.get(r["id"], [])

    return dict(recipes=recs)


