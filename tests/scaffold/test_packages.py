"""Framework boundaries: no side effects on import or factory call."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PACKAGE_ROOTS = {
    "qa_contracts": ROOT / "Contracts" / "src" / "qa_contracts",
    "qa_assistant": ROOT / "Q&A_Assistant" / "src" / "qa_assistant",
    "kb_management": ROOT / "KBManagement" / "src" / "kb_management",
    "qa_infrastructure": ROOT / "Infrastructure" / "src" / "qa_infrastructure",
    "qa_service": ROOT / "ServiceAPI" / "src" / "qa_service",
    "qa_client": ROOT / "Clients" / "python" / "src" / "qa_client",
    "qa_cli": ROOT / "Clients" / "cli" / "src" / "qa_cli",
}

#: Domain packages must not reach for transport, storage or UI layers.
FORBIDDEN_IMPORTS = {
    "qa_contracts": {"fastapi", "uvicorn", "sqlite3", "qa_service", "qa_infrastructure"},
    "qa_assistant": {"fastapi", "uvicorn", "sqlite3", "qa_service", "qa_infrastructure"},
    "kb_management": {"fastapi", "uvicorn", "qa_service"},
    "qa_client": {"qa_service", "qa_infrastructure", "qa_assistant", "kb_management"},
    "qa_cli": {"qa_service", "qa_infrastructure"},
}


def _python_files(package: str) -> list[Path]:
    return sorted(PACKAGE_ROOTS[package].rglob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
            elif node.level and node.module:
                found.add(node.module.split(".")[0])
    return found


@pytest.mark.parametrize("package", sorted(PACKAGE_ROOTS))
def test_package_exists(package: str) -> None:
    assert _python_files(package), f"{package} has no modules"


@pytest.mark.parametrize(
    ("package", "forbidden"), sorted(FORBIDDEN_IMPORTS.items())
)
def test_dependency_boundaries(package: str, forbidden: set[str]) -> None:
    violations: list[str] = []
    for path in _python_files(package):
        for module in _imports(path) & forbidden:
            violations.append(f"{path.relative_to(ROOT)} imports {module}")
    assert not violations, "\n".join(violations)


def test_import_has_no_side_effects(tmp_path: Path, forbid_network: None) -> None:
    """Importing the app and building the container writes nothing and connects nowhere."""
    from qa_service.app import create_app
    from qa_service.container import build_container, close_container
    from qa_service.settings import Settings

    before = {p for p in tmp_path.rglob("*")}
    app = create_app(Settings(data_dir=tmp_path / "var"))
    container = build_container(Settings(data_dir=tmp_path / "var"))
    close_container(container)
    after = {p for p in tmp_path.rglob("*")}
    assert before == after
    assert not (tmp_path / "var").exists(), "create_app must not create the data directory"
    assert app.state.container.mode == "scaffold"
    assert "qa_service" in sys.modules


def test_required_public_signatures() -> None:
    """Contracts and placeholders expose the frozen surface."""
    from qa_contracts import model_ports, ports

    assert hasattr(ports, "KnowledgeCatalog")
    assert hasattr(ports, "SnapshotReader")
    assert hasattr(ports, "Embedder")
    assert hasattr(model_ports, "ModelInstaller")
    assert hasattr(model_ports, "InferenceGuard")


def test_contracts_package_is_lightweight() -> None:
    """Contract DTOs must be usable without FastAPI or a DB driver installed."""
    import qa_contracts
    from qa_contracts import answers, knowledge, models, operations, repositories, selection  # noqa: F401

    assert qa_contracts.SCHEMA_VERSION == 1
    assert qa_contracts.EVENT_SCHEMA_VERSION == 1
    assert qa_contracts.HTTP_SCHEMA_VERSION == 2
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in _python_files("qa_contracts")
    )
    assert "import fastapi" not in source
    assert "import sqlite3" not in source
