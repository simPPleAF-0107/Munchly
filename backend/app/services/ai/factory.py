from app.core.config import settings
from app.services.ai.base import AIService
from app.services.ai.gemini_provider import GeminiProvider

class AIServiceFactory:
    @staticmethod
    def create(provider: str = None) -> AIService:
        provider = provider or getattr(settings, "AI_PROVIDER", "gemini")
        if provider == "gemini":
            return GeminiProvider()
        raise ValueError(f"Unknown AI provider: {provider}")
    
    @staticmethod
    def create_optional() -> AIService | None:
        """Create AI service, returning None if not available."""
        try:
            service = AIServiceFactory.create()
            # Don't block on availability check here
            return service
        except Exception:
            return None
