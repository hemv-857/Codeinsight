from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from graph.call_graph import CallGraph, CallGraphError, CallGraphService
from graph.dependency_graph import DependencyGraph, DependencyGraphError, DependencyGraphService
from graph.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphError,
    KnowledgeGraphPersistenceResult,
    KnowledgeGraphService,
)
from parser.tree_sitter_parser import (
    ParseTreeSummary,
    TreeSitterParseError,
    TreeSitterParserService,
)

from backend.app.core.dependencies import (
    get_architecture_explanation_service,
    get_call_graph_service,
    get_dependency_graph_service,
    get_embedding_service,
    get_hybrid_retrieval_service,
    get_knowledge_graph_service,
    get_metadata_service,
    get_repository_chunker_service,
    get_repository_import_service,
    get_repository_qa_service,
    get_repository_scanner_service,
    get_repository_summary_service,
    get_tree_sitter_parser_service,
    get_vector_store_service,
)
from backend.app.schemas.architecture_explanation import (
    ArchitectureComponentResponse,
    ArchitectureExplanationRequest,
    ArchitectureExplanationResponse,
    ImportedArchitectureExplanationRequest,
)
from backend.app.schemas.call_graph import (
    CallGraphEdgeResponse,
    CallGraphNodeResponse,
    CallGraphRequest,
    CallGraphResponse,
    CallGraphStatsResponse,
)
from backend.app.schemas.dependency_graph import (
    DependencyEdgeResponse,
    DependencyGraphRequest,
    DependencyGraphResponse,
    DependencyGraphStatsResponse,
    DependencyNodeResponse,
)
from backend.app.schemas.embedding import (
    ChunkEmbeddingResponse,
    RepositoryEmbeddingRequest,
    RepositoryEmbeddingsResponse,
    RepositoryEmbeddingStatsResponse,
)
from backend.app.schemas.knowledge_graph import (
    KnowledgeGraphPersistenceResponse,
    KnowledgeGraphRequest,
    KnowledgeGraphResponse,
    KnowledgeGraphStatsResponse,
)
from backend.app.schemas.metadata import MetadataPersistRequest, StoredRepositoryMetadata
from backend.app.schemas.parse import (
    ParseFileRequest,
    ParseRepositoryResponse,
    ParseTreeResponse,
    SourceCallResponse,
    SourcePoint,
    SourceSymbolResponse,
)
from backend.app.schemas.repository_chunk import (
    RepositoryChunkRequest,
    RepositoryChunkResponseItem,
    RepositoryChunksResponse,
    RepositoryChunkStatsResponse,
    SkippedChunkFileResponse,
)
from backend.app.schemas.repository_import import RepositoryImportRequest, RepositoryImportResponse
from backend.app.schemas.repository_qa import (
    ImportedRepositoryQARequest,
    RepositoryQARequest,
    RepositoryQAResponse,
    RepositoryQASnippetResponse,
)
from backend.app.schemas.repository_scan import RepositoryScanRequest, RepositoryScanResult
from backend.app.schemas.repository_summary import (
    RepositorySummaryFileResponse,
    RepositorySummaryLanguageResponse,
    RepositorySummaryRequest,
    RepositorySummaryResponse,
    RepositorySummaryStatsResponse,
    RepositorySummarySymbolResponse,
)
from backend.app.schemas.retrieval import (
    HybridRetrievalRequest,
    HybridRetrievalResponse,
    HybridRetrievalResultResponse,
    HybridRetrievalStatsResponse,
    ImportedHybridRetrievalRequest,
)
from backend.app.schemas.vector_store import VectorStoreRequest, VectorStoreResponse
from backend.app.services.architecture_explanation import (
    ArchitectureExplanation,
    ArchitectureExplanationError,
    ArchitectureExplanationService,
)
from backend.app.services.embedding import EmbeddingError, EmbeddingService, RepositoryEmbeddings
from backend.app.services.metadata import MetadataService
from backend.app.services.repository_chunker import (
    RepositoryChunkError,
    RepositoryChunkerService,
    RepositoryChunks,
)
from backend.app.services.repository_import import RepositoryImportError, RepositoryImportService
from backend.app.services.repository_qa import (
    RepositoryQAAnswer,
    RepositoryQAError,
    RepositoryQAService,
)
from backend.app.services.repository_scanner import RepositoryScanError, RepositoryScannerService
from backend.app.services.repository_summary import (
    RepositorySummary,
    RepositorySummaryError,
    RepositorySummaryService,
)
from backend.app.services.retrieval import HybridRetrieval, HybridRetrievalService, RetrievalError
from backend.app.services.vector_store import VectorStoreResult, VectorStoreService

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


def to_architecture_explanation_response(
    result: ArchitectureExplanation,
) -> ArchitectureExplanationResponse:
    """Convert architecture explanation output into an API response."""
    return ArchitectureExplanationResponse(
        repository_path=result.repository_path,
        focus=result.focus,
        overview=result.overview,
        components=[
            ArchitectureComponentResponse(
                name=component.name,
                path=component.path,
                role=component.role,
                evidence=list(component.evidence),
            )
            for component in result.components
        ],
        dependency_flow=list(result.dependency_flow),
        call_flow=list(result.call_flow),
        observations=list(result.observations),
        evidence_paths=list(result.evidence_paths),
        confidence=result.confidence,
    )


def to_repository_qa_response(result: RepositoryQAAnswer) -> RepositoryQAResponse:
    """Convert repository Q&A output into an API response."""
    return RepositoryQAResponse(
        repository_path=result.repository_path,
        question=result.question,
        answer=result.answer,
        mode=result.mode,
        confidence=result.confidence,
        supporting_files=list(result.supporting_files),
        supporting_symbols=list(result.supporting_symbols),
        snippets=[
            RepositoryQASnippetResponse(
                path=snippet.path,
                start_line=snippet.start_line,
                end_line=snippet.end_line,
                content=snippet.content,
                score=snippet.score,
            )
            for snippet in result.snippets
        ],
    )


def to_repository_embeddings_response(
    embeddings: RepositoryEmbeddings,
) -> RepositoryEmbeddingsResponse:
    """Convert repository embeddings into an API response."""
    return RepositoryEmbeddingsResponse(
        repository_path=embeddings.repository_path,
        model=embeddings.model,
        embeddings=[
            ChunkEmbeddingResponse(
                chunk_id=embedding.chunk_id,
                path=embedding.path,
                kind=embedding.kind,
                language=embedding.language,
                start_line=embedding.start_line,
                end_line=embedding.end_line,
                embedding=list(embedding.embedding),
                symbol_kind=embedding.symbol_kind,
                symbol_name=embedding.symbol_name,
                symbol_parent=embedding.symbol_parent,
            )
            for embedding in embeddings.embeddings
        ],
        skipped_files=[
            SkippedChunkFileResponse(path=file.path, reason=file.reason)
            for file in embeddings.skipped_files
        ],
        stats=RepositoryEmbeddingStatsResponse(
            chunk_count=embeddings.stats.chunk_count,
            embedding_count=embeddings.stats.embedding_count,
            dimensions=embeddings.stats.dimensions,
            skipped_file_count=embeddings.stats.skipped_file_count,
        ),
    )


def to_vector_store_response(result: VectorStoreResult) -> VectorStoreResponse:
    """Convert vector storage output into an API response."""
    return VectorStoreResponse(
        repository_path=result.repository_path,
        model=result.model,
        stored_embedding_count=result.stored_embedding_count,
        dimensions=result.dimensions,
        backend=result.backend,
        skipped_file_count=result.skipped_file_count,
    )


def to_hybrid_retrieval_response(result: HybridRetrieval) -> HybridRetrievalResponse:
    """Convert hybrid retrieval output into an API response."""
    return HybridRetrievalResponse(
        repository_path=result.repository_path,
        query=result.query,
        model=result.model,
        results=[
            HybridRetrievalResultResponse(
                chunk_id=item.chunk_id,
                path=item.path,
                kind=item.kind,
                language=item.language,
                start_line=item.start_line,
                end_line=item.end_line,
                content=item.content,
                score=item.score,
                vector_score=item.vector_score,
                keyword_score=item.keyword_score,
                graph_score=item.graph_score,
                related_paths=list(item.related_paths),
                symbol_kind=item.symbol_kind,
                symbol_name=item.symbol_name,
                symbol_parent=item.symbol_parent,
            )
            for item in result.results
        ],
        stats=HybridRetrievalStatsResponse(
            result_count=result.stats.result_count,
            searched_embedding_count=result.stats.searched_embedding_count,
            dimensions=result.stats.dimensions,
        ),
    )


def to_repository_summary_response(result: RepositorySummary) -> RepositorySummaryResponse:
    """Convert repository summary output into an API response."""
    return RepositorySummaryResponse(
        repository_path=result.repository_path,
        overview=result.overview,
        languages=[
            RepositorySummaryLanguageResponse(
                language=item.language,
                file_count=item.file_count,
                size_bytes=item.size_bytes,
            )
            for item in result.languages
        ],
        key_files=[
            RepositorySummaryFileResponse(
                path=item.path,
                language=item.language,
                size_bytes=item.size_bytes,
                symbol_count=item.symbol_count,
                dependency_count=item.dependency_count,
                dependent_count=item.dependent_count,
            )
            for item in result.key_files
        ],
        key_symbols=[
            RepositorySummarySymbolResponse(
                name=item.name,
                kind=item.kind,
                path=item.path,
                line=item.line,
                parent=item.parent,
            )
            for item in result.key_symbols
        ],
        dependency_highlights=list(result.dependency_highlights),
        call_highlights=list(result.call_highlights),
        evidence_paths=list(result.evidence_paths),
        embedding_indexed=result.embedding_indexed,
        stats=RepositorySummaryStatsResponse(
            file_count=result.stats.file_count,
            directory_count=result.stats.directory_count,
            language_count=result.stats.language_count,
            parsed_file_count=result.stats.parsed_file_count,
            skipped_parse_file_count=result.stats.skipped_parse_file_count,
            symbol_count=result.stats.symbol_count,
            dependency_count=result.stats.dependency_count,
            callable_count=result.stats.callable_count,
            call_count=result.stats.call_count,
            indexed_embedding_count=result.stats.indexed_embedding_count,
        ),
    )


def to_repository_chunks_response(chunks: RepositoryChunks) -> RepositoryChunksResponse:
    """Convert repository chunks into an API response."""
    return RepositoryChunksResponse(
        repository_path=chunks.repository_path,
        chunks=[
            RepositoryChunkResponseItem(
                id=chunk.id,
                kind=chunk.kind,
                path=chunk.path,
                language=chunk.language,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                char_count=chunk.char_count,
                symbol_kind=chunk.symbol_kind,
                symbol_name=chunk.symbol_name,
                symbol_parent=chunk.symbol_parent,
            )
            for chunk in chunks.chunks
        ],
        skipped_files=[
            SkippedChunkFileResponse(path=file.path, reason=file.reason)
            for file in chunks.skipped_files
        ],
        stats=RepositoryChunkStatsResponse(
            source_file_count=chunks.stats.source_file_count,
            chunk_count=chunks.stats.chunk_count,
            file_chunk_count=chunks.stats.file_chunk_count,
            symbol_chunk_count=chunks.stats.symbol_chunk_count,
            skipped_file_count=chunks.stats.skipped_file_count,
        ),
    )


def to_call_graph_response(graph: CallGraph) -> CallGraphResponse:
    """Convert call-graph domain output into an API response."""
    return CallGraphResponse(
        repository_path=graph.repository_path,
        nodes=[
            CallGraphNodeResponse(
                id=node.id,
                name=node.name,
                kind=node.kind,
                path=node.path,
                line=node.line,
                parent=node.parent,
            )
            for node in graph.nodes
        ],
        edges=[
            CallGraphEdgeResponse(
                source=edge.source,
                target=edge.target,
                caller=edge.caller,
                callee=edge.callee,
                path=edge.path,
                line=edge.line,
                recursive=edge.recursive,
            )
            for edge in graph.edges
        ],
        unresolved_calls=list(graph.unresolved_calls),
        stats=CallGraphStatsResponse(
            callable_count=graph.stats.callable_count,
            call_count=graph.stats.call_count,
            resolved_call_count=graph.stats.resolved_call_count,
            unresolved_call_count=graph.stats.unresolved_call_count,
            recursive_call_count=graph.stats.recursive_call_count,
        ),
    )


def to_knowledge_graph_response(
    graph: KnowledgeGraph,
    persistence: KnowledgeGraphPersistenceResult,
) -> KnowledgeGraphResponse:
    """Convert knowledge-graph domain output into an API response."""
    return KnowledgeGraphResponse(
        repository_path=graph.repository_path,
        stats=KnowledgeGraphStatsResponse(
            node_count=graph.stats.node_count,
            edge_count=graph.stats.edge_count,
            file_count=graph.stats.file_count,
            symbol_count=graph.stats.symbol_count,
            dependency_edge_count=graph.stats.dependency_edge_count,
            call_edge_count=graph.stats.call_edge_count,
        ),
        persistence=KnowledgeGraphPersistenceResponse(
            persisted=persistence.persisted,
            node_count=persistence.node_count,
            edge_count=persistence.edge_count,
            backend=persistence.backend,
            durable_backend=persistence.durable_backend,
        ),
    )


def to_dependency_graph_response(graph: DependencyGraph) -> DependencyGraphResponse:
    """Convert graph-domain output into an API response."""
    return DependencyGraphResponse(
        repository_path=graph.repository_path,
        nodes=[
            DependencyNodeResponse(path=node.path, language=node.language) for node in graph.nodes
        ],
        edges=[
            DependencyEdgeResponse(
                source=edge.source,
                target=edge.target,
                import_name=edge.import_name,
                import_source=edge.import_source,
                dependency_type=edge.dependency_type,
            )
            for edge in graph.edges
        ],
        external_dependencies=list(graph.external_dependencies),
        unresolved_imports=list(graph.unresolved_imports),
        circular_dependencies=[list(cycle) for cycle in graph.circular_dependencies],
        stats=DependencyGraphStatsResponse(
            file_count=graph.stats.file_count,
            internal_dependency_count=graph.stats.internal_dependency_count,
            external_dependency_count=graph.stats.external_dependency_count,
            unresolved_dependency_count=graph.stats.unresolved_dependency_count,
            circular_dependency_count=graph.stats.circular_dependency_count,
        ),
    )


def to_parse_response(result: ParseTreeSummary) -> ParseTreeResponse:
    """Convert parser-domain output into an API response."""
    return ParseTreeResponse(
        path=result.path,
        language=result.language,
        root_node_type=result.root_node_type,
        start_byte=result.start_byte,
        end_byte=result.end_byte,
        start_point=SourcePoint(row=result.start_point.row, column=result.start_point.column),
        end_point=SourcePoint(row=result.end_point.row, column=result.end_point.column),
        has_error=result.has_error,
        named_child_count=result.named_child_count,
        symbols=[
            SourceSymbolResponse(
                kind=symbol.kind,
                name=symbol.name,
                line=symbol.line,
                column=symbol.column,
                end_line=symbol.end_line,
                end_column=symbol.end_column,
                parent=symbol.parent,
                source=symbol.source,
                exported=symbol.exported,
                inherits=list(symbol.inherits),
            )
            for symbol in result.symbols
        ],
        calls=[
            SourceCallResponse(
                caller=call.caller,
                callee=call.callee,
                line=call.line,
                column=call.column,
                end_line=call.end_line,
                end_column=call.end_column,
                recursive=call.recursive,
            )
            for call in result.calls
        ],
    )


@router.post(
    "/import", response_model=RepositoryImportResponse, status_code=status.HTTP_201_CREATED
)
def import_repository(
    request: RepositoryImportRequest,
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Import a GitHub or local Git repository."""
    try:
        if request.source_type == "github":
            return service.import_github(request.source)
        return service.import_local(request.source)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/import/zip",
    response_model=RepositoryImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_repository_zip(
    file: Annotated[UploadFile, File()],
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Import a repository from an uploaded ZIP archive."""
    try:
        content = await file.read(service.max_zip_bytes + 1)
        return service.import_zip(file.filename or "repository.zip", content)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}", response_model=RepositoryImportResponse)
def get_repository_import(
    import_id: str,
    service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
) -> RepositoryImportResponse:
    """Return progress for a repository import."""
    try:
        return service.get_progress(import_id)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/scan", response_model=RepositoryScanResult)
def scan_repository(
    request: RepositoryScanRequest,
    service: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
) -> RepositoryScanResult:
    """Recursively scan a repository path."""
    try:
        return service.scan(request.repository_path)
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/scan", response_model=RepositoryScanResult)
def scan_imported_repository(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    scanner_service: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
) -> RepositoryScanResult:
    """Recursively scan a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositoryScanError("Repository import has no local path to scan.")
        return scanner_service.scan(Path(imported_repository.repository_path))
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/metadata", response_model=StoredRepositoryMetadata, status_code=status.HTTP_201_CREATED
)
def persist_repository_metadata(
    request: MetadataPersistRequest,
    service: Annotated[MetadataService, Depends(get_metadata_service)],
) -> StoredRepositoryMetadata:
    """Persist scan metadata for a repository path."""
    try:
        return service.persist_repository(Path(request.repository_path), request.name)
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/metadata/{repository_id}", response_model=StoredRepositoryMetadata)
def get_repository_metadata(
    repository_id: int,
    service: Annotated[MetadataService, Depends(get_metadata_service)],
) -> StoredRepositoryMetadata:
    """Return stored repository metadata."""
    try:
        return service.get_repository(repository_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository metadata was not found.",
        ) from error


@router.get("/imports/{import_id}/metadata", response_model=StoredRepositoryMetadata)
def persist_imported_repository_metadata(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    metadata_service: Annotated[MetadataService, Depends(get_metadata_service)],
) -> StoredRepositoryMetadata:
    """Persist metadata for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositoryScanError("Repository import has no local path to persist.")
        return metadata_service.persist_repository(Path(imported_repository.repository_path))
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except RepositoryScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/parse-file", response_model=ParseTreeResponse)
def parse_repository_file(
    request: ParseFileRequest,
    parser_service: Annotated[TreeSitterParserService, Depends(get_tree_sitter_parser_service)],
) -> ParseTreeResponse:
    """Parse one supported source file with Tree-sitter."""
    try:
        return to_parse_response(parser_service.parse_file(request.path))
    except TreeSitterParseError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/parse-import/{import_id}", response_model=ParseRepositoryResponse)
def parse_imported_repository(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    scanner_service: Annotated[RepositoryScannerService, Depends(get_repository_scanner_service)],
    parser_service: Annotated[TreeSitterParserService, Depends(get_tree_sitter_parser_service)],
) -> ParseRepositoryResponse:
    """Parse supported files in a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise TreeSitterParseError("Repository import has no local path to parse.")
        repository_path = Path(imported_repository.repository_path)
        scan = scanner_service.scan(repository_path)
        parsed_files = [
            to_parse_response(parser_service.parse_file(repository_path / file.path))
            for file in scan.files
            if parser_service.supports_path(Path(file.path))
        ]
        return ParseRepositoryResponse(
            repository_path=str(repository_path),
            parsed_files=parsed_files,
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, TreeSitterParseError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/dependency-graph", response_model=DependencyGraphResponse)
def build_dependency_graph(
    request: DependencyGraphRequest,
    service: Annotated[DependencyGraphService, Depends(get_dependency_graph_service)],
) -> DependencyGraphResponse:
    """Build a file-level dependency graph for a repository path."""
    try:
        return to_dependency_graph_response(service.build(request.repository_path))
    except (RepositoryScanError, DependencyGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/chunks", response_model=RepositoryChunksResponse)
def chunk_repository(
    request: RepositoryChunkRequest,
    service: Annotated[RepositoryChunkerService, Depends(get_repository_chunker_service)],
) -> RepositoryChunksResponse:
    """Chunk supported repository source files for later embedding generation."""
    try:
        return to_repository_chunks_response(service.chunk_repository(request.repository_path))
    except (RepositoryScanError, RepositoryChunkError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/chunks", response_model=RepositoryChunksResponse)
def chunk_imported_repository(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[RepositoryChunkerService, Depends(get_repository_chunker_service)],
) -> RepositoryChunksResponse:
    """Chunk a previously imported repository for later embedding generation."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositoryChunkError("Repository import has no local path to chunk.")
        return to_repository_chunks_response(
            service.chunk_repository(Path(imported_repository.repository_path))
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositoryChunkError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/embeddings", response_model=RepositoryEmbeddingsResponse)
def generate_repository_embeddings(
    request: RepositoryEmbeddingRequest,
    service: Annotated[EmbeddingService, Depends(get_embedding_service)],
) -> RepositoryEmbeddingsResponse:
    """Generate embeddings for repository chunks."""
    try:
        return to_repository_embeddings_response(service.embed_repository(request.repository_path))
    except (RepositoryScanError, RepositoryChunkError, EmbeddingError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/embeddings", response_model=RepositoryEmbeddingsResponse)
def generate_imported_repository_embeddings(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[EmbeddingService, Depends(get_embedding_service)],
) -> RepositoryEmbeddingsResponse:
    """Generate embeddings for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise EmbeddingError("Repository import has no local path to embed.")
        return to_repository_embeddings_response(
            service.embed_repository(Path(imported_repository.repository_path))
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositoryChunkError, EmbeddingError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/vector-store", response_model=VectorStoreResponse)
def store_repository_vectors(
    request: VectorStoreRequest,
    service: Annotated[VectorStoreService, Depends(get_vector_store_service)],
) -> VectorStoreResponse:
    """Generate and store repository embedding vectors."""
    try:
        return to_vector_store_response(service.index_repository(request.repository_path))
    except (RepositoryScanError, RepositoryChunkError, EmbeddingError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/vector-store", response_model=VectorStoreResponse)
def store_imported_repository_vectors(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[VectorStoreService, Depends(get_vector_store_service)],
) -> VectorStoreResponse:
    """Generate and store vectors for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise EmbeddingError("Repository import has no local path to index.")
        return to_vector_store_response(
            service.index_repository(Path(imported_repository.repository_path))
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositoryChunkError, EmbeddingError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/retrieve", response_model=HybridRetrievalResponse)
def retrieve_repository_context(
    request: HybridRetrievalRequest,
    service: Annotated[HybridRetrievalService, Depends(get_hybrid_retrieval_service)],
) -> HybridRetrievalResponse:
    """Retrieve relevant repository chunks using vector, keyword, and graph signals."""
    try:
        return to_hybrid_retrieval_response(
            service.retrieve(
                repository_path=request.repository_path,
                query=request.query,
                limit=request.limit,
            )
        )
    except (EmbeddingError, RetrievalError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/imports/{import_id}/retrieve", response_model=HybridRetrievalResponse)
def retrieve_imported_repository_context(
    import_id: str,
    request: ImportedHybridRetrievalRequest,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[HybridRetrievalService, Depends(get_hybrid_retrieval_service)],
) -> HybridRetrievalResponse:
    """Retrieve relevant chunks for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RetrievalError("Repository import has no local path to retrieve.")
        return to_hybrid_retrieval_response(
            service.retrieve(
                repository_path=Path(imported_repository.repository_path),
                query=request.query,
                limit=request.limit,
            )
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (EmbeddingError, RetrievalError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/summary", response_model=RepositorySummaryResponse)
def summarize_repository(
    request: RepositorySummaryRequest,
    service: Annotated[RepositorySummaryService, Depends(get_repository_summary_service)],
) -> RepositorySummaryResponse:
    """Summarize a repository from parsed code intelligence and graph context."""
    try:
        return to_repository_summary_response(service.summarize(request.repository_path))
    except (RepositoryScanError, RepositorySummaryError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/summary", response_model=RepositorySummaryResponse)
def summarize_imported_repository(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[RepositorySummaryService, Depends(get_repository_summary_service)],
) -> RepositorySummaryResponse:
    """Summarize a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositorySummaryError("Repository import has no local path to summarize.")
        return to_repository_summary_response(
            service.summarize(Path(imported_repository.repository_path))
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositorySummaryError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/architecture-explanation", response_model=ArchitectureExplanationResponse)
def explain_repository_architecture(
    request: ArchitectureExplanationRequest,
    service: Annotated[
        ArchitectureExplanationService, Depends(get_architecture_explanation_service)
    ],
) -> ArchitectureExplanationResponse:
    """Explain repository architecture using grounded repository evidence."""
    try:
        return to_architecture_explanation_response(
            service.explain(repository_path=request.repository_path, focus=request.focus)
        )
    except (RepositoryScanError, RepositorySummaryError, ArchitectureExplanationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post(
    "/imports/{import_id}/architecture-explanation",
    response_model=ArchitectureExplanationResponse,
)
def explain_imported_repository_architecture(
    import_id: str,
    request: ImportedArchitectureExplanationRequest,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[
        ArchitectureExplanationService, Depends(get_architecture_explanation_service)
    ],
) -> ArchitectureExplanationResponse:
    """Explain architecture for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise ArchitectureExplanationError("Repository import has no local path to explain.")
        return to_architecture_explanation_response(
            service.explain(
                repository_path=Path(imported_repository.repository_path),
                focus=request.focus,
            )
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositorySummaryError, ArchitectureExplanationError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/question", response_model=RepositoryQAResponse)
def answer_repository_question(
    request: RepositoryQARequest,
    service: Annotated[RepositoryQAService, Depends(get_repository_qa_service)],
) -> RepositoryQAResponse:
    """Answer a repository question using grounded repository context."""
    try:
        return to_repository_qa_response(
            service.answer(
                repository_path=request.repository_path,
                question=request.question,
                limit=request.limit,
            )
        )
    except (RepositoryScanError, RepositorySummaryError, RepositoryQAError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/imports/{import_id}/question", response_model=RepositoryQAResponse)
def answer_imported_repository_question(
    import_id: str,
    request: ImportedRepositoryQARequest,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[RepositoryQAService, Depends(get_repository_qa_service)],
) -> RepositoryQAResponse:
    """Answer a repository question for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise RepositoryQAError("Repository import has no local path to answer from.")
        return to_repository_qa_response(
            service.answer(
                repository_path=Path(imported_repository.repository_path),
                question=request.question,
                limit=request.limit,
            )
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, RepositorySummaryError, RepositoryQAError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/call-graph", response_model=CallGraphResponse)
def build_call_graph(
    request: CallGraphRequest,
    service: Annotated[CallGraphService, Depends(get_call_graph_service)],
) -> CallGraphResponse:
    """Build a function-level call graph for a repository path."""
    try:
        return to_call_graph_response(service.build(request.repository_path))
    except (RepositoryScanError, CallGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/call-graph", response_model=CallGraphResponse)
def build_imported_repository_call_graph(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[CallGraphService, Depends(get_call_graph_service)],
) -> CallGraphResponse:
    """Build a call graph for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise CallGraphError("Repository import has no local path to graph.")
        return to_call_graph_response(service.build(Path(imported_repository.repository_path)))
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, CallGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/knowledge-graph", response_model=KnowledgeGraphResponse)
def build_knowledge_graph(
    request: KnowledgeGraphRequest,
    service: Annotated[KnowledgeGraphService, Depends(get_knowledge_graph_service)],
) -> KnowledgeGraphResponse:
    """Build and persist a repository knowledge graph in Neo4j."""
    try:
        graph, persistence = service.build_and_persist(request.repository_path)
        return to_knowledge_graph_response(graph, persistence)
    except (RepositoryScanError, KnowledgeGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/knowledge-graph", response_model=KnowledgeGraphResponse)
def build_imported_repository_knowledge_graph(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[KnowledgeGraphService, Depends(get_knowledge_graph_service)],
) -> KnowledgeGraphResponse:
    """Build and persist a knowledge graph for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise KnowledgeGraphError("Repository import has no local path to graph.")
        graph, persistence = service.build_and_persist(Path(imported_repository.repository_path))
        return to_knowledge_graph_response(graph, persistence)
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, KnowledgeGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/imports/{import_id}/dependency-graph", response_model=DependencyGraphResponse)
def build_imported_repository_dependency_graph(
    import_id: str,
    import_service: Annotated[RepositoryImportService, Depends(get_repository_import_service)],
    service: Annotated[DependencyGraphService, Depends(get_dependency_graph_service)],
) -> DependencyGraphResponse:
    """Build a dependency graph for a previously imported repository."""
    try:
        imported_repository = import_service.get_progress(import_id)
        if imported_repository.repository_path is None:
            raise DependencyGraphError("Repository import has no local path to graph.")
        return to_dependency_graph_response(
            service.build(Path(imported_repository.repository_path))
        )
    except RepositoryImportError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except (RepositoryScanError, DependencyGraphError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
