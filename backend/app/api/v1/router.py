from fastapi import APIRouter
from app.api.v1.endpoints import auth, onboarding, meal_plans, grocery, ai

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(onboarding.router)
api_router.include_router(meal_plans.router)
api_router.include_router(grocery.router)
api_router.include_router(ai.router)
