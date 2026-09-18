export const DIET_TYPES = [
  { value: "VEGAN", label: "Vegan", emoji: "🌱" },
  { value: "VEGETARIAN", label: "Vegetarian", emoji: "🥬" },
  { value: "EGGETARIAN", label: "Eggetarian", emoji: "🥚" },
  { value: "NON_VEGETARIAN", label: "Non-Vegetarian", emoji: "🍗" },
] as const;

export const ACTIVITY_LEVELS = [
  { value: "SEDENTARY", label: "Sedentary" },
  { value: "LIGHTLY_ACTIVE", label: "Lightly Active" },
  { value: "MODERATELY_ACTIVE", label: "Moderately Active" },
  { value: "VERY_ACTIVE", label: "Very Active" },
  { value: "EXTREMELY_ACTIVE", label: "Extremely Active" },
] as const;

export const HEALTH_GOALS = [
  { value: "LOSE_WEIGHT", label: "Lose Weight" },
  { value: "MAINTAIN_WEIGHT", label: "Maintain Weight" },
  { value: "GAIN_WEIGHT", label: "Gain Weight" },
  { value: "BUILD_MUSCLE", label: "Build Muscle" },
  { value: "IMPROVE_FITNESS", label: "Improve Fitness" },
  { value: "EAT_HEALTHIER", label: "Eat Healthier" },
] as const;

export const MEAL_TYPES = [
  { value: "BREAKFAST", label: "Breakfast" },
  { value: "LUNCH", label: "Lunch" },
  { value: "DINNER", label: "Dinner" },
] as const;

export const ALLERGENS = [
  { value: "PEANUTS", label: "Peanuts" },
  { value: "TREE_NUTS", label: "Tree Nuts" },
  { value: "MILK", label: "Milk" },
  { value: "EGGS", label: "Eggs" },
  { value: "SOY", label: "Soy" },
  { value: "WHEAT", label: "Wheat" },
  { value: "FISH", label: "Fish" },
  { value: "SHELLFISH", label: "Shellfish" },
  { value: "SESAME", label: "Sesame" },
  { value: "CUSTOM", label: "Custom" },
] as const;

export const MEDICAL_CONDITIONS = [
  { value: "NONE", label: "None" },
  { value: "DIABETES", label: "Diabetes" },
  { value: "PREDIABETES", label: "Prediabetes" },
  { value: "HIGH_BLOOD_PRESSURE", label: "High Blood Pressure" },
  { value: "HIGH_CHOLESTEROL", label: "High Cholesterol" },
  { value: "ANEMIA", label: "Anemia" },
  { value: "GERD", label: "GERD" },
  { value: "OTHER", label: "Other" },
] as const;

export const DIETARY_RESTRICTIONS = [
  { value: "GLUTEN_FREE", label: "Gluten Free" },
  { value: "LACTOSE_FREE", label: "Lactose Free" },
  { value: "LOW_CARB", label: "Low Carb" },
  { value: "LOW_SODIUM", label: "Low Sodium" },
  { value: "LOW_SUGAR", label: "Low Sugar" },
  { value: "HIGH_PROTEIN", label: "High Protein" },
  { value: "KETO", label: "Keto" },
  { value: "OTHER", label: "Other" },
] as const;

export const CUISINES = [
  { value: "INDIAN", label: "Indian", emoji: "🇮🇳" },
  { value: "BENGALI", label: "Bengali", emoji: "🇮🇳" },
  { value: "NORTH_INDIAN", label: "North Indian", emoji: "🇮🇳" },
  { value: "SOUTH_INDIAN", label: "South Indian", emoji: "🇮🇳" },
  { value: "PUNJABI", label: "Punjabi", emoji: "🇮🇳" },
  { value: "GUJARATI", label: "Gujarati", emoji: "🇮🇳" },
  { value: "MAHARASHTRIAN", label: "Maharashtrian", emoji: "🇮🇳" },
  { value: "KERALA", label: "Kerala", emoji: "🇮🇳" },
  { value: "HYDERABADI", label: "Hyderabadi", emoji: "🇮🇳" },
  { value: "CHINESE", label: "Chinese", emoji: "🇨🇳" },
  { value: "ITALIAN", label: "Italian", emoji: "🇮🇹" },
  { value: "WESTERN", label: "Western", emoji: "🍔" },
  { value: "MEXICAN", label: "Mexican", emoji: "🇲🇽" },
  { value: "OTHER", label: "Other", emoji: "🌍" },
] as const;

export const COOKING_ABILITIES = [
  { value: "MINIMAL", label: "Minimal" },
  { value: "BASIC", label: "Basic" },
  { value: "MODERATE", label: "Moderate" },
  { value: "ADVANCED", label: "Advanced" },
] as const;

export const BUDGET_TYPES = [
  { value: "GROCERIES_ONLY", label: "Groceries Only" },
  { value: "GROCERIES_AND_EATING_OUT", label: "Groceries & Eating Out" },
] as const;

export const PREFERENCE_TYPES = [
  { value: "LIKE", label: "Like" },
  { value: "DISLIKE", label: "Dislike" },
  { value: "NEVER", label: "Never" },
] as const;

export const GENDERS = [
  { value: "MALE", label: "Male" },
  { value: "FEMALE", label: "Female" },
  { value: "OTHER", label: "Other" },
] as const;

export const REPLACEMENT_REASONS = [
  { value: "TOO_EXPENSIVE", label: "Too expensive" },
  { value: "DONT_LIKE_INGREDIENTS", label: "Don't like the ingredients" },
  { value: "TOO_HARD_TO_COOK", label: "Too hard to cook" },
  { value: "NOT_ENOUGH_TIME", label: "Not enough time" },
  { value: "WANT_SOMETHING_ELSE", label: "Just want something else" },
] as const;

export const ONBOARDING_STEPS = [
  { path: "/onboarding/welcome", title: "Welcome", description: "Let's get started" },
  { path: "/onboarding/goals", title: "Goals", description: "What do you want to achieve?" },
  { path: "/onboarding/diet", title: "Diet", description: "Your dietary preferences" },
  { path: "/onboarding/allergies", title: "Allergies", description: "Any allergies or restrictions?" },
  { path: "/onboarding/cuisine", title: "Cuisine", description: "Your favorite cuisines" },
  { path: "/onboarding/budget", title: "Budget", description: "Your budget and cooking ability" }
];

export function getLabel(items: readonly {value: string; label: string}[], value: string): string {
  return items.find(i => i.value === value)?.label ?? value;
}

export function getEmoji(items: readonly {value: string; emoji?: string}[], value: string): string {
  return (items.find(i => i.value === value) as any)?.emoji ?? '';
}
