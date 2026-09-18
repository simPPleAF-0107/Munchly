export interface User {
  id: string;
  email: string;
  auth_provider: string;
  subscription_tier: string;
  is_active: boolean;
  created_at: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  name: string;
  age: number;
  gender: string;
  country_code: string;
  state_code: string;
  city: string;
  height_cm: number;
  weight_kg: number;
  activity_level: string;
  health_goal: string;
  cooking_ability: string;
  max_prep_time_min: number;
  weekly_grocery_limit: number;
  weekly_grocery_limit_currency: string;
  budget_type: string;
  onboarding_completed: boolean;
}

export interface MealTargets {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface NutritionTargets {
  daily_calories: number;
  daily_calories_range: [number, number];
  protein_g: number;
  protein_range: [number, number];
  carbs_g: number;
  fat_g: number;
  fat_min_g: number;
  fiber_g: number;
  fiber_min_g: number;
  bmi: number;
  bmi_category: string;
  bmr: number;
  tdee: number;
  per_meal: Record<string, MealTargets>;
}

export interface RecipeIngredient {
  food_id: string;
  food_name: string;
  quantity_g: number;
  unit: string;
  is_optional: boolean;
}

export interface Recipe {
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

export interface Food {
  id: string;
  name: string;
  category: string;
  calories_per_100g: number;
  protein_per_100g: number;
  carbs_per_100g: number;
  fat_per_100g: number;
  fiber_per_100g: number;
  is_vegan: boolean;
  is_vegetarian: boolean;
}

export interface MealOption {
  recipe_id: string;
  recipe: Recipe;
  option_type: string;
  score: number;
}

export interface MealPlanMeal {
  id: string;
  day_of_week: number;
  meal_type: string;
  selected_recipe_id: string | null;
  options: MealOption[];
}

export interface MealPlan {
  id: string;
  week_start_date: string;
  total_consumed_cost: number | null;
  total_purchase_cost: number | null;
  cost_currency: string;
  status: string;
  meals: MealPlanMeal[];
  created_at: string;
}

export interface ShoppingListItem {
  food_id: string;
  food_name: string;
  category: string;
  consumed_quantity_g: number;
  purchase_quantity_g: number;
  purchase_unit: string;
  estimated_item_cost: number;
}

export interface ShoppingList {
  id: string;
  consumed_cost: number;
  actual_shopping_cost: number;
  remaining_inventory_value: number;
  cost_currency: string;
  items: ShoppingListItem[];
  items_by_category: Record<string, ShoppingListItem[]>;
  weekly_grocery_limit: number;
  within_budget: boolean;
}

export interface OnboardingData {
  basic_info: Record<string, any>;
  body_info: Record<string, any>;
  goal: Record<string, any>;
  dietary_preference: Record<string, any>;
  allergies: Record<string, any>;
  restrictions: Record<string, any>;
  medical_conditions: Record<string, any>;
  food_preferences: Record<string, any>;
  cuisine_preferences: Record<string, any>;
  cooking: Record<string, any>;
  budget: Record<string, any>;
  pantry_items: Record<string, any>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}
