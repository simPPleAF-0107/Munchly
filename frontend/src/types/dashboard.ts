/**
 * Dashboard types — wired to Phase 3-5 backend APIs.
 * No mock data. Every type maps to a real API response.
 */

// === Phase 3: Daily Context ===

export interface DailyContextResponse {
  id: string;
  user_id: string;
  date: string;
  status: "PENDING" | "COMPLETED" | "SKIPPED";
  workout_today: boolean;
  workout_type: string | null;
  workout_intensity: string | null;
  hunger_level: string | null;
  energy_level: string | null;
  food_mood: string | null;
  eating_location: string | null;
  available_cook_time_min: number | null;
  adjusted_calorie_target: number | null;
  pantry_food_ids: string[] | null;
  craving_recipe_id: string | null;
  craving_meal_type: string | null;
  change_level: string | null;
  checked_in_at: string | null;
}

export interface CheckInPayload {
  workout_today: boolean;
  workout_type?: string;
  workout_intensity?: string;
  hunger_level?: string;
  energy_level?: string;
  food_mood?: string;
  eating_location?: string;
  available_cook_time_min?: number;
}

// === Phase 4: Feedback ===

export interface FeedbackResponse {
  feedback_id: string;
  change_level: string | null;
  applied_tier: string;
  affected_entities: Array<{ type: string; id: string }>;
}

export interface RejectionPayload {
  recipe_id: string;
  meal_plan_meal_id?: string;
  feedback_type: string;
  reason?: string;
  ingredient_ids?: string[];
  scope: "TODAY" | "FUTURE" | "PERMANENT";
  notes?: string;
}

export interface ConflictOption {
  label: string;
  action: string;
}

export interface ConflictItem {
  conflict_type: string;
  severity: string;
  description: string;
  constraint_a: string;
  constraint_b: string;
  options: ConflictOption[];
  recommendation: string | null;
}

export interface ConflictReport {
  has_conflicts: boolean;
  conflicts: ConflictItem[];
  warnings: string[];
}

// === Phase 5: Behavioral Learning ===

export interface BehavioralProfile {
  id: string;
  dimension: string;
  meal_type: string | null;
  entity_key: string;
  observed_strength: number;
  sample_count: number;
  confidence: number;
  last_updated: string;
}

export interface BehavioralInsight {
  id: string;
  dimension: string;
  meal_type: string | null;
  entity_key: string;
  message: string;
  observed_strength: number;
  confidence: number;
  status: "PENDING" | "SHOWN" | "ACCEPTED" | "DISMISSED";
  created_at: string;
}

// === Dashboard: Computed display types ===

export interface NutrientBar {
  name: string;
  current: number;
  target: number;
  unit: string;
  percent: number;
  status: "good" | "warning" | "low" | "limited_data";
}

export interface MealFit {
  overall: number; // 0-100 percentage
  dimensions: Array<{
    name: string;
    score: number; // 0-5 stars
    label: string;
  }>;
}

export interface WhyThisMeal {
  reasons: Array<{
    dimension: string;
    description: string;
    score: number;
  }>;
}

export interface WhyNotMeal {
  recipe_name: string;
  reasons: Array<{
    type: "hard" | "soft";
    description: string;
  }>;
}
