import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, Text, insert, select

from backend.app.database.connection import create_sqlite_engine

metadata = MetaData()

conversation_sessions_table = Table(
    "conversation_sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("repository_path", Text, nullable=False),
    Column("created_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
)

conversation_messages_table = Table(
    "conversation_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", String, ForeignKey("conversation_sessions.id"), nullable=False),
    Column("role", String, nullable=False),
    Column("content", Text, nullable=False),
    Column("metadata", Text, nullable=False),
    Column("created_at", String, nullable=False),
)


@dataclass(frozen=True)
class ConversationMessage:
    """A stored conversation message."""

    id: int
    session_id: str
    role: str
    content: str
    metadata: dict[str, object]
    created_at: str


@dataclass(frozen=True)
class ConversationSession:
    """A stored repository conversation."""

    id: str
    repository_path: str
    created_at: str
    updated_at: str
    messages: tuple[ConversationMessage, ...]


class ConversationMemoryRepository:
    """Stores repository conversation memory in SQLite."""

    def __init__(self, database_path: str) -> None:
        self.engine = create_sqlite_engine(Path(database_path))
        self.initialize()

    def initialize(self) -> None:
        metadata.create_all(self.engine)

    def ensure_session(self, repository_path: str, session_id: str | None = None) -> str:
        now = datetime.now(UTC).isoformat()
        if session_id is not None and self.get_session(session_id) is not None:
            return session_id
        session_id = session_id or str(uuid4())
        with self.engine.begin() as connection:
            connection.execute(
                insert(conversation_sessions_table),
                {
                    "id": session_id,
                    "repository_path": repository_path,
                    "created_at": now,
                    "updated_at": now,
                },
            )
        return session_id

    def append_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> ConversationMessage:
        now = datetime.now(UTC).isoformat()
        with self.engine.begin() as connection:
            result = connection.execute(
                insert(conversation_messages_table),
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": json.dumps(metadata or {}),
                    "created_at": now,
                },
            )
            connection.execute(
                conversation_sessions_table.update()
                .where(conversation_sessions_table.c.id == session_id)
                .values(updated_at=now)
            )
            message_id = int(result.inserted_primary_key[0])
        return ConversationMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
            created_at=now,
        )

    def get_session(self, session_id: str) -> ConversationSession | None:
        with self.engine.connect() as connection:
            session = (
                connection.execute(
                    select(conversation_sessions_table).where(
                        conversation_sessions_table.c.id == session_id
                    )
                )
                .mappings()
                .first()
            )
            if session is None:
                return None
            rows = (
                connection.execute(
                    select(conversation_messages_table)
                    .where(conversation_messages_table.c.session_id == session_id)
                    .order_by(conversation_messages_table.c.id)
                )
                .mappings()
                .all()
            )
        return ConversationSession(
            id=str(session["id"]),
            repository_path=str(session["repository_path"]),
            created_at=str(session["created_at"]),
            updated_at=str(session["updated_at"]),
            messages=tuple(
                ConversationMessage(
                    id=int(row["id"]),
                    session_id=str(row["session_id"]),
                    role=str(row["role"]),
                    content=str(row["content"]),
                    metadata=dict(json.loads(str(row["metadata"]))),
                    created_at=str(row["created_at"]),
                )
                for row in rows
            ),
        )
