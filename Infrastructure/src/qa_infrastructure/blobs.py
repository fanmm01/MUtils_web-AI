"""Content-addressed blob store: streaming writes, hash verification, GC.

Files are stored as ``<root>/<aa>/<digest>``. Writes go to a temporary file in
the same directory and are atomically renamed after the hash is known, so a
crashed upload never leaves a partial file under a content address.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

from qa_contracts.errors import NotFound

_CHUNK = 1024 * 1024


class FileBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, digest: str) -> Path:
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("blob digest must be a lowercase sha256 hex string")
        return self.root / digest[:2] / digest

    async def put(self, stream: BinaryIO) -> str:
        return await asyncio.to_thread(self._put_sync, stream)

    def _put_sync(self, stream: BinaryIO) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        handle, staging = tempfile.mkstemp(prefix=".blob-", dir=self.root)
        digest = hashlib.sha256()
        try:
            with os.fdopen(handle, "wb") as target:
                while True:
                    chunk = stream.read(_CHUNK)
                    if not chunk:
                        break
                    digest.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            hexdigest = digest.hexdigest()
            final = self.path_for(hexdigest)
            final.parent.mkdir(parents=True, exist_ok=True)
            if final.exists():
                os.unlink(staging)
            else:
                os.replace(staging, final)
            return hexdigest
        except BaseException:
            if os.path.exists(staging):
                os.unlink(staging)
            raise

    async def put_bytes(self, data: bytes) -> str:
        return await self.put(_BytesReader(data))

    async def get(self, ref: str) -> BinaryIO:
        path = self.path_for(ref)
        if not path.is_file():
            raise NotFound("blob")
        return path.open("rb")

    async def read_bytes(self, ref: str) -> bytes:
        path = self.path_for(ref)
        if not path.is_file():
            raise NotFound("blob")
        return await asyncio.to_thread(path.read_bytes)

    async def verify(self, ref: str) -> bool:
        try:
            path = self.path_for(ref)
        except ValueError:
            return False
        if not path.is_file():
            return False
        return await asyncio.to_thread(_digest_of, path) == ref

    async def delete_unreferenced(self, refs: list[str]) -> int:
        removed = 0
        for ref in refs:
            try:
                path = self.path_for(ref)
            except ValueError:
                continue
            if path.is_file():
                path.unlink()
                removed += 1
        return removed


class _BytesReader:
    """Minimal BinaryIO surface used to feed bytes through the streaming path."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            chunk, self._offset = self._data[self._offset:], len(self._data)
            return chunk
        start, self._offset = self._offset, min(len(self._data), self._offset + size)
        return self._data[start:self._offset]


def _digest_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
