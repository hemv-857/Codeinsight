from pydantic import BaseModel, ConfigDict


class ConversationMessageResponse(BaseModel):
    """One stored conversation message."""

    id: int
    session_id: str
    role: str
    content: str
    metadata: dict[str, object]
    created_at: str

    model_config = ConfigDict(frozen=True)


class ConversationSessionResponse(BaseModel):
    """Stored conversation session with messages."""

    id: str
    repository_path: str
    created_at: str
    updated_at: str
    messages: list[ConversationMessageResponse]

    model_config = ConfigDict(frozen=True)
