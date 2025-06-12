from pydal.validators import *
from .common import Field, db, auth

db.define_table(
    "ingredients",
    # If we don't want duplicates we can add unique=True to name
    Field("name", type="string", requires=IS_NOT_EMPTY()),
    Field("unit", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
    Field("calories_per_unit", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
    Field("description", type="text", requires=IS_NOT_EMPTY()),
)

db.define_table(
    "recipes",
    Field("name", type="string", requires=IS_NOT_EMPTY()),
    Field("type", type="string", requires=IS_NOT_EMPTY()),
    Field("description", type="string", requires=IS_NOT_EMPTY()),
    Field("image", type="upload"),
    Field("instruction_steps",type="string", requires=IS_NOT_EMPTY()),
    Field("servings", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
    Field("author", "reference auth_user", requires=IS_NOT_EMPTY(), readable=False, writable=False),
)

db.define_table(
    "link",
    Field("recipe_id", "reference recipes", requires=IS_NOT_EMPTY()),
    Field("ingredient_id", "reference ingredients", requires=IS_NOT_EMPTY()),
    Field("quantity_per_serving", type="integer", requires=IS_INT_IN_RANGE(0,1000)),
)

db.commit()

# for table in db.tables:
#     db[table].drop()
# db.commit()