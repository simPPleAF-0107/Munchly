from fastapi import APIRouter, Depends, HTTPException, Request
import uuid
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.services.ai.factory import AIServiceFactory
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.rate_limiter import limiter
from app.models.enums import SubscriptionTier

router = APIRouter(prefix="/ai", tags=["ai"])

class ExplainRequest(BaseModel):
    meal_plan_id: uuid.UUID
    meal_plan_summary: dict

class SubstituteRequest(BaseModel):
    recipe_name: str
    ingredient_name: str
    reason: str

class AskRequest(BaseModel):
    question: str

class RecipeInstructionsRequest(BaseModel):
    recipe_name: str
    ingredients: List[dict]

def get_ai_limit(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and getattr(user, "subscription_tier", None) == SubscriptionTier.PLUS:
        return "100000/hour"
    return "30/hour"

@router.post("/explain")
@limiter.limit(get_ai_limit)
async def explain_meal_plan(
    request: Request,
    payload: ExplainRequest,
    current_user: User = Depends(get_current_user)
):
    ai = AIServiceFactory.create_optional()
    if not ai or not await ai.is_available():
        return {"explanation": "AI assistant is currently unavailable. Your meal plan works perfectly without it."}
    
    tier = getattr(current_user.subscription_tier, "name", "FREE") if hasattr(current_user, "subscription_tier") else "FREE"
    user_profile = {"id": str(current_user.id), "tier": tier}
    result = await ai.explain_meal_plan(payload.meal_plan_summary, user_profile)
    return {"explanation": result}

@router.post("/substitute")
@limiter.limit(get_ai_limit)
async def suggest_substitution(
    request: Request,
    payload: SubstituteRequest,
    current_user: User = Depends(get_current_user)
):
    ai = AIServiceFactory.create_optional()
    if not ai or not await ai.is_available():
        return {"suggestion": "AI assistant is currently unavailable. Consider using standard substitutions for this ingredient."}
    
    restrictions = [d.name for d in current_user.dietary_restrictions] if hasattr(current_user, "dietary_restrictions") and current_user.dietary_restrictions else []
    result = await ai.suggest_substitution(payload.recipe_name, payload.ingredient_name, payload.reason, restrictions)
    return {"suggestion": result}

@router.post("/ask")
@limiter.limit(get_ai_limit)
async def ask_question(
    request: Request,
    payload: AskRequest,
    current_user: User = Depends(get_current_user)
):
    ai = AIServiceFactory.create_optional()
    if not ai or not await ai.is_available():
        return {"answer": "AI assistant is currently unavailable. Please remember to consult a healthcare professional for medical advice."}
    
    context = {"id": str(current_user.id)}
    result = await ai.answer_food_question(payload.question, context)
    return {"answer": result}

@router.post("/recipe/instructions")
@limiter.limit(get_ai_limit)
async def generate_recipe_instructions(
    request: Request,
    payload: RecipeInstructionsRequest,
    current_user: User = Depends(get_current_user)
):
    ai = AIServiceFactory.create_optional()
    if not ai or not await ai.is_available():
        return {"instructions": f"AI assistant is currently unavailable. Please search for a reliable recipe for {payload.recipe_name} online."}
    
    result = await ai.generate_recipe_instructions(payload.recipe_name, payload.ingredients)
    return {"instructions": result}

@router.get("/status")
async def ai_status():
    ai = AIServiceFactory.create_optional()
    available = ai is not None and await ai.is_available()
    return {"available": available}
