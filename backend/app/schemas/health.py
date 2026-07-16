from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health endpoint response contract."""

    status: Literal["ok"]
    service: str
    environment: str
    version: str

    model_config = ConfigDict(frozen=True)
