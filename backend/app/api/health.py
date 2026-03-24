# Health check endpoint — confirms the API is running and config is loaded

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Returns app status and basic info. Used to verify the server is alive."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "debug": settings.debug,
        "weaviate_url": settings.weaviate_url,
    }
