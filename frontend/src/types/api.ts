import type { RecipeIngredient } from "./index";

export interface RecipeResponse {
  id: string;
  name: string;
  description: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sodium_mg: number;
  estimated_cost: number;
  cost_currency: string;
  prep_time_min: number;
  difficulty: string;
  servings: number;
  instructions: string;
  image_url: string | null;
  diet_compatibility: string[];
  meal_types: string[];
  cuisines: string[];
  ingredients: RecipeIngredient[];
  allergens: string[];
}

export interface MealOptionResponse {
  recipe_id: string;
  recipe: RecipeResponse;
  option_type: string;
  score: number;
}

export interface MealPlanMealResponse {
  id: string;
  day_of_week: number;
  meal_type: string;
  selected_recipe_id: string | null;
  options: MealOptionResponse[];
}

export interface MealPlanResponse {
  id: string;
  week_start_date: string;
  total_consumed_cost: number | null;
  total_purchase_cost: number | null;
  cost_currency: string;
  status: string;
  meals: MealPlanMealResponse[];
  created_at: string;
}

export interface ShoppingListItemResponse {
  food_id: string;
  food_name: string;
  category: string;
  consumed_quantity_g: number;
  purchase_quantity_g: number;
  purchase_unit: string;
  estimated_item_cost: number;
}

export interface ShoppingListResponse {
  id: string;
  consumed_cost: number;
  actual_shopping_cost: number;
  remaining_inventory_value: number;
  cost_currency: string;
  items: ShoppingListItemResponse[];
  items_by_category: Record<string, ShoppingListItemResponse[]>;
  weekly_grocery_limit: number;
  within_budget: boolean;
}

export interface UserResponse {
  id: string;
  email: string;
  auth_provider: string;
  subscription_tier: string;
  is_active: boolean;
  created_at: string;
}
