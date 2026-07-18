from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class SystemUnderstandingRequest(BaseModel):
    """Request body for generating a system understanding report."""

    repository_path: Path


class UnderstandingComponentResponse(BaseModel):
    """Main component in a system understanding report."""

    name: str
    path: str
    role: str
    evidence: list[str]

    model_config = ConfigDict(frozen=True)


class UnderstandingFileResponse(BaseModel):
    """Important file in a system understanding report."""

    path: str
    language: str | None
    reason: str
    score: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class UnderstandingSymbolResponse(BaseModel):
    """Related symbol in a system understanding report."""

    name: str
    kind: str
    path: str
    line: int = Field(ge=1)
    reason: str

    model_config = ConfigDict(frozen=True)


class SystemUnderstandingStatsResponse(BaseModel):
    """System understanding report statistics."""

    file_count: int = Field(ge=0)
    parsed_file_count: int = Field(ge=0)
    symbol_count: int = Field(ge=0)
    dependency_count: int = Field(ge=0)
    call_count: int = Field(ge=0)
    diagram_count: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class SystemUnderstandingResponse(BaseModel):
    """One-click system understanding report response."""

    repository_path: str
    title: str
    application_overview: str
    architecture_summary: str
    main_components: list[UnderstandingComponentResponse]
    critical_execution_flows: list[str]
    important_services: list[UnderstandingSymbolResponse]
    database_interactions: list[str]
    external_dependencies: list[str]
    high_risk_modules: list[UnderstandingFileResponse]
    suggested_learning_path: list[str]
    architecture_diagram: str
    dependency_visualization: str
    important_files: list[UnderstandingFileResponse]
    related_symbols: list[UnderstandingSymbolResponse]
    evidence_paths: list[str]
    markdown: str
    stats: SystemUnderstandingStatsResponse

    model_config = ConfigDict(frozen=True)
