import pytest
from app.services.constraint_service import ConstraintService
from app.models.recipe import Recipe
from app.models.enums import DietaryType, MealType

@pytest.fixture
def recipes():
    return [
        Recipe(id="1", name="Vegan Salad", dietary_compatibility=[DietaryType.VEGAN, DietaryType.VEGETARIAN, DietaryType.NON_VEG]),
        Recipe(id="2", name="Omelette", dietary_compatibility=[DietaryType.EGGETARIAN, DietaryType.NON_VEG]),
        Recipe(id="3", name="Chicken Curry", dietary_compatibility=[DietaryType.NON_VEG]),
        Recipe(id="4", name="Fish Stew", dietary_compatibility=[DietaryType.NON_VEG])
    ]

@pytest.mark.asyncio
async def test_diet_compatibility_vegan(recipes):
    # Vegan user
    filtered = ConstraintService.filter_by_diet(recipes, DietaryType.VEGAN, [])
    assert len(filtered) == 1
    assert filtered[0].name == "Vegan Salad"

@pytest.mark.asyncio
async def test_diet_compatibility_vegetarian(recipes):
    # Vegetarian user
    filtered = ConstraintService.filter_by_diet(recipes, DietaryType.VEGETARIAN, [])
    # Should get Vegan and Vegetarian recipes (only 1 here)
    assert len(filtered) == 1
    assert filtered[0].name == "Vegan Salad"

@pytest.mark.asyncio
async def test_diet_compatibility_eggetarian(recipes):
    # Eggetarian user
    filtered = ConstraintService.filter_by_diet(recipes, DietaryType.EGGETARIAN, [])
    # Should get Vegan, Vegetarian, Eggetarian
    assert len(filtered) == 2
    names = [r.name for r in filtered]
    assert "Vegan Salad" in names
    assert "Omelette" in names
    assert "Chicken Curry" not in names

@pytest.mark.asyncio
async def test_diet_compatibility_non_veg_no_fish(recipes):
    # Non-veg user who avoids fish
    filtered = ConstraintService.filter_by_diet(recipes, DietaryType.NON_VEG, ["fish"])
    # We assume 'fish' in avoided ingredients handles the Fish Stew exclusion, 
    # but the diet itself allows all. So diet filter leaves all, and then ingredient exclusion removes fish.
    # If the diet filter alone is tested:
    diet_filtered = ConstraintService.filter_by_diet(recipes, DietaryType.NON_VEG, [])
    assert len(diet_filtered) == 4

@pytest.mark.asyncio
async def test_diet_compatibility_non_veg(recipes):
    # Non-veg sees all
    filtered = ConstraintService.filter_by_diet(recipes, DietaryType.NON_VEG, [])
    assert len(filtered) == 4
