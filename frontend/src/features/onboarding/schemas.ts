import * as z from "zod";

export const basicInfoSchema = z.object({
  name: z.string().min(1, "Name is required"),
  age: z.coerce.number().min(13, "Must be at least 13").max(120, "Invalid age"),
  gender: z.string().min(1, "Gender is required"),
  country_code: z.string().default("IN"),
  state_code: z.string().optional(),
  city: z.string().optional(),
});

export const bodyInfoSchema = z.object({
  height_cm: z.coerce.number().min(50).max(300),
  weight_kg: z.coerce.number().min(10).max(500),
  activity_level: z.string().min(1, "Activity level is required"),
});

export const healthGoalSchema = z.object({
  health_goal: z.string().min(1, "Goal is required"),
});

export const dietaryPreferenceSchema = z.object({
  diet_type: z.string().min(1, "Diet type is required"),
  eats_chicken: z.boolean().optional(),
  eats_mutton: z.boolean().optional(),
  eats_fish: z.boolean().optional(),
  eats_seafood: z.boolean().optional(),
});

export const cookingSchema = z.object({
  cooking_ability: z.string().min(1),
  max_prep_time_min: z.coerce.number().min(5).max(120),
});

export const budgetSchema = z.object({
  weekly_grocery_limit: z.coerce.number().min(1),
  weekly_grocery_limit_currency: z.string().min(1),
  budget_type: z.string().min(1),
});
