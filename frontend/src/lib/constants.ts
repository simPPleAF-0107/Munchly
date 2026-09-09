export const DIET_TYPES = [
  "Omnivore",
  "Vegetarian",
  "Vegan",
  "Pescatarian",
  "Keto",
  "Paleo",
  "Mediterranean"
] as const;

export const ACTIVITY_LEVELS = [
  "Sedentary",
  "Lightly Active",
  "Moderately Active",
  "Very Active",
  "Extra Active"
] as const;

export const HEALTH_GOALS = [
  "Weight Loss",
  "Muscle Gain",
  "Maintenance",
  "Heart Health",
  "Energy Boost"
] as const;

export const MEAL_TYPES = [
  "Breakfast",
  "Lunch",
  "Dinner",
  "Snack"
] as const;

export const ALLERGENS = [
  "Dairy",
  "Egg",
  "Tree Nut",
  "Peanut",
  "Shellfish",
  "Wheat",
  "Soy",
  "Fish",
  "Sesame"
] as const;

export const MEDICAL_CONDITIONS = [
  "Diabetes Type 1",
  "Diabetes Type 2",
  "Hypertension",
  "Celiac Disease",
  "IBS",
  "PCOS"
] as const;

export const DIETARY_RESTRICTIONS = [
  "Gluten-Free",
  "Dairy-Free",
  "Low-FODMAP",
  "Halal",
  "Kosher",
  "Low-Sodium",
  "Low-Sugar"
] as const;

export const CUISINES = [
  { name: "Italian", emoji: "🇮🇹" },
  { name: "Indian", emoji: "🇮🇳" },
  { name: "Mexican", emoji: "🇲🇽" },
  { name: "Japanese", emoji: "🇯🇵" },
  { name: "Chinese", emoji: "🇨🇳" },
  { name: "Mediterranean", emoji: "🇬🇷" },
  { name: "American", emoji: "🇺🇸" },
  { name: "Thai", emoji: "🇹🇭" },
  { name: "Korean", emoji: "🇰🇷" },
  { name: "French", emoji: "🇫🇷" }
] as const;

export const COOKING_ABILITIES = [
  "Beginner",
  "Intermediate",
  "Advanced",
  "Expert"
] as const;

export const BUDGET_TYPES = [
  "Economy",
  "Moderate",
  "Premium",
  "Luxury"
] as const;

export const ONBOARDING_STEPS = [
  { path: "/onboarding/welcome", title: "Welcome", description: "Let's get started" },
  { path: "/onboarding/goals", title: "Goals", description: "What do you want to achieve?" },
  { path: "/onboarding/diet", title: "Diet", description: "Your dietary preferences" },
  { path: "/onboarding/allergies", title: "Allergies", description: "Any allergies or restrictions?" },
  { path: "/onboarding/cuisine", title: "Cuisine", description: "Your favorite cuisines" },
  { path: "/onboarding/budget", title: "Budget", description: "Your budget and cooking ability" }
];

export const REPLACEMENT_REASONS = [
  "Too expensive",
  "Don't like the ingredients",
  "Too hard to cook",
  "Not enough time",
  "Just want something else"
] as const;
