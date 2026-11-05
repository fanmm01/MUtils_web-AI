"""Content-addressed blob store placeholder (streaming, reference-protected)."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from . import unimplemented


class FileBlobStore:
    """Never writes in P1; the root is recorded for later phases only."""

    def __init__(self, root: Path) -> None:
        self.root = root

    async def put(self, stream: BinaryIO) -> str:
        raise unimplemented("infrastructure.blobs.put")

    async def get(self, ref: str) -> BinaryIO:
        raise unimplemented("infrastructure.blobs.get")

    async def verify(self, ref: str) -> bool:
        raise unimplemented("infrastructure.blobs.verify")

    async def delete_unreferenced(self, refs: list[str]) -> int:
        raise unimplemented("infrastructure.blobs.delete_unreferenced")
