import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path

from graph.dependency_graph import DependencyGraphError, DependencyGraphService

from backend.app.repositories.vector_store import VectorStoreRepository
from backend.app.services.embedding import EmbeddingClient, EmbeddingError
from backend.app.services.repository_scanner import RepositoryScanError

VECTOR_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.3
GRAPH_WEIGHT = 0.1
DEFAULT_RETRIEVAL_LIMIT = 10
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")

logger = logging.getLogger(__name__)


class RetrievalError(Exception):
    """Raised when hybrid retrieval cannot continue."""


@dataclass(frozen=True)
class HybridRetrievalResult:
    """One ranked retrieval result."""

    chunk_id: str
    path: str
    kind: str
    language: str
    start_line: int
    end_line: int
    content: str
    score: float
    vector_score: float
    keyword_score: float
    graph_score: float
    related_paths: tuple[str, ...]
    symbol_kind: str | None = None
    symbol_name: str | None = None
    symbol_parent: str | None = None


@dataclass(frozen=True)
class HybridRetrievalStats:
    """Summary counts for a hybrid retrieval query."""

    result_count: int
    searched_embedding_count: int
    dimensions: int


@dataclass(frozen=True)
class HybridRetrieval:
    """Hybrid retrieval response domain object."""

    repository_path: str
    query: str
    model: str
    results: tuple[HybridRetrievalResult, ...]
    stats: HybridRetrievalStats


@dataclass(frozen=True)
class _Candidate:
    chunk_id: str
    path: str
    kind: str
    language: str
    start_line: int
    end_line: int
    content: str
    vector_score: float
    keyword_score: float
    symbol_kind: str | None
    symbol_name: str | None
    symbol_parent: str | None


class HybridRetrievalService:
    """Ranks stored repository chunks using vector, keyword, and graph signals."""

    def __init__(
        self,
        repository: VectorStoreRepository,
        embedding_client: EmbeddingClient | None,
        dependency_graph: DependencyGraphService,
        model: str,
    ) -> None:
        self.repository = repository
        self.embedding_client = embedding_client
        self.dependency_graph = dependency_graph
        self.model = model

    def retrieve(
        self,
        repository_path: Path,
        query: str,
        limit: int = DEFAULT_RETRIEVAL_LIMIT,
    ) -> HybridRetrieval:
        normalized_query = query.strip()
        if not normalized_query:
            raise RetrievalError("Retrieval query cannot be empty.")
        if limit <= 0:
            raise RetrievalError("Retrieval limit must be positive.")
        if self.embedding_client is None:
            raise RetrievalError("Embedding client is not configured.")

        root = repository_path.expanduser().resolve()
        stored_embeddings = self.repository.list_repository(str(root))
        if not stored_embeddings:
            raise RetrievalError("No vectors have been stored for this repository.")

        try:
            query_vectors = self.embedding_client.create_embeddings(
                model=self.model,
                inputs=[normalized_query],
            )
        except EmbeddingError:
            raise
        except Exception as error:
            logger.exception("Embedding query generation failed.")
            raise RetrievalError(str(error)) from error

        if len(query_vectors) != 1:
            raise RetrievalError("Embedding response count did not match query count.")
        query_vector = tuple(float(value) for value in query_vectors[0])
        query_tokens = self._tokens(normalized_query)

        candidates = tuple(
            _Candidate(
                chunk_id=embedding.chunk_id,
                path=embedding.path,
                kind=embedding.kind,
                language=embedding.language,
                start_line=embedding.start_line,
                end_line=embedding.end_line,
                content=embedding.content,
                vector_score=self._normalized_cosine(query_vector, embedding.embedding),
                keyword_score=self._keyword_score(
                    query_tokens=query_tokens,
                    text=" ".join(
                        value
                        for value in (
                            embedding.path,
                            embedding.symbol_name,
                            embedding.symbol_kind,
                            embedding.content,
                        )
                        if value is not None
                    ),
                ),
                symbol_kind=embedding.symbol_kind,
                symbol_name=embedding.symbol_name,
                symbol_parent=embedding.symbol_parent,
            )
            for embedding in stored_embeddings
        )
        related_by_path = self._related_paths(root)
        seed_paths = self._seed_paths(candidates)
        results = tuple(
            sorted(
                (
                    self._result_for_candidate(candidate, related_by_path, seed_paths)
                    for candidate in candidates
                ),
                key=lambda result: (-result.score, result.path, result.start_line),
            )[:limit]
        )
        dimensions = len(stored_embeddings[0].embedding)
        return HybridRetrieval(
            repository_path=str(root),
            query=normalized_query,
            model=self.model,
            results=results,
            stats=HybridRetrievalStats(
                result_count=len(results),
                searched_embedding_count=len(stored_embeddings),
                dimensions=dimensions,
            ),
        )

    def _result_for_candidate(
        self,
        candidate: _Candidate,
        related_by_path: dict[str, set[str]],
        seed_paths: set[str],
    ) -> HybridRetrievalResult:
        related_paths = tuple(sorted(related_by_path.get(candidate.path, set())))
        graph_score = self._graph_score(candidate.path, related_paths, seed_paths)
        score = (
            (candidate.vector_score * VECTOR_WEIGHT)
            + (candidate.keyword_score * KEYWORD_WEIGHT)
            + (graph_score * GRAPH_WEIGHT)
        )
        return HybridRetrievalResult(
            chunk_id=candidate.chunk_id,
            path=candidate.path,
            kind=candidate.kind,
            language=candidate.language,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
            content=candidate.content,
            score=score,
            vector_score=candidate.vector_score,
            keyword_score=candidate.keyword_score,
            graph_score=graph_score,
            related_paths=related_paths[:5],
            symbol_kind=candidate.symbol_kind,
            symbol_name=candidate.symbol_name,
            symbol_parent=candidate.symbol_parent,
        )

    def _related_paths(self, repository_path: Path) -> dict[str, set[str]]:
        try:
            graph = self.dependency_graph.build(repository_path)
        except (RepositoryScanError, DependencyGraphError) as error:
            logger.warning("Dependency graph unavailable for retrieval: %s", error)
            return {}

        related_by_path: dict[str, set[str]] = {}
        for edge in graph.edges:
            if edge.target is None:
                continue
            related_by_path.setdefault(edge.source, set()).add(edge.target)
            related_by_path.setdefault(edge.target, set()).add(edge.source)
        return related_by_path

    def _seed_paths(self, candidates: tuple[_Candidate, ...]) -> set[str]:
        keyword_paths = {candidate.path for candidate in candidates if candidate.keyword_score > 0}
        if keyword_paths:
            return keyword_paths
        top_vector_score = max(candidate.vector_score for candidate in candidates)
        return {
            candidate.path
            for candidate in candidates
            if math.isclose(candidate.vector_score, top_vector_score)
        }

    def _graph_score(
        self,
        path: str,
        related_paths: tuple[str, ...],
        seed_paths: set[str],
    ) -> float:
        if path in seed_paths:
            return 1.0
        if seed_paths.intersection(related_paths):
            return 0.5
        return 0.0

    def _keyword_score(self, query_tokens: set[str], text: str) -> float:
        if not query_tokens:
            return 0.0
        text_tokens = self._tokens(text)
        return len(query_tokens.intersection(text_tokens)) / len(query_tokens)

    def _tokens(self, text: str) -> set[str]:
        return set(TOKEN_PATTERN.findall(text.lower()))

    def _normalized_cosine(
        self,
        left: tuple[float, ...],
        right: tuple[float, ...],
    ) -> float:
        if len(left) != len(right):
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        cosine = sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
        return max(0.0, min(1.0, (cosine + 1.0) / 2.0))
