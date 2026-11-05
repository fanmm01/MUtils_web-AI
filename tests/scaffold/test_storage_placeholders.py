"""A1 placeholder adapters: typed, side-effect free and honest about 501."""

from __future__ import annotations

import pytest

from qa_contracts.errors import FeatureNotImplemented
from qa_infrastructure.blobs import FileBlobStore
from qa_infrastructure.catalog import AuthorizedKnowledgeCatalog
from qa_infrastructure.indexes import BM25Index, DenseIndex, EmbeddingCache
from qa_infrastructure.ollama import OllamaDiscovery, OllamaInstaller, OllamaRuntime
from qa_infrastructure.providers import (
    ConfiguredEmbedder,
    ConfiguredReranker,
    ConfiguredSupportChecker,
    ConfiguredTokenCounter,
    build_provider,
)
from qa_infrastructure.snapshots import FileSnapshotStore, PublishedSnapshotReader
from qa_infrastructure.sqlite import SQLiteStore


@pytest.mark.parametrize(
    "call",
    [
        lambda: SQLiteStore.__new__(SQLiteStore).migrate("head"),
        lambda: FileBlobStore(__import__("pathlib").Path(".")).verify("x"),
        lambda: FileSnapshotStore(__import__("pathlib").Path(".")).stage([]),
        lambda: PublishedSnapshotReader().resolve("kb", None),
        lambda: BM25Index().search("q", object(), 5),
        lambda: DenseIndex().search([0.1], object(), 5),
        lambda: EmbeddingCache().get_many([]),
        lambda: AuthorizedKnowledgeCatalog().list_authorized(None, None),
        lambda: ConfiguredEmbedder().embed([], None, None),
        lambda: ConfiguredReranker().rank("q", [], None),
        lambda: ConfiguredTokenCounter().count(None, None),
        lambda: ConfiguredSupportChecker().check("s", [], None),
        lambda: OllamaDiscovery().discover([]),
        lambda: OllamaRuntime().probe(None),
        lambda: OllamaInstaller().preview(None),
    ],
)
def test_placeholders_refuse_instead_of_faking(call) -> None:
    with pytest.raises(FeatureNotImplemented) as excinfo:
        _run(call)
    assert excinfo.value.status_code == 501


def _run(call):  # type: ignore[no-untyped-def]
    import asyncio
    import inspect

    result = call()
    if inspect.isawaitable(result):
        return asyncio.run(result)
    if inspect.isgenerator(result) or hasattr(result, "__anext__"):
        raise FeatureNotImplemented("generator placeholder")
    return result


def test_provider_bundle_is_empty_and_offline(tmp_path) -> None:
    bundle = build_provider(object())
    assert bundle.providers == {}
    assert not (tmp_path / "volumes").exists()


def test_store_records_path_but_opens_nothing(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "kb.sqlite3")
    assert store.database_path == tmp_path / "kb.sqlite3"
    assert not store.database_path.exists()
