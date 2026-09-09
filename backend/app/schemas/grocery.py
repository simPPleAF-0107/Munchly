import uuid
from pydantic import BaseModel, ConfigDict

class ShoppingListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_id: uuid.UUID
    food_name: str
    category: str
    consumed_quantity_g: float
    purchase_quantity_g: float
    purchase_unit: str
    estimated_item_cost: float

class ShoppingListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consumed_cost: float
    actual_shopping_cost: float
    remaining_inventory_value: float
    cost_currency: str
    items: list[ShoppingListItemResponse]
    items_by_category: dict[str, list[ShoppingListItemResponse]]
    weekly_grocery_limit: float
    within_budget: bool
