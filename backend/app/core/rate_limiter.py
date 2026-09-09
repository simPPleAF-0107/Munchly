from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

RATE_LIMITS = {
    "meal_plan_generate": "5/hour",
    "meal_replace": "30/hour",
    "ai_chat": "30/hour",
    "auth_register": "5/hour",
    "auth_login": "10/hour",
    "default": "100/hour"
}
