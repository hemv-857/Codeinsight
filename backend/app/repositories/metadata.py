from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    delete,
    insert,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Connection

from backend.app.database.connection import create_sqlite_engine
from backend.app.schemas.metadata import StoredDirectory, StoredFile, StoredRepositoryMetadata
from backend.app.schemas.repository_scan import RepositoryScanResult

metadata = MetaData()

repositories_table = Table(
    "repositories",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("path", Text, nullable=False, unique=True),
    Column("languages", Text, nullable=False),
    Column("extensions", Text, nullable=False),
    Column("indexed_at", String, nullable=False),
)

directories_table = Table(
    "directories",
    metadata,
    Column(
        "repository_id",
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("path", Text, primary_key=True),
)

files_table = Table(
    "files",
    metadata,
    Column(
        "repository_id",
        Integer,
        ForeignKey("repositories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("path", Text, primary_key=True),
    Column("extension", String, nullable=False),
    Column("language", String),
    Column("size_bytes", Integer, nullable=False),
    Column("sha256", String, nullable=False),
    Column("modified_at", String, nullable=False),
)


class MetadataRepository:
    """Stores repository scan metadata in SQLite through SQLAlchemy Core."""

    def __init__(self, database_path: str) -> None:
        self.engine = create_sqlite_engine(Path(database_path))
        self.initialize()

    def initialize(self) -> None:
        metadata.create_all(self.engine)

    def save_scan(
        self,
        name: str,
        scan: RepositoryScanResult,
        file_metadata: dict[str, tuple[str, datetime]],
    ) -> StoredRepositoryMetadata:
        indexed_at = datetime.now(UTC)
        with self.engine.begin() as connection:
            repository_id = self._upsert_repository(connection, name, scan, indexed_at)
            connection.execute(
                delete(directories_table).where(directories_table.c.repository_id == repository_id)
            )
            connection.execute(
                delete(files_table).where(files_table.c.repository_id == repository_id)
            )

            if scan.directories:
                connection.execute(
                    insert(directories_table),
                    [{"repository_id": repository_id, "path": path} for path in scan.directories],
                )
            if scan.files:
                connection.execute(
                    insert(files_table),
                    [
                        {
                            "repository_id": repository_id,
                            "path": file.path,
                            "extension": file.extension,
                            "language": file.language,
                            "size_bytes": file.size_bytes,
                            "sha256": file_metadata[file.path][0],
                            "modified_at": file_metadata[file.path][1].isoformat(),
                        }
                        for file in scan.files
                    ],
                )

        return self.get_repository(repository_id)

    def get_repository(self, repository_id: int) -> StoredRepositoryMetadata:
        with self.engine.connect() as connection:
            repository = (
                connection.execute(
                    select(repositories_table).where(repositories_table.c.id == repository_id)
                )
                .mappings()
                .one_or_none()
            )
            if repository is None:
                raise KeyError("Repository metadata was not found.")

            directories = (
                connection.execute(
                    select(directories_table.c.path)
                    .where(directories_table.c.repository_id == repository_id)
                    .order_by(directories_table.c.path)
                )
                .mappings()
                .all()
            )
            files = (
                connection.execute(
                    select(
                        files_table.c.path,
                        files_table.c.extension,
                        files_table.c.language,
                        files_table.c.size_bytes,
                        files_table.c.sha256,
                        files_table.c.modified_at,
                    )
                    .where(files_table.c.repository_id == repository_id)
                    .order_by(files_table.c.path)
                )
                .mappings()
                .all()
            )

        return StoredRepositoryMetadata(
            repository_id=int(repository["id"]),
            name=str(repository["name"]),
            path=str(repository["path"]),
            languages=self._decode_list(str(repository["languages"])),
            extensions=self._decode_list(str(repository["extensions"])),
            indexed_at=datetime.fromisoformat(str(repository["indexed_at"])),
            directories=[StoredDirectory(path=str(row["path"])) for row in directories],
            files=[
                StoredFile(
                    path=str(row["path"]),
                    extension=str(row["extension"]),
                    language=str(row["language"]) if row["language"] is not None else None,
                    size_bytes=int(row["size_bytes"]),
                    sha256=str(row["sha256"]),
                    modified_at=datetime.fromisoformat(str(row["modified_at"])),
                )
                for row in files
            ],
        )

    def _upsert_repository(
        self,
        connection: Connection,
        name: str,
        scan: RepositoryScanResult,
        indexed_at: datetime,
    ) -> int:
        statement = sqlite_insert(repositories_table).values(
            name=name,
            path=scan.repository_path,
            languages=self._encode_list(scan.languages),
            extensions=self._encode_list(scan.extensions),
            indexed_at=indexed_at.isoformat(),
        )
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=[repositories_table.c.path],
                set_={
                    "name": statement.excluded.name,
                    "languages": statement.excluded.languages,
                    "extensions": statement.excluded.extensions,
                    "indexed_at": statement.excluded.indexed_at,
                },
            )
        )
        repository = (
            connection.execute(
                select(repositories_table.c.id).where(
                    repositories_table.c.path == scan.repository_path
                )
            )
            .mappings()
            .one_or_none()
        )
        if repository is None:
            raise RuntimeError("Repository metadata was not persisted.")
        return int(repository["id"])

    def _encode_list(self, values: list[str]) -> str:
        return "\n".join(values)

    def _decode_list(self, value: str) -> list[str]:
        if not value:
            return []
        return value.split("\n")
