import google.generativeai as genai
import json
from app.core.config import settings
from app.services.ai.base import AIService
import logging

logger = logging.getLogger(__name__)

class GeminiProvider(AIService):
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    async def is_available(self) -> bool:
        return self.model is not None
        
    async def _generate_content(self, prompt: str, fallback: str) -> str:
        if not self.model:
            return fallback
        try:
            # We are in an async function, we can use generate_content_async if available, 
            # or just run it synchronously if not (for simplicity assuming generate_content_async or run_in_executor)
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content with Gemini: {e}")
            return fallback

    async def explain_meal_plan(
        self, meal_plan_summary: dict, user_profile: dict
    ) -> str:
        prompt = f"""
        You are the Munchly AI Assistant, an expert nutrition and meal planning advisor.
        Based on the user's profile and their recommended meal plan, briefly explain why this plan is good for them.
        Keep it encouraging, concise, and helpful.
        
        User Profile: {json.dumps(user_profile)}
        Meal Plan: {json.dumps(meal_plan_summary)}
        """
        fallback = "This meal plan is tailored to your nutritional needs and preferences, designed to help you reach your goals."
        return await self._generate_content(prompt, fallback)
    
    async def suggest_substitution(
        self, recipe_name: str, ingredient_name: str, reason: str,
        dietary_restrictions: list[str]
    ) -> str:
        prompt = f"""
        You are the Munchly AI Assistant.
        A user wants to substitute '{ingredient_name}' in the recipe '{recipe_name}' because: {reason}.
        Their dietary restrictions are: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}.
        Suggest 1-3 suitable alternatives, including how to adjust the quantities or cooking methods if necessary.
        Be concise and practical.
        """
        fallback = f"Consider replacing {ingredient_name} with an alternative that fits your dietary needs and the recipe's flavor profile."
        return await self._generate_content(prompt, fallback)
    
    async def answer_food_question(
        self, question: str, user_context: dict
    ) -> str:
        prompt = f"""
        You are the Munchly AI Assistant, an expert nutrition and cooking advisor.
        Answer the following user question concisely and accurately.
        
        User Context: {json.dumps(user_context)}
        Question: {question}
        
        Disclaimer: Remind the user that for medical conditions, they should consult a healthcare professional.
        """
        fallback = "I'm currently unable to answer this question. Please remember to consult a healthcare professional for medical advice."
        return await self._generate_content(prompt, fallback)
    
    async def generate_recipe_instructions(
        self, recipe_name: str, ingredients: list[dict]
    ) -> str:
        prompt = f"""
        You are the Munchly AI Assistant, a master chef.
        Provide step-by-step cooking instructions for '{recipe_name}' using these ingredients: {json.dumps(ingredients)}.
        Ensure steps are clear, concise, and safe.
        """
        fallback = f"Please search for a reliable recipe for {recipe_name} online to ensure you get the best cooking instructions."
        return await self._generate_content(prompt, fallback)
