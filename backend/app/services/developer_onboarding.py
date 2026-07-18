from dataclasses import dataclass
from pathlib import Path

from backend.app.services.architecture_docs import (
    ArchitectureDocsError,
    ArchitectureDocsService,
    GeneratedArchitectureDoc,
)
from backend.app.services.architecture_explanation import ArchitectureExplanationError
from backend.app.services.mermaid_diagrams import (
    MermaidDiagram,
    MermaidDiagramError,
    MermaidDiagramService,
)
from backend.app.services.readme_generator import (
    GeneratedReadme,
    ReadmeGeneratorError,
    ReadmeGeneratorService,
)
from backend.app.services.repository_summary import RepositorySummaryError

MAX_SECTION_ITEMS = 8


class DeveloperOnboardingError(Exception):
    """Raised when developer onboarding documentation cannot continue."""


@dataclass(frozen=True)
class DeveloperOnboardingSection:
    """One generated developer onboarding section."""

    heading: str
    content: str


@dataclass(frozen=True)
class DeveloperOnboardingStats:
    """Generated developer onboarding documentation statistics."""

    section_count: int
    word_count: int
    evidence_path_count: int
    diagram_count: int
    confidence: float


@dataclass(frozen=True)
class GeneratedDeveloperOnboarding:
    """Developer onboarding guide generated from repository intelligence."""

    repository_path: str
    title: str
    focus: str | None
    markdown: str
    sections: tuple[DeveloperOnboardingSection, ...]
    evidence_paths: tuple[str, ...]
    stats: DeveloperOnboardingStats


class DeveloperOnboardingService:
    """Generates a practical onboarding guide from existing repository documentation."""

    def __init__(
        self,
        readme_generator: ReadmeGeneratorService,
        architecture_docs: ArchitectureDocsService,
        mermaid_diagrams: MermaidDiagramService,
    ) -> None:
        self.readme_generator = readme_generator
        self.architecture_docs = architecture_docs
        self.mermaid_diagrams = mermaid_diagrams

    def generate(
        self,
        repository_path: Path,
        focus: str | None = None,
    ) -> GeneratedDeveloperOnboarding:
        """Generate a developer onboarding guide for a repository path."""
        try:
            readme = self.readme_generator.generate(repository_path)
            architecture = self.architecture_docs.generate(repository_path, focus=focus)
            diagrams = self.mermaid_diagrams.generate(repository_path, focus=focus)
        except (
            ReadmeGeneratorError,
            RepositorySummaryError,
            ArchitectureExplanationError,
            ArchitectureDocsError,
            MermaidDiagramError,
        ) as error:
            raise DeveloperOnboardingError(str(error)) from error

        title = self._title(Path(readme.repository_path), architecture.focus)
        evidence_paths = tuple(
            dict.fromkeys(list(readme.evidence_paths) + list(architecture.evidence_paths))
        )[:MAX_SECTION_ITEMS]
        sections = (
            DeveloperOnboardingSection("Repository Snapshot", self._snapshot(readme.markdown)),
            DeveloperOnboardingSection("Local Setup", self._section(readme, "Getting Started")),
            DeveloperOnboardingSection("First Files To Read", self._section(readme, "Key Files")),
            DeveloperOnboardingSection(
                "Architecture Map", self._section(architecture, "Core Components")
            ),
            DeveloperOnboardingSection("Development Workflow", self._workflow()),
            DeveloperOnboardingSection("Validation Checklist", self._checklist()),
            DeveloperOnboardingSection("Useful Diagrams", self._diagrams(diagrams.diagrams)),
            DeveloperOnboardingSection("Follow-Up Questions", self._questions(architecture.focus)),
        )
        markdown = self._markdown(title, sections)
        return GeneratedDeveloperOnboarding(
            repository_path=readme.repository_path,
            title=title,
            focus=architecture.focus,
            markdown=markdown,
            sections=sections,
            evidence_paths=evidence_paths,
            stats=DeveloperOnboardingStats(
                section_count=len(sections),
                word_count=len(markdown.split()),
                evidence_path_count=len(evidence_paths),
                diagram_count=diagrams.stats.diagram_count,
                confidence=architecture.stats.confidence,
            ),
        )

    def _title(self, root: Path, focus: str | None) -> str:
        name = root.name or "Repository"
        return f"{name} Developer Onboarding: {focus}" if focus else f"{name} Developer Onboarding"

    def _snapshot(self, markdown: str) -> str:
        return self._between(markdown, "Overview", "Repository Stats")

    def _section(self, document: GeneratedReadme | GeneratedArchitectureDoc, heading: str) -> str:
        for section in document.sections:
            if section.heading == heading:
                return section.content
        return f"No {heading.lower()} section was generated."

    def _workflow(self) -> str:
        return "\n".join(
            [
                "1. Import or scan the repository in CodeInsight.",
                "2. Review the repository snapshot and key files before changing code.",
                "3. Inspect dependency and call-flow diagrams for the area you plan to edit.",
                "4. Run the project-specific setup and validation commands from this guide.",
                "5. Use repository Q&A and search for focused follow-up investigation.",
            ]
        )

    def _checklist(self) -> str:
        return "\n".join(
            [
                "- Confirm dependencies install successfully.",
                "- Run the repository's tests or closest available validation command.",
                "- Check impacted files in dependency and call graphs before large edits.",
                "- Re-run CodeInsight search, technical debt, and bug impact tools after changes.",
                "- Update generated docs when architecture or onboarding flow changes.",
            ]
        )

    def _diagrams(self, diagrams: tuple[MermaidDiagram, ...]) -> str:
        blocks: list[str] = []
        for diagram in diagrams[:3]:
            blocks.append(f"### {diagram.title}\n\n```mermaid\n{diagram.code}\n```")
        return "\n\n".join(blocks) if blocks else "No Mermaid diagrams were generated."

    def _questions(self, focus: str | None) -> str:
        focused = focus or "the feature you plan to change"
        return "\n".join(
            [
                f"- How does {focused} work end to end?",
                f"- What breaks if I modify {focused}?",
                "- Which files have the highest architecture risk?",
                "- Which dependency paths should I inspect before implementation?",
            ]
        )

    def _between(self, markdown: str, heading: str, next_heading: str) -> str:
        start_marker = f"## {heading}"
        next_marker = f"## {next_heading}"
        start = markdown.find(start_marker)
        end = markdown.find(next_marker)
        if start == -1:
            return "No repository overview was generated."
        content_start = start + len(start_marker)
        content_end = end if end != -1 else len(markdown)
        return markdown[content_start:content_end].strip()

    def _markdown(
        self,
        title: str,
        sections: tuple[DeveloperOnboardingSection, ...],
    ) -> str:
        body = "\n\n".join(
            f"## {section.heading}\n\n{section.content.strip()}" for section in sections
        )
        return f"# {title}\n\n{body}\n"
