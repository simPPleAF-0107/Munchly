export interface RecipeResponse {
  id: string;
  title: string;
  description: string;
  instructions: string;
  prep_time_mins: number;
  cook_time_mins: number;
  servings: number;
  cuisine_type: string;
  difficulty_level: string;
  calories_per_serving: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  image_url?: string;
  estimated_cost: number;
  diet_type?: string;
}

export interface MealOptionResponse {
  recipe_id: string;
  recipe: RecipeResponse;
  option_type: 'BEST' | 'BUDGET' | 'VARIETY' | string;
  score: number;
}

export interface MealPlanMealResponse {
  id: string;
  day_of_week: number; // 1-7 (1 = Monday)
  meal_type: 'BREAKFAST' | 'LUNCH' | 'DINNER' | string;
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
  id: string;
  food_name: string;
  needed_quantity: number;
  needed_unit: string;
  purchase_quantity: number;
  purchase_unit: string;
  estimated_cost: number;
  is_purchased: boolean;
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
  name?: string;
  diet_type?: string;
  location?: string;
  cuisines?: string[];
  weekly_budget?: number;
  currency?: string;
  subscription_tier?: string;
  daily_calories_target?: number;
  daily_protein_target?: number;
}
