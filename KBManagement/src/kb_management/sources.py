"""Source registration, scanning and streamed upload placeholders (A1 owner)."""

from __future__ import annotations

from typing import BinaryIO

from qa_contracts.knowledge import Selection, Source, SourceManifest

from . import unimplemented


class SourceService:
    async def register(self, req: Source) -> Source:
        raise unimplemented("kb.sources.register")

    async def get(self, source_id: str) -> Source:
        raise unimplemented("kb.sources.get")

    async def list(self, kb_id: str) -> list[Source]:
        raise unimplemented("kb.sources.list")

    async def update(self, source_id: str, req: Source) -> Source:
        raise unimplemented("kb.sources.update")

    async def remove(self, source_id: str) -> None:
        raise unimplemented("kb.sources.remove")


class LocalSource:
    async def scan(self, root_id: str, selection: Selection) -> SourceManifest:
        raise unimplemented("kb.sources.local.scan")


class UploadSource:
    async def begin(self, manifest: list[str]) -> str:
        raise unimplemented("kb.sources.upload.begin")

    async def write(self, batch_id: str, relative_path: str, stream: BinaryIO) -> str:
        raise unimplemented("kb.sources.upload.write")

    async def finish(self, batch_id: str) -> SourceManifest:
        raise unimplemented("kb.sources.upload.finish")


class DirectoryPoller:
    async def tick(self, source_id: str) -> object:
        raise unimplemented("kb.sources.poller.tick")
