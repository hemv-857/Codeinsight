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
        "frontend/components/dashboard.tsx",
        "frontend/components/providers.tsx",
        "frontend/tailwind.config.ts",
    ]

    missing_paths = [path for path in required_paths if not (ROOT / path).is_file()]

    assert missing_paths == []
