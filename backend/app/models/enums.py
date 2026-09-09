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
