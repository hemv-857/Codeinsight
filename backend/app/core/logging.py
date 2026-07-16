import logging

from backend.app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure process logging once during application startup."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=settings.log_level,
    )
