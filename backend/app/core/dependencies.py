from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from graph.call_graph import CallGraphService
from graph.dependency_graph import DependencyGraphService
from graph.fallback_repository import FallbackKnowledgeGraphRepository
from graph.knowledge_graph import KnowledgeGraphRepository, KnowledgeGraphService
from graph.neo4j_repository import Neo4jKnowledgeGraphRepository
from graph.networkx_repository import NetworkXKnowledgeGraphRepository
from graph.persistent_repository import PersistentKnowledgeGraphRepository
from graph.sqlite_repository import SQLiteKnowledgeGraphRepository
from parser.tree_sitter_parser import TreeSitterParserService

from backend.app.core.config import Settings, get_cached_settings
from backend.app.repositories.metadata import MetadataRepository
from backend.app.services.metadata import MetadataService
from backend.app.services.repository_import import RepositoryImportService
from backend.app.services.repository_scanner import RepositoryScannerService


def get_settings() -> Settings:
    """Provide application settings to FastAPI routes."""
    return get_cached_settings()


@lru_cache(maxsize=16)
def get_cached_repository_import_service(
    storage_root: str,
    clone_timeout_seconds: int,
    max_zip_bytes: int,
) -> RepositoryImportService:
    """Return a repository import service for a storage configuration."""
    return RepositoryImportService(
        storage_root=Path(storage_root),
        clone_timeout_seconds=clone_timeout_seconds,
        max_zip_bytes=max_zip_bytes,
    )


def get_repository_import_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> RepositoryImportService:
    """Provide repository import operations to API routes."""
    return get_cached_repository_import_service(
        storage_root=str(settings.repository_storage_path),
        clone_timeout_seconds=settings.repository_clone_timeout_seconds,
        max_zip_bytes=settings.repository_zip_max_bytes,
    )


@lru_cache(maxsize=1)
def get_repository_scanner_service() -> RepositoryScannerService:
    """Provide repository scanning operations to API routes."""
    return RepositoryScannerService()


@lru_cache(maxsize=16)
def get_cached_metadata_repository(database_path: str) -> MetadataRepository:
    """Return a SQLite-backed metadata repository."""
    return MetadataRepository(database_path)


def get_metadata_service(
    settings: Annotated[Settings, Depends(get_settings)],
    scanner: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
) -> MetadataService:
    """Provide metadata persistence operations to API routes."""
    return MetadataService(
        scanner=scanner,
        repository=get_cached_metadata_repository(str(settings.metadata_database_path)),
    )


@lru_cache(maxsize=1)
def get_tree_sitter_parser_service() -> TreeSitterParserService:
    """Provide Tree-sitter parsing operations to API routes."""
    return TreeSitterParserService()


def get_dependency_graph_service(
    scanner: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
    parser: Annotated[TreeSitterParserService, Depends(get_tree_sitter_parser_service)],
) -> DependencyGraphService:
    """Provide dependency graph construction operations to API routes."""
    return DependencyGraphService(scanner=scanner, parser=parser)


def get_call_graph_service(
    scanner: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
    parser: Annotated[TreeSitterParserService, Depends(get_tree_sitter_parser_service)],
) -> CallGraphService:
    """Provide call graph construction operations to API routes."""
    return CallGraphService(scanner=scanner, parser=parser)


@lru_cache(maxsize=16)
def get_cached_neo4j_repository(
    uri: str,
    username: str,
    password: str,
    database: str,
) -> Neo4jKnowledgeGraphRepository:
    """Return a Neo4j-backed knowledge graph repository."""
    return Neo4jKnowledgeGraphRepository.connect(
        uri=uri,
        username=username,
        password=password,
        database=database,
    )


@lru_cache(maxsize=16)
def get_cached_knowledge_graph_repository(
    uri: str,
    username: str,
    password: str,
    database: str,
) -> KnowledgeGraphRepository:
    """Return a Neo4j-first repository with an in-memory NetworkX fallback."""
    return FallbackKnowledgeGraphRepository(
        primary=get_cached_neo4j_repository(
            uri=uri,
            username=username,
            password=password,
            database=database,
        ),
        fallback=NetworkXKnowledgeGraphRepository(),
    )


@lru_cache(maxsize=16)
def get_cached_sqlite_graph_repository(database_path: str) -> SQLiteKnowledgeGraphRepository:
    """Return a SQLite-backed durable graph snapshot repository."""
    return SQLiteKnowledgeGraphRepository(database_path)


@lru_cache(maxsize=16)
def get_cached_persistent_knowledge_graph_repository(
    uri: str,
    username: str,
    password: str,
    database: str,
    graph_database_path: str,
) -> KnowledgeGraphRepository:
    """Return a live graph repository with durable SQLite snapshots."""
    return PersistentKnowledgeGraphRepository(
        live_repository=get_cached_knowledge_graph_repository(
            uri=uri,
            username=username,
            password=password,
            database=database,
        ),
        durable_repository=get_cached_sqlite_graph_repository(graph_database_path),
    )


def get_knowledge_graph_service(
    settings: Annotated[Settings, Depends(get_settings)],
    scanner: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
    parser: Annotated[TreeSitterParserService, Depends(get_tree_sitter_parser_service)],
    dependency_graph: Annotated[DependencyGraphService, Depends(get_dependency_graph_service)],
    call_graph: Annotated[CallGraphService, Depends(get_call_graph_service)],
) -> KnowledgeGraphService:
    """Provide knowledge graph construction and persistence operations."""
    return KnowledgeGraphService(
        scanner=scanner,
        parser=parser,
        dependency_graph=dependency_graph,
        call_graph=call_graph,
        repository=get_cached_persistent_knowledge_graph_repository(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
            graph_database_path=str(settings.graph_database_path),
        ),
    )
