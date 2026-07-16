import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_workspace_has_required_dependencies() -> None:
    package_json = json.loads((ROOT / "frontend" / "package.json").read_text())

    dependencies = package_json["dependencies"]

    for package_name in [
        "@tanstack/react-query",
        "@xyflow/react",
        "framer-motion",
        "next",
        "react",
        "react-dom",
    ]:
        assert package_name in dependencies


def test_frontend_dashboard_files_exist() -> None:
    required_paths = [
        "frontend/app/layout.tsx",
        "frontend/app/page.tsx",
        "frontend/app/globals.css",
        "frontend/components/architecture-docs-panel.tsx",
        "frontend/components/architecture-violations-panel.tsx",
        "frontend/components/bug-impact-panel.tsx",
        "frontend/components/dashboard.tsx",
        "frontend/components/circular-dependencies-panel.tsx",
        "frontend/components/dead-code-panel.tsx",
        "frontend/components/dependency-graph-panel.tsx",
        "frontend/components/graph-control-toggle.tsx",
        "frontend/components/knowledge-graph-panel.tsx",
        "frontend/components/mermaid-diagrams-panel.tsx",
        "frontend/components/providers.tsx",
        "frontend/components/readme-generator-panel.tsx",
        "frontend/components/repository-explorer.tsx",
        "frontend/components/repository-search-panel.tsx",
        "frontend/components/stack-trace-panel.tsx",
        "frontend/components/technical-debt-panel.tsx",
        "frontend/tailwind.config.ts",
    ]

    missing_paths = [path for path in required_paths if not (ROOT / path).is_file()]

    assert missing_paths == []


def test_frontend_repository_explorer_uses_scan_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    explorer_source = (ROOT / "frontend" / "components" / "repository-explorer.tsx").read_text()

    assert "/api/repositories/scan" in api_source
    assert "/api/repositories/imports/" in api_source
    assert "scanRepository" in explorer_source
    assert "scanImportedRepository" in explorer_source


def test_frontend_dependency_graph_uses_dependency_graph_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    graph_source = (ROOT / "frontend" / "components" / "dependency-graph-panel.tsx").read_text()

    assert "/api/repositories/dependency-graph" in api_source
    assert "/dependency-graph" in api_source
    assert "buildDependencyGraph" in graph_source
    assert "buildImportedDependencyGraph" in graph_source
    assert "ReactFlow" in graph_source
    assert "MiniMap" in graph_source
    assert "GraphControlToggle" in graph_source


def test_frontend_repository_search_uses_retrieval_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    search_source = (ROOT / "frontend" / "components" / "repository-search-panel.tsx").read_text()

    assert "/api/repositories/vector-store" in api_source
    assert "/api/repositories/retrieve" in api_source
    assert "/retrieve" in api_source
    assert "indexRepositoryVectors" in search_source
    assert "indexImportedRepositoryVectors" in search_source
    assert "searchRepository" in search_source
    assert "searchImportedRepository" in search_source


def test_frontend_technical_debt_uses_technical_debt_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    debt_source = (ROOT / "frontend" / "components" / "technical-debt-panel.tsx").read_text()

    assert "/api/repositories/technical-debt" in api_source
    assert "/technical-debt" in api_source
    assert "analyzeTechnicalDebt" in debt_source
    assert "analyzeImportedTechnicalDebt" in debt_source


def test_frontend_circular_dependencies_uses_cycle_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    cycle_source = (
        ROOT / "frontend" / "components" / "circular-dependencies-panel.tsx"
    ).read_text()

    assert "/api/repositories/circular-dependencies" in api_source
    assert "/circular-dependencies" in api_source
    assert "detectCircularDependencies" in cycle_source
    assert "detectImportedCircularDependencies" in cycle_source


def test_frontend_dead_code_uses_dead_code_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    dead_code_source = (ROOT / "frontend" / "components" / "dead-code-panel.tsx").read_text()

    assert "/api/repositories/dead-code" in api_source
    assert "/dead-code" in api_source
    assert "detectDeadCode" in dead_code_source
    assert "detectImportedDeadCode" in dead_code_source


def test_frontend_architecture_violations_uses_violation_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    violation_source = (
        ROOT / "frontend" / "components" / "architecture-violations-panel.tsx"
    ).read_text()

    assert "/api/repositories/architecture-violations" in api_source
    assert "/architecture-violations" in api_source
    assert "detectArchitectureViolations" in violation_source
    assert "detectImportedArchitectureViolations" in violation_source


def test_frontend_stack_trace_parser_uses_stack_trace_api() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    parser_source = (ROOT / "frontend" / "components" / "stack-trace-panel.tsx").read_text()

    assert "/api/repositories/stack-trace/parse" in api_source
    assert "parseStackTrace" in parser_source
    assert "StackTracePanel" in parser_source


def test_frontend_bug_impact_uses_bug_impact_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    impact_source = (ROOT / "frontend" / "components" / "bug-impact-panel.tsx").read_text()

    assert "/api/repositories/bug-impact" in api_source
    assert "/bug-impact" in api_source
    assert "predictBugImpact" in impact_source
    assert "predictImportedBugImpact" in impact_source


def test_frontend_readme_generator_uses_readme_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    readme_source = (ROOT / "frontend" / "components" / "readme-generator-panel.tsx").read_text()

    assert "/api/repositories/readme" in api_source
    assert "/readme" in api_source
    assert "generateReadme" in readme_source
    assert "generateImportedReadme" in readme_source
    assert "ReadmeGeneratorPanel" in readme_source


def test_frontend_architecture_docs_uses_architecture_docs_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    docs_source = (ROOT / "frontend" / "components" / "architecture-docs-panel.tsx").read_text()

    assert "/api/repositories/architecture-docs" in api_source
    assert "/architecture-docs" in api_source
    assert "generateArchitectureDocs" in docs_source
    assert "generateImportedArchitectureDocs" in docs_source
    assert "ArchitectureDocsPanel" in docs_source


def test_frontend_mermaid_diagrams_uses_mermaid_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    diagram_source = (ROOT / "frontend" / "components" / "mermaid-diagrams-panel.tsx").read_text()

    assert "/api/repositories/mermaid-diagrams" in api_source
    assert "/mermaid-diagrams" in api_source
    assert "generateMermaidDiagrams" in diagram_source
    assert "generateImportedMermaidDiagrams" in diagram_source
    assert "MermaidDiagramsPanel" in diagram_source


def test_frontend_knowledge_graph_uses_knowledge_graph_apis() -> None:
    api_source = (ROOT / "frontend" / "lib" / "api.ts").read_text()
    graph_source = (ROOT / "frontend" / "components" / "knowledge-graph-panel.tsx").read_text()

    assert "/api/repositories/knowledge-graph" in api_source
    assert "/knowledge-graph" in api_source
    assert "buildKnowledgeGraph" in graph_source
    assert "buildImportedKnowledgeGraph" in graph_source
    assert "ReactFlow" in graph_source
    assert "MiniMap" in graph_source
    assert "GraphControlToggle" in graph_source
