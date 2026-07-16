from dataclasses import dataclass

from backend.app.repositories.conversation_memory import (
    ConversationMemoryRepository,
    ConversationSession,
)
from backend.app.services.repository_qa import RepositoryQAAnswer


class ConversationMemoryError(Exception):
    """Raised when conversation memory cannot continue."""


@dataclass(frozen=True)
class RememberedAnswer:
    """A Q&A answer stored in conversation memory."""

    session_id: str
    answer: RepositoryQAAnswer


class ConversationMemoryService:
    """Coordinates repository Q&A session memory."""

    def __init__(self, repository: ConversationMemoryRepository) -> None:
        self.repository = repository

    def remember_turn(
        self,
        *,
        repository_path: str,
        question: str,
        answer: RepositoryQAAnswer,
        session_id: str | None,
    ) -> RememberedAnswer:
        if session_id is not None:
            existing = self.repository.get_session(session_id)
            if existing is not None and existing.repository_path != repository_path:
                raise ConversationMemoryError("Conversation session belongs to another repository.")
        resolved_session_id = self.repository.ensure_session(repository_path, session_id)
        self.repository.append_message(
            session_id=resolved_session_id,
            role="user",
            content=question,
        )
        self.repository.append_message(
            session_id=resolved_session_id,
            role="assistant",
            content=answer.answer,
            metadata={
                "mode": answer.mode,
                "confidence": answer.confidence,
                "supporting_files": list(answer.supporting_files),
                "supporting_symbols": list(answer.supporting_symbols),
            },
        )
        return RememberedAnswer(
            session_id=resolved_session_id,
            answer=answer.with_session(resolved_session_id),
        )

    def get_session(self, session_id: str) -> ConversationSession:
        session = self.repository.get_session(session_id)
        if session is None:
            raise ConversationMemoryError("Conversation session was not found.")
        return session
