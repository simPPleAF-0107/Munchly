export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface UserProfile {
  id: string;
  user_id: string;
  full_name?: string;
  date_of_birth?: string;
  gender?: string;
  height_cm?: number;
  weight_kg?: number;
  activity_level?: string;
  health_goal?: string;
  target_weight_kg?: number;
  cooking_ability?: string;
  budget_type?: string;
  location_country?: string;
  location_city?: string;
  currency?: string;
}

export interface DietaryPreference {
  id: string;
  profile_id: string;
  diet_type: string;
}

export interface Allergy {
  id: string;
  profile_id: string;
  allergen: string;
  severity: string;
}

export interface FoodPreference {
  id: string;
  profile_id: string;
  food_item: string;
  preference_type: string;
}

export interface CuisinePreference {
  id: string;
  profile_id: string;
  cuisine: string;
}

export interface NutritionTargets {
  daily_calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface MealTargets {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Recipe {
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
  is_allergen: boolean;
  allergen_type?: string;
}

export interface RecipeIngredient {
  id: string;
  recipe_id: string;
  food_id: string;
  quantity: number;
  unit: string;
  notes?: string;
  food?: Food;
}

export interface MealPlan {
  id: string;
  user_id: string;
  start_date: string;
  end_date: string;
  target_calories: number;
  status: string;
}

export interface MealPlanMeal {
  id: string;
  meal_plan_id: string;
  recipe_id: string;
  meal_type: string;
  planned_date: string;
  servings: number;
  consumed: boolean;
  recipe?: Recipe;
}

export interface MealOption {
  recipe: Recipe;
  match_score: number;
  reason: string;
}

export interface ShoppingList {
  id: string;
  user_id: string;
  meal_plan_id: string;
  created_at: string;
}

export interface ShoppingListItem {
  id: string;
  shopping_list_id: string;
  food_id: string;
  quantity: number;
  unit: string;
  is_purchased: boolean;
  food?: Food;
}

export interface OnboardingData {
  profile: Partial<UserProfile>;
  dietary_preferences: string[];
  allergies: Array<{ allergen: string; severity: string }>;
  food_preferences: Array<{ food_item: string; preference_type: string }>;
  cuisines: string[];
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}
