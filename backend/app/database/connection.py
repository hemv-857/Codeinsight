from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event


def create_sqlite_engine(database_path: Path) -> Engine:
    """Create a SQLite SQLAlchemy engine with foreign keys enabled."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{database_path}", future=True)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
