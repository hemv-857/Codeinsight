from pathlib import Path

from backend.app.repositories.conversation_memory import ConversationMemoryRepository
from backend.app.services.conversation_memory import (
    ConversationMemoryError,
    ConversationMemoryService,
)
from backend.app.services.repository_qa import RepositoryQAAnswer


def create_answer(repository_path: str) -> RepositoryQAAnswer:
    return RepositoryQAAnswer(
        repository_path=repository_path,
        question="What is this repository?",
        answer="It is a small Python repository.",
        mode="summary",
        confidence=0.68,
        supporting_files=("app/main.py",),
        supporting_symbols=("main (function)",),
        snippets=(),
    )


def test_conversation_memory_persists_question_and_answer(tmp_path: Path) -> None:
    repository = ConversationMemoryRepository(str(tmp_path / "memory.sqlite3"))
    service = ConversationMemoryService(repository)
    answer = create_answer(str(tmp_path))

    remembered = service.remember_turn(
        repository_path=answer.repository_path,
        question=answer.question,
        answer=answer,
        session_id=None,
    )
    session = service.get_session(remembered.session_id)

    assert remembered.answer.session_id == remembered.session_id
    assert session.repository_path == str(tmp_path)
    assert [message.role for message in session.messages] == ["user", "assistant"]
    assert session.messages[1].metadata["supporting_files"] == ["app/main.py"]


def test_conversation_memory_reuses_existing_session(tmp_path: Path) -> None:
    repository = ConversationMemoryRepository(str(tmp_path / "memory.sqlite3"))
    service = ConversationMemoryService(repository)
    answer = create_answer(str(tmp_path))
    first = service.remember_turn(
        repository_path=answer.repository_path,
        question=answer.question,
        answer=answer,
        session_id=None,
    )

    second = service.remember_turn(
        repository_path=answer.repository_path,
        question="And auth?",
        answer=answer,
        session_id=first.session_id,
    )
    session = service.get_session(first.session_id)

    assert second.session_id == first.session_id
    assert len(session.messages) == 4


def test_conversation_memory_rejects_cross_repository_reuse(tmp_path: Path) -> None:
    repository = ConversationMemoryRepository(str(tmp_path / "memory.sqlite3"))
    service = ConversationMemoryService(repository)
    answer = create_answer(str(tmp_path / "one"))
    remembered = service.remember_turn(
        repository_path=answer.repository_path,
        question=answer.question,
        answer=answer,
        session_id=None,
    )

    try:
        service.remember_turn(
            repository_path=str(tmp_path / "two"),
            question=answer.question,
            answer=create_answer(str(tmp_path / "two")),
            session_id=remembered.session_id,
        )
    except ConversationMemoryError as error:
        assert "another repository" in str(error)
    else:
        raise AssertionError("Expected ConversationMemoryError.")
