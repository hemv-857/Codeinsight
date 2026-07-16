from backend.app.core.config import Settings, get_cached_settings


def get_settings() -> Settings:
    """Provide application settings to FastAPI routes."""
    return get_cached_settings()
