"""Version-pinned keyword index; dense indexing remains a P3 capability."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

from qa_contracts.answers import Hit
from qa_contracts.base import ID
from qa_contracts.errors import FeatureNotImplemented, NotFound
from qa_contracts.knowledge import Chunk, SearchScope

from . import unimplemented

# Keep hyphenated identifiers whole (e.g. ERR-404) while deriving adjacent
# Han bigrams without depending on a runtime dictionary or model.
_TERM = re.compile(r"[㐀-鿿]+|[a-z0-9_]+(?:[-./][a-z0-9_]+)*", re.I)
_REF = re.compile(r"[0-9a-f]{64}\Z")


class ChineseTokenizer:
    def tokenize(self, text: str) -> list[str]:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        tokens: list[str] = []
        for match in _TERM.finditer(normalized):
            word = match.group()
            if "㐀" <= word[0] <= "鿿":
                tokens.extend(word)
                tokens.extend(word[i : i + 2] for i in range(len(word) - 1))
            else:
                tokens.append(word)
        return tokens


class BM25Index:
    """Content-addressed immutable index, scoped to exactly one KB snapshot.

    A root stores sealed JSON files that another process can open by index_ref;
    without a root, the same implementation is an isolated in-memory fake.
    ``build`` is the frozen KeywordIndexWriter port and ``search`` is the
    KeywordReader port. No SQLite, HTTP, or model runtime is imported.
    """

    def __init__(
        self, root: Path | None = None, *, tokenizer: ChineseTokenizer | None = None
    ) -> None:
        self._root = root
        self._memory: dict[str, bytes] = {}
        self._tokenizer = tokenizer or ChineseTokenizer()

    async def build(self, chunks: list[Chunk], profile: str) -> str:
        if not profile:
            raise ValueError("keyword profile must not be empty")
        if not chunks:
            # The frozen writer port supplies no KB/version apart from Chunk.
            # A shared empty index could masquerade as any published snapshot.
            raise ValueError("empty keyword index cannot be pinned to a KB/version")
        identities = {(chunk.kb_id, chunk.version_id) for chunk in chunks}
        if len(identities) > 1:
            raise ValueError("one keyword index must contain one KB and version")
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("duplicate chunk IDs in keyword index")
        payload = {
            "kb_id": chunks[0].kb_id,
            "version_id": chunks[0].version_id,
            "profile": profile,
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }
        return self._store_payload(payload)

    async def build_empty(self, kb_id: str, version_id: str, profile: str) -> str:
        """Seal an empty index with explicit, immutable KB/version identity."""
        if not all(
            isinstance(value, str) and 1 <= len(value) <= 256
            for value in (kb_id, version_id)
        ) or not isinstance(profile, str) or not profile:
            raise ValueError("empty keyword index requires a KB, version and profile")
        return self._store_payload(
            {"kb_id": kb_id, "version_id": version_id, "profile": profile, "chunks": []}
        )

    def _store_payload(self, payload: dict[str, object]) -> str:
        encoded = json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        ref = hashlib.sha256(encoded).hexdigest()
        if self._root is None:
            self._memory[ref] = encoded
        else:
            self._root.mkdir(parents=True, exist_ok=True)
            target = self._root / f"{ref}.json"
            if target.exists():
                if target.read_bytes() != encoded:
                    raise ValueError("keyword index is corrupt")
            else:
                fd, staging = tempfile.mkstemp(prefix=".keyword-", dir=self._root)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(encoded)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(staging, target)
                finally:
                    if os.path.exists(staging):
                        os.unlink(staging)
        return ref

    async def search(self, query: str, scope: SearchScope, k: int) -> list[Hit]:
        if k < 1:
            raise ValueError("top_k must be positive")
        if not isinstance(scope, SearchScope):
            raise FeatureNotImplemented("infrastructure.indexes.bm25.search")
        if not _REF.fullmatch(scope.index_ref):
            raise ValueError("invalid keyword index reference")
        if self._root is None:
            if scope.index_ref not in self._memory:
                raise NotFound("keyword index")
            encoded = self._memory[scope.index_ref]
        else:
            try:
                encoded = (self._root / f"{scope.index_ref}.json").read_bytes()
            except FileNotFoundError as exc:
                raise NotFound("keyword index") from exc
        if hashlib.sha256(encoded).hexdigest() != scope.index_ref:
            raise ValueError("keyword index is corrupt")
        payload = json.loads(encoded)
        if payload["profile"] != scope.keyword_profile or (
            payload["kb_id"],
            payload["version_id"],
        ) != (scope.kb_id, scope.version_id):
            raise ValueError("keyword index does not match the pinned search scope")
        chunks = [Chunk.model_validate(row) for row in payload["chunks"]]
        if not chunks:
            return []
        normalized_query = unicodedata.normalize("NFKC", query).casefold()
        # A single shared Han character (e.g. 的) must not make an unrelated
        # multi-character query match. Keep unigrams only for one-character runs.
        terms: set[str] = set()
        for match in _TERM.finditer(normalized_query):
            word = match.group()
            if "㐀" <= word[0] <= "鿿" and len(word) > 1:
                terms.update(word[i : i + 2] for i in range(len(word) - 1))
            else:
                terms.add(word)
        if not terms:
            return []
        counts = [Counter(self._tokenizer.tokenize(chunk.text)) for chunk in chunks]
        lengths = [sum(row.values()) for row in counts]
        avg_length = sum(lengths) / len(chunks) or 1.0
        document_frequency = Counter(term for row in counts for term in row)
        matches: list[tuple[float, Chunk]] = []
        for chunk, row, length in zip(chunks, counts, lengths, strict=True):
            score = 0.0
            for term in terms & row.keys():
                frequency = row[term]
                idf = math.log1p(
                    (len(chunks) - document_frequency[term] + 0.5)
                    / (document_frequency[term] + 0.5)
                )
                score += (
                    idf
                    * (frequency * 2.2)
                    / (frequency + 1.2 * (0.25 + 0.75 * length / avg_length))
                )
            if score > 0:
                matches.append((score, chunk))
        matches.sort(key=lambda pair: (-pair[0], pair[1].ordinal, pair[1].chunk_id))
        return [
            Hit(
                kb_id=chunk.kb_id,
                version_id=chunk.version_id,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=score,
                locator=chunk.locator,
            )
            for score, chunk in matches[:k]
        ]


class DenseIndex:
    async def build(self, vectors: list[list[float]], mapping: list[ID]) -> str:
        raise unimplemented("infrastructure.indexes.dense.build")

    async def search(self, vector: list[float], scope: SearchScope, k: int) -> list[Hit]:
        raise unimplemented("infrastructure.indexes.dense.search")


class EmbeddingCache:
    async def get_many(self, keys: list[str]) -> dict[str, list[float]]:
        raise unimplemented("infrastructure.indexes.cache.get_many")

    async def put_many(self, items: dict[str, list[float]]) -> None:
        raise unimplemented("infrastructure.indexes.cache.put_many")
