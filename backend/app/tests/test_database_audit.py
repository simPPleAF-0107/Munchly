import pytest
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, UUIDMixin
from app.models.user import User
from app.models.profile import UserProfile
from app.models.health import UserHealthCondition
from app.models.dietary import (
    UserDietaryPreference, UserAllergy, UserDietaryRestriction,
    UserFoodPreference, UserCuisinePreference, UserAvailableIngredient
)
from app.models.food import Food, FoodAllergen, FoodRegion, FoodPrice
from app.models.recipe import (
    Recipe, RecipeIngredient, RecipeDietCompatibility,
    RecipeMealType, RecipeCuisine, RecipeRegion
)
from app.models.meal_plan import MealPlan, MealPlanMeal, MealOption, MealHistory
from app.models.grocery import ShoppingList, ShoppingListItem
from app.models.medical_rule import MedicalRule, MedicalRuleConstraint
from app.models.event import UserEvent
from app.models.lifestyle import UserLifestyle
from app.models.daily_context import DailyContext
from app.models.feedback import UserFeedback, UserPreferenceOverride
from app.models.behavioral_profile import UserBehavioralProfile, UserBehavioralInsight

# List of all models to check
ALL_MODELS = [
    User, UserProfile, UserHealthCondition, UserDietaryPreference, UserAllergy, UserDietaryRestriction,
    UserFoodPreference, UserCuisinePreference, UserAvailableIngredient,
    Food, FoodAllergen, FoodRegion, FoodPrice,
    Recipe, RecipeIngredient, RecipeDietCompatibility, RecipeMealType, RecipeCuisine, RecipeRegion,
    MealPlan, MealPlanMeal, MealOption, MealHistory,
    ShoppingList, ShoppingListItem,
    MedicalRule, MedicalRuleConstraint,
    UserEvent, UserLifestyle, DailyContext,
    UserFeedback, UserPreferenceOverride,
    UserBehavioralProfile, UserBehavioralInsight
]

def test_models_inherit_base_classes():
    """Verify all models inherit from proper base classes."""
    for model in ALL_MODELS:
        assert issubclass(model, Base), f"{model.__name__} does not inherit from Base"
        assert issubclass(model, UUIDMixin), f"{model.__name__} does not inherit from UUIDMixin"

def test_user_foreign_keys_cascade_delete():
    """Verify all models that reference 'users' have ondelete='CASCADE' on FKs."""
    for model in ALL_MODELS:
        mapper = inspect(model)
        for column in mapper.columns:
            for fk in column.foreign_keys:
                if fk.target_fullname == "users.id":
                    assert fk.ondelete == "CASCADE", f"Missing ondelete='CASCADE' on {model.__name__}.{column.name}"

def test_user_event_immutable():
    """Verify UserEvent model has NO update fields."""
    mapper = inspect(UserEvent)
    column_names = [col.name for col in mapper.columns]
    # Typically, no 'updated_at' or similar fields
    assert "updated_at" not in column_names, "UserEvent should not have an updated_at field"
    assert "updated_by" not in column_names, "UserEvent should not have an updated_by field"

def test_daily_context_unique_constraint():
    """Verify DailyContext has a unique constraint on (user_id, date)."""
    mapper = inspect(DailyContext)
    constraints = getattr(mapper.local_table, "constraints", set())
    found = False
    for constraint in constraints:
        if type(constraint).__name__ == "UniqueConstraint":
            cols = [col.name for col in constraint.columns]
            if sorted(cols) == sorted(["user_id", "date"]):
                found = True
                break
    assert found, "DailyContext missing unique constraint on (user_id, date)"

def test_behavioral_profile_unique_constraint():
    """Verify UserBehavioralProfile has appropriate unique constraints."""
    mapper = inspect(UserBehavioralProfile)
    constraints = getattr(mapper.local_table, "constraints", set())
    found = False
    for constraint in constraints:
        if type(constraint).__name__ == "UniqueConstraint":
            cols = [col.name for col in constraint.columns]
            if sorted(cols) == sorted(["user_id", "dimension", "meal_type", "entity_key"]):
                found = True
                break
    assert found, "UserBehavioralProfile missing unique constraint"

def test_recipe_cascade_delete():
    """Verify Recipe has cascade delete for ingredients, cuisines, regions, etc."""
    mapper = inspect(Recipe)
    
    expected_cascades = ["ingredients", "diet_compatibility", "meal_types", "cuisines", "regions"]
    for rel_name in expected_cascades:
        rel = mapper.relationships[rel_name]
        assert rel.cascade.delete, f"Recipe.{rel_name} missing delete cascade"
        assert rel.cascade.delete_orphan, f"Recipe.{rel_name} missing delete-orphan cascade"

def test_user_event_jsonb():
    """Verify JSONB field usage in UserEvent.metadata_."""
    mapper = inspect(UserEvent)
    col = mapper.columns.get("metadata_")
    assert isinstance(col.type, JSONB), "UserEvent.metadata_ must be JSONB type"
