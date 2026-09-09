from abc import ABC, abstractmethod

class AIService(ABC):
    """Abstract AI service interface. App works without any implementation."""
    
    @abstractmethod
    async def explain_meal_plan(
        self, meal_plan_summary: dict, user_profile: dict
    ) -> str:
        """Explain why these meals were recommended."""
    
    @abstractmethod
    async def suggest_substitution(
        self, recipe_name: str, ingredient_name: str, reason: str,
        dietary_restrictions: list[str]
    ) -> str:
        """Suggest ingredient substitutions."""
    
    @abstractmethod
    async def answer_food_question(
        self, question: str, user_context: dict
    ) -> str:
        """Answer a general food/nutrition question."""
    
    @abstractmethod
    async def generate_recipe_instructions(
        self, recipe_name: str, ingredients: list[dict]
    ) -> str:
        """Generate detailed cooking instructions."""
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the AI service is available."""
