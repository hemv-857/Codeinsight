from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_settings
from backend.app.schemas.health import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def read_health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Return backend liveness and version metadata."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        version=settings.version,
    )
