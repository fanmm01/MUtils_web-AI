"""Assemble A1 services on demand from the open container.

Routes never construct repositories themselves: this module is the one place
that turns the container into services. If the database has not been migrated,
every business call fails with an actionable 503 instead of silently creating a
schema or returning fake data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kb_management.content import ContentService
from kb_management.imports import FileResolver, ImportService
from kb_management.indexing import BuildRequest, IndexBuilder, SnapshotPublisher
from kb_management.parsers import ParserRegistry
from kb_management.service import KBService
from kb_management.sources import LocalSource, SourceRoot, SourceService, UploadSource
from kb_management.versions import VersionService
from qa_contracts.errors import ProviderUnavailable, ValidationFailed
from qa_contracts.knowledge import ChunkProfile
from qa_infrastructure.indexes import BM25Index
from qa_infrastructure.repositories import SQLiteKnowledgeRepository

from .container import Container, open_container


class ContentRebuilder:
    """Content edits enqueue a whole-base rebuild so QA pairs are indexed too.

    The manifest-driven import path only covers source files; this path makes
    directly entered documents and QA pairs reach a snapshot.
    """

    def __init__(self, *, builder: IndexBuilder | None, snapshots: object) -> None:
        self._builder = builder
        self._snapshots = snapshots

    async def request_build(self, kb_id: str, *, reason: str) -> str | None:
        del reason
        if self._builder is None:
            return None
        outcome = await self._builder.build(BuildRequest(kb_id=kb_id))
        return outcome.snapshot.version_id if outcome.snapshot else None


@dataclass(slots=True)
class BusinessServices:
    container: Container
    knowledge: KBService
    content: ContentService
    imports: ImportService
    sources: SourceService
    versions: VersionService
    uploads: UploadSource
    resolver: FileResolver
    parser: ParserRegistry


async def services(
    container: Container, *, chunk_profile: ChunkProfile | None = None
) -> BusinessServices:
    if not container.opened:
        await _open(container)
    assert container.knowledge is not None
    assert container.sources is not None
    assert container.content is not None
    assert container.qa_pairs is not None
    assert container.snapshots is not None
    assert container.jobs is not None
    assert container.previews is not None
    assert container.uploads is not None
    assert container.snapshot_files is not None
    assert container.blobs is not None

    shared_blobs = container.blobs
    resolver = FileResolver(
        FileResolver.default_roots(container.settings.source_roots)
    )
    parser = ParserRegistry()
    profile = chunk_profile or _profile_from_settings(container)
    builder = (
        IndexBuilder(
            knowledge=container.knowledge,
            sources=container.sources,
            content=container.content,
            snapshots=container.snapshots,
            files=container.snapshot_files,
            parser=parser,
            splitter=_splitter(),
            keyword_writer=BM25Index(container.settings.data_dir / "indexes"),
            chunk_profile=profile,
            keyword_profile=container.settings.chunking.keyword_profile,
            store=container.store,
            qa_pairs=container.qa_pairs,
        )
        if profile is not None
        else None
    )
    publisher = SnapshotPublisher(
        knowledge=container.knowledge,
        snapshots=container.snapshots,
        files=container.snapshot_files,
        sources=container.sources,
        store=container.store,
    )
    rebuilds = ContentRebuilder(builder=builder, snapshots=container.snapshots)
    return BusinessServices(
        container=container,
        knowledge=KBService(
            knowledge=container.knowledge,
            sources=container.sources,
            content=container.content,
            qa_pairs=container.qa_pairs,
            snapshots=container.snapshots,
        ),
        content=ContentService(
            content=container.content,
            qa_pairs=container.qa_pairs,
            builds=rebuilds,
            store=container.store,
        ),
        imports=ImportService(
            knowledge=container.knowledge,
            sources=container.sources,
            previews=container.previews,
            jobs=container.jobs,
            builder=builder,
            content=container.content,
            files=resolver,
            local_roots=container.settings.source_roots,
            upload_root=container.settings.data_dir / "uploads",
        ),
        sources=SourceService(sources=container.sources),
        versions=VersionService(
            snapshots=container.snapshots,
            knowledge=container.knowledge,
            publisher=publisher,
        ),
        uploads=UploadSource(
            blobs=shared_blobs,
            uploads=container.uploads,
            sources=container.sources,
            upload_root=container.settings.data_dir / "uploads",
        ),
        resolver=resolver,
        parser=parser,
    )


async def rebuild_services(container: Container, *, chunk_profile: ChunkProfile | None = None):
    """Used by the worker, which must run after shutdown of the request loop."""
    return await services(container, chunk_profile=chunk_profile)


async def require_services(container: Container) -> BusinessServices:
    """Fetch services or refuse honestly: 501 in scaffold, 503 without a database."""
    from qa_contracts.errors import FeatureNotImplemented

    if container.settings.mode == "scaffold":
        raise FeatureNotImplemented(container.settings.mode)
    return await services(container)


async def _open(container: Container) -> None:
    if container.store is None:
        raise ProviderUnavailable("the service container was not built")
    if not container.store.database_path.exists():
        raise ProviderUnavailable(
            "database is not initialized; run 'qa-migrate' before serving business requests"
        )
    await open_container(container)


def _profile_from_settings(container: Container) -> ChunkProfile | None:
    chunking = container.settings.chunking
    if not chunking.configured:
        return None
    assert chunking.target_tokens is not None and chunking.overlap_tokens is not None
    return ChunkProfile(
        target_tokens=chunking.target_tokens, overlap_tokens=chunking.overlap_tokens
    )


def _splitter():  # type: ignore[no-untyped-def]
    """A2 owns the chunker; import lazily so A1 routes stay usable without it."""
    try:
        from kb_management.chunking import Chunker
    except ImportError as exc:  # pragma: no cover - package is a workspace member
        raise ValidationFailed() from exc
    return Chunker()


def source_root(container: Container, root_id: str) -> LocalSource:
    configured = container.settings.source_roots.get(root_id)
    if configured is None:
        raise ValidationFailed()
    return LocalSource(SourceRoot(root_id=root_id, path=Path(configured)))


__all__ = [
    "BusinessServices",
    "SQLiteKnowledgeRepository",
    "rebuild_services",
    "services",
    "source_root",
]
