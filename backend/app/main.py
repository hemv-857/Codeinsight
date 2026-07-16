import logging

from fastapi import FastAPI

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.repositories import router as repositories_router
from backend.app.core.config import Settings, get_cached_settings
from backend.app.core.dependencies import get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the Forge AI FastAPI application."""
    resolved_settings = settings or get_cached_settings()
    configure_logging(resolved_settings)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.version,
    )

    def provide_settings() -> Settings:
        return resolved_settings

    app.dependency_overrides[get_settings] = provide_settings
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(repositories_router)

    logger.info("Forge AI backend started", extra={"environment": resolved_settings.environment})
    return app


app = create_app()
