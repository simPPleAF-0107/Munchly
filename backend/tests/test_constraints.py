import pytest
from app.services.constraint_service import ConstraintService
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.ingredient import Ingredient
from app.models.enums import MealType

@pytest.fixture
def ingredients():
    return {
        "peanut": Ingredient(id="i1", name="Peanut"),
        "chicken": Ingredient(id="i2", name="Chicken"),
        "apple": Ingredient(id="i3", name="Apple")
    }

@pytest.fixture
def recipes(ingredients):
    r1 = Recipe(id="r1", name="Peanut Butter Jelly", meal_types=[MealType.BREAKFAST], ingredients=[
        RecipeIngredient(ingredient=ingredients["peanut"]),
        RecipeIngredient(ingredient=ingredients["apple"])
    ])
    r2 = Recipe(id="r2", name="Chicken Apple Salad", meal_types=[MealType.LUNCH, MealType.DINNER], ingredients=[
        RecipeIngredient(ingredient=ingredients["chicken"]),
        RecipeIngredient(ingredient=ingredients["apple"])
    ])
    r3 = Recipe(id="r3", name="Apple Snack", meal_types=[MealType.SNACK], ingredients=[
        RecipeIngredient(ingredient=ingredients["apple"])
    ])
    return [r1, r2, r3]

@pytest.mark.asyncio
async def test_allergen_exclusion(recipes):
    allergies = ["peanut"]
    filtered = ConstraintService.filter_by_ingredients(recipes, allergies, [])
    names = [r.name for r in filtered]
    assert "Peanut Butter Jelly" not in names
    assert "Chicken Apple Salad" in names

@pytest.mark.asyncio
async def test_never_food_exclusion(recipes):
    never_foods = ["chicken"]
    filtered = ConstraintService.filter_by_ingredients(recipes, [], never_foods)
    names = [r.name for r in filtered]
    assert "Chicken Apple Salad" not in names
    assert "Peanut Butter Jelly" in names

@pytest.mark.asyncio
async def test_meal_type_filtering(recipes):
    # Breakfast
    breakfasts = ConstraintService.filter_by_meal_type(recipes, MealType.BREAKFAST)
    assert len(breakfasts) == 1
    assert breakfasts[0].name == "Peanut Butter Jelly"

    # Lunch
    lunches = ConstraintService.filter_by_meal_type(recipes, MealType.LUNCH)
    assert len(lunches) == 1
    assert lunches[0].name == "Chicken Apple Salad"

@pytest.mark.asyncio
async def test_medical_per_meal_rules():
    # Let's say user has a rule: max 30g sugar per meal
    recipe = Recipe(id="r1", name="Sweet Cake", nutritional_info={"sugar": 40, "calories": 500})
    
    medical_rules = {
        "per_meal": {
            "sugar": {"max": 30}
        }
    }
    
    passed = ConstraintService.check_medical_rules(recipe, medical_rules)
    assert not passed
    
    recipe2 = Recipe(id="r2", name="Apple", nutritional_info={"sugar": 15, "calories": 100})
    passed2 = ConstraintService.check_medical_rules(recipe2, medical_rules)
    assert passed2
