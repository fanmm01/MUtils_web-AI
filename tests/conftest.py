"""Test fixtures shared by A1 scaffold tests.

No network, no database and no model: every fixture is in-memory.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qa_service.app import create_app
from qa_service.settings import Settings


@pytest.fixture()
def scaffold_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("QA_DATA_DIR", str(tmp_path / "var"))
    return Settings(data_dir=tmp_path / "var")


@pytest.fixture()
def client(scaffold_settings: Settings) -> Iterator[TestClient]:
    app = create_app(scaffold_settings)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def forbid_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if scaffold code opens a socket."""
    import socket

    def _blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("scaffold code attempted network access")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)


@pytest.fixture(autouse=True)
def _isolate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    (tmp_path / "home").mkdir(exist_ok=True)
    for key in ("QA_MODE", "QA_HOST", "QA_PORT", "QA_ALLOWED_ORIGINS", "QA_RUNTIME_TARGETS"):
        monkeypatch.delenv(key, raising=False)
    assert os.environ["HOME"] == str(tmp_path / "home")
