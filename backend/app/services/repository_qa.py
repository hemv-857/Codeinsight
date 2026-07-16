import re
from dataclasses import dataclass
from pathlib import Path

from backend.app.services.architecture_explanation import ArchitectureExplanationService
from backend.app.services.repository_summary import (
    RepositorySummary,
    RepositorySummaryError,
    RepositorySummaryService,
)
from backend.app.services.retrieval import (
    HybridRetrievalResult,
    HybridRetrievalService,
    RetrievalError,
)

DEFAULT_QA_LIMIT = 5
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


class RepositoryQAError(Exception):
    """Raised when repository Q&A cannot continue."""


@dataclass(frozen=True)
class RepositoryQASnippet:
    """Retrieved source snippet supporting an answer."""

    path: str
    start_line: int
    end_line: int
    content: str
    score: float


@dataclass(frozen=True)
class RepositoryQAAnswer:
    """Grounded repository Q&A answer."""

    repository_path: str
    question: str
    answer: str
    mode: str
    confidence: float
    supporting_files: tuple[str, ...]
    supporting_symbols: tuple[str, ...]
    snippets: tuple[RepositoryQASnippet, ...]


class RepositoryQAService:
    """Answers repository questions from summaries, architecture context, and retrieval."""

    def __init__(
        self,
        summary_service: RepositorySummaryService,
        architecture_service: ArchitectureExplanationService,
        retrieval_service: HybridRetrievalService,
    ) -> None:
        self.summary_service = summary_service
        self.architecture_service = architecture_service
        self.retrieval_service = retrieval_service

    def answer(
        self,
        repository_path: Path,
        question: str,
        limit: int = DEFAULT_QA_LIMIT,
    ) -> RepositoryQAAnswer:
        normalized_question = question.strip()
        if not normalized_question:
            raise RepositoryQAError("Question cannot be empty.")
        if limit <= 0:
            raise RepositoryQAError("Question result limit must be positive.")

        try:
            summary = self.summary_service.summarize(repository_path)
        except RepositorySummaryError:
            raise
        except Exception as error:
            raise RepositoryQAError(str(error)) from error

        snippets = self._retrieval_snippets(repository_path, normalized_question, limit)
        question_tokens = self._tokens(normalized_question)
        if self._is_architecture_question(question_tokens):
            explanation = self.architecture_service.explain(
                repository_path=repository_path,
                focus=normalized_question,
            )
            supporting_files = tuple(
                dict.fromkeys(
                    list(explanation.evidence_paths) + [snippet.path for snippet in snippets]
                )
            )[:limit]
            return RepositoryQAAnswer(
                repository_path=summary.repository_path,
                question=normalized_question,
                answer=" ".join(
                    [
                        explanation.overview,
                        *explanation.dependency_flow,
                        *explanation.call_flow,
                    ]
                ),
                mode="architecture",
                confidence=explanation.confidence,
                supporting_files=supporting_files,
                supporting_symbols=self._supporting_symbols(summary, question_tokens, limit),
                snippets=snippets,
            )

        supporting_files = tuple(
            dict.fromkeys(
                [file.path for file in summary.key_files] + [snippet.path for snippet in snippets]
            )
        )[:limit]
        return RepositoryQAAnswer(
            repository_path=summary.repository_path,
            question=normalized_question,
            answer=self._summary_answer(summary.overview, snippets),
            mode="retrieval" if snippets else "summary",
            confidence=0.78 if snippets else 0.68,
            supporting_files=supporting_files,
            supporting_symbols=self._supporting_symbols(summary, question_tokens, limit),
            snippets=snippets,
        )

    def _retrieval_snippets(
        self,
        repository_path: Path,
        question: str,
        limit: int,
    ) -> tuple[RepositoryQASnippet, ...]:
        try:
            retrieval = self.retrieval_service.retrieve(repository_path, question, limit=limit)
        except RetrievalError:
            return ()
        return tuple(self._snippet(result) for result in retrieval.results)

    def _snippet(self, result: HybridRetrievalResult) -> RepositoryQASnippet:
        return RepositoryQASnippet(
            path=result.path,
            start_line=result.start_line,
            end_line=result.end_line,
            content=result.content,
            score=result.score,
        )

    def _summary_answer(
        self,
        overview: str,
        snippets: tuple[RepositoryQASnippet, ...],
    ) -> str:
        if snippets:
            files = ", ".join(dict.fromkeys(snippet.path for snippet in snippets))
            return f"{overview} The most relevant indexed evidence is in {files}."
        return f"{overview} No semantic index evidence was available for this question."

    def _supporting_symbols(
        self,
        summary: RepositorySummary,
        question_tokens: set[str],
        limit: int,
    ) -> tuple[str, ...]:
        focused = [
            f"{symbol.name} ({symbol.kind})"
            for symbol in summary.key_symbols
            if question_tokens.intersection(self._tokens(f"{symbol.name} {symbol.path}"))
        ]
        fallback = [f"{symbol.name} ({symbol.kind})" for symbol in summary.key_symbols]
        return tuple(dict.fromkeys(focused or fallback))[:limit]

    def _is_architecture_question(self, question_tokens: set[str]) -> bool:
        return bool(
            question_tokens.intersection(
                {
                    "architecture",
                    "architectural",
                    "flow",
                    "flows",
                    "depend",
                    "depends",
                    "dependency",
                    "dependencies",
                    "how",
                }
            )
        )

    def _tokens(self, text: str) -> set[str]:
        return set(TOKEN_PATTERN.findall(text.lower()))
