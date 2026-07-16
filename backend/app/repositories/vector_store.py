import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, delete, insert, select, text

from backend.app.database.connection import create_sqlite_engine
from backend.app.services.embedding import ChunkEmbedding, RepositoryEmbeddings

metadata = MetaData()

vector_embeddings_table = Table(
    "vector_embeddings",
    metadata,
    Column("repository_path", Text, primary_key=True),
    Column("chunk_id", Text, primary_key=True),
    Column("model", String, nullable=False),
    Column("dimensions", Integer, nullable=False),
    Column("path", Text, nullable=False),
    Column("kind", String, nullable=False),
    Column("language", String, nullable=False),
    Column("start_line", Integer, nullable=False),
    Column("end_line", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("symbol_kind", String),
    Column("symbol_name", String),
    Column("symbol_parent", String),
    Column("embedding", Text, nullable=False),
    Column("stored_at", String, nullable=False),
)


class VectorStoreRepository:
    """Stores repository embedding vectors in SQLite."""

    def __init__(self, database_path: str) -> None:
        self.engine = create_sqlite_engine(Path(database_path))
        self.initialize()

    def initialize(self) -> None:
        metadata.create_all(self.engine)
        self._ensure_content_column()

    def _ensure_content_column(self) -> None:
        with self.engine.begin() as connection:
            columns = {
                str(row["name"])
                for row in connection.execute(text("PRAGMA table_info(vector_embeddings)"))
                .mappings()
                .all()
            }
            if "content" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE vector_embeddings ADD COLUMN content TEXT NOT NULL DEFAULT ''"
                    )
                )

    def replace(self, embeddings: RepositoryEmbeddings) -> int:
        stored_at = datetime.now(UTC).isoformat()
        with self.engine.begin() as connection:
            connection.execute(
                delete(vector_embeddings_table).where(
                    vector_embeddings_table.c.repository_path == embeddings.repository_path
                )
            )
            if embeddings.embeddings:
                connection.execute(
                    insert(vector_embeddings_table),
                    [
                        {
                            "repository_path": embeddings.repository_path,
                            "chunk_id": embedding.chunk_id,
                            "model": embeddings.model,
                            "dimensions": len(embedding.embedding),
                            "path": embedding.path,
                            "kind": embedding.kind,
                            "language": embedding.language,
                            "start_line": embedding.start_line,
                            "end_line": embedding.end_line,
                            "content": embedding.content,
                            "symbol_kind": embedding.symbol_kind,
                            "symbol_name": embedding.symbol_name,
                            "symbol_parent": embedding.symbol_parent,
                            "embedding": json.dumps(list(embedding.embedding)),
                            "stored_at": stored_at,
                        }
                        for embedding in embeddings.embeddings
                    ],
                )
        return len(embeddings.embeddings)

    def list_repository(self, repository_path: str) -> tuple[ChunkEmbedding, ...]:
        with self.engine.connect() as connection:
            rows = (
                connection.execute(
                    select(vector_embeddings_table)
                    .where(vector_embeddings_table.c.repository_path == repository_path)
                    .order_by(vector_embeddings_table.c.path, vector_embeddings_table.c.start_line)
                )
                .mappings()
                .all()
            )

        return tuple(
            ChunkEmbedding(
                chunk_id=str(row["chunk_id"]),
                path=str(row["path"]),
                kind=str(row["kind"]),
                language=str(row["language"]),
                start_line=int(row["start_line"]),
                end_line=int(row["end_line"]),
                content=str(row["content"]),
                symbol_kind=str(row["symbol_kind"]) if row["symbol_kind"] is not None else None,
                symbol_name=str(row["symbol_name"]) if row["symbol_name"] is not None else None,
                symbol_parent=(
                    str(row["symbol_parent"]) if row["symbol_parent"] is not None else None
                ),
                embedding=tuple(float(value) for value in json.loads(str(row["embedding"]))),
            )
            for row in rows
        )
