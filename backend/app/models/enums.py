import enum

class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class ActivityLevel(str, enum.Enum):
    SEDENTARY = "SEDENTARY"
    LIGHTLY_ACTIVE = "LIGHTLY_ACTIVE"
    MODERATELY_ACTIVE = "MODERATELY_ACTIVE"
    VERY_ACTIVE = "VERY_ACTIVE"
    EXTREMELY_ACTIVE = "EXTREMELY_ACTIVE"

class HealthGoal(str, enum.Enum):
    LOSE_WEIGHT = "LOSE_WEIGHT"
    MAINTAIN_WEIGHT = "MAINTAIN_WEIGHT"
    GAIN_WEIGHT = "GAIN_WEIGHT"
    BUILD_MUSCLE = "BUILD_MUSCLE"
    IMPROVE_FITNESS = "IMPROVE_FITNESS"
    EAT_HEALTHIER = "EAT_HEALTHIER"

class DietType(str, enum.Enum):
    VEGAN = "VEGAN"
    VEGETARIAN = "VEGETARIAN"
    EGGETARIAN = "EGGETARIAN"
    NON_VEGETARIAN = "NON_VEGETARIAN"

class MealType(str, enum.Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"

class PreferenceType(str, enum.Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    NEVER = "NEVER"

class CookingAbility(str, enum.Enum):
    MINIMAL = "MINIMAL"
    BASIC = "BASIC"
    MODERATE = "MODERATE"
    ADVANCED = "ADVANCED"

class Allergen(str, enum.Enum):
    PEANUTS = "PEANUTS"
    TREE_NUTS = "TREE_NUTS"
    MILK = "MILK"
    EGGS = "EGGS"
    SOY = "SOY"
    WHEAT = "WHEAT"
    FISH = "FISH"
    SHELLFISH = "SHELLFISH"
    SESAME = "SESAME"
    CUSTOM = "CUSTOM"

class MedicalCondition(str, enum.Enum):
    NONE = "NONE"
    DIABETES = "DIABETES"
    PREDIABETES = "PREDIABETES"
    HIGH_BLOOD_PRESSURE = "HIGH_BLOOD_PRESSURE"
    HIGH_CHOLESTEROL = "HIGH_CHOLESTEROL"
    ANEMIA = "ANEMIA"
    GERD = "GERD"
    OTHER = "OTHER"

class DietaryRestriction(str, enum.Enum):
    GLUTEN_FREE = "GLUTEN_FREE"
    LACTOSE_FREE = "LACTOSE_FREE"
    LOW_CARB = "LOW_CARB"
    LOW_SODIUM = "LOW_SODIUM"
    LOW_SUGAR = "LOW_SUGAR"
    HIGH_PROTEIN = "HIGH_PROTEIN"
    KETO = "KETO"
    OTHER = "OTHER"

class Cuisine(str, enum.Enum):
    INDIAN = "INDIAN"
    BENGALI = "BENGALI"
    NORTH_INDIAN = "NORTH_INDIAN"
    SOUTH_INDIAN = "SOUTH_INDIAN"
    PUNJABI = "PUNJABI"
    GUJARATI = "GUJARATI"
    MAHARASHTRIAN = "MAHARASHTRIAN"
    KERALA = "KERALA"
    HYDERABADI = "HYDERABADI"
    CHINESE = "CHINESE"
    ITALIAN = "ITALIAN"
    WESTERN = "WESTERN"
    MEXICAN = "MEXICAN"
    OTHER = "OTHER"

class BudgetType(str, enum.Enum):
    GROCERIES_ONLY = "GROCERIES_ONLY"
    GROCERIES_AND_EATING_OUT = "GROCERIES_AND_EATING_OUT"

class OptionType(str, enum.Enum):
    BEST = "BEST"
    BUDGET = "BUDGET"
    VARIETY = "VARIETY"

class MealAction(str, enum.Enum):
    EATEN = "EATEN"
    SKIPPED = "SKIPPED"
    REPLACED = "REPLACED"
    FAVORITED = "FAVORITED"

class RuleScope(str, enum.Enum):
    PER_MEAL = "PER_MEAL"
    PER_DAY = "PER_DAY"
    PER_WEEK = "PER_WEEK"

class RuleOperator(str, enum.Enum):
    MIN = "MIN"
    MAX = "MAX"

class FoodCategory(str, enum.Enum):
    GRAIN = "GRAIN"
    PULSE = "PULSE"
    VEGETABLE = "VEGETABLE"
    FRUIT = "FRUIT"
    DAIRY = "DAIRY"
    MEAT = "MEAT"
    FISH_SEAFOOD = "FISH_SEAFOOD"
    EGG = "EGG"
    OIL_FAT = "OIL_FAT"
    SPICE = "SPICE"
    NUT_SEED = "NUT_SEED"
    SWEETENER = "SWEETENER"
    BEVERAGE = "BEVERAGE"
    OTHER = "OTHER"

class SubscriptionTier(str, enum.Enum):
    FREE = "FREE"
    PLUS = "PLUS"

class Difficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class MealPlanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class EventType(str, enum.Enum):
    """Immutable behavioral event types."""
    # Meal plan events
    MEAL_SUGGESTED = "MEAL_SUGGESTED"
    MEAL_VIEWED = "MEAL_VIEWED"
    MEAL_SELECTED = "MEAL_SELECTED"
    MEAL_EATEN = "MEAL_EATEN"
    MEAL_SKIPPED = "MEAL_SKIPPED"
    MEAL_REPLACED = "MEAL_REPLACED"
    MEAL_FAVORITED = "MEAL_FAVORITED"
    # Feedback events
    FEEDBACK_SUBMITTED = "FEEDBACK_SUBMITTED"
    INGREDIENT_REJECTED = "INGREDIENT_REJECTED"
    PREFERENCE_UPDATED = "PREFERENCE_UPDATED"
    # Check-in events
    DAILY_CHECKIN = "DAILY_CHECKIN"
    PANTRY_UPDATED = "PANTRY_UPDATED"
    CRAVING_OVERRIDE = "CRAVING_OVERRIDE"
    # Plan events
    PLAN_GENERATED = "PLAN_GENERATED"
    PLAN_VALIDATED = "PLAN_VALIDATED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"

class NutritionConfidence(str, enum.Enum):
    """How trustworthy is the nutrition data for a recipe."""
    VERIFIED = "VERIFIED"         # Direct from IFCT/USDA with source_id
    CALCULATED = "CALCULATED"     # Computed from VERIFIED ingredient data
    ESTIMATED = "ESTIMATED"       # Some ingredient data missing
    INCOMPLETE = "INCOMPLETE"     # >30% data gaps

class PlanChangeLevel(str, enum.Enum):
    """Plan stability levels - default to smallest possible change."""
    UNCHANGED = "UNCHANGED"
    MINOR_ADJUSTMENT = "MINOR_ADJUSTMENT"
    MEAL_REPLACED = "MEAL_REPLACED"
    DAY_REOPTIMIZED = "DAY_REOPTIMIZED"
    FULL_REGENERATION = "FULL_REGENERATION"

class ExerciseType(str, enum.Enum):
    NONE = "NONE"
    GYM_WEIGHTS = "GYM_WEIGHTS"
    CARDIO = "CARDIO"
    YOGA = "YOGA"
    SPORTS = "SPORTS"
    WALKING = "WALKING"
    SWIMMING = "SWIMMING"
    HOME_WORKOUT = "HOME_WORKOUT"
    MIXED = "MIXED"
    OTHER = "OTHER"

class WorkoutIntensity(str, enum.Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class FitnessGoal(str, enum.Enum):
    NONE = "NONE"
    BUILD_STRENGTH = "BUILD_STRENGTH"
    BUILD_MUSCLE = "BUILD_MUSCLE"
    LOSE_FAT = "LOSE_FAT"
    IMPROVE_ENDURANCE = "IMPROVE_ENDURANCE"
    GENERAL_FITNESS = "GENERAL_FITNESS"
    FLEXIBILITY = "FLEXIBILITY"

class BulkCutStatus(str, enum.Enum):
    NONE = "NONE"
    BULKING = "BULKING"
    CUTTING = "CUTTING"
    MAINTENANCE = "MAINTENANCE"
    LEAN_BULK = "LEAN_BULK"
    RECOMP = "RECOMP"

class CookingEffort(str, enum.Enum):
    MINIMAL = "MINIMAL"    # Microwave, toast, assemble
    EASY = "EASY"          # 1-pan, under 20 min
    MODERATE = "MODERATE"  # Standard cooking
    ELABORATE = "ELABORATE" # Multi-step, specialty

class FoodWastePreference(str, enum.Enum):
    NOT_IMPORTANT = "NOT_IMPORTANT"
    SOMEWHAT_IMPORTANT = "SOMEWHAT_IMPORTANT"
    VERY_IMPORTANT = "VERY_IMPORTANT"

class HungerLevel(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class PreferenceStrictness(str, enum.Enum):
    FLEXIBLE = "FLEXIBLE"       # Happy to try new things
    MODERATE = "MODERATE"       # Likes familiar, open to occasional variety
    STRICT = "STRICT"           # Stick to what I know

class WorkoutTiming(str, enum.Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    NO_FIXED_TIME = "NO_FIXED_TIME"
