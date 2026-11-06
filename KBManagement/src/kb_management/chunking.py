"""Structure-aware, deterministic chunks with original source positions."""

from __future__ import annotations

import hashlib
import re

from qa_contracts.knowledge import (
    Chunk,
    ChunkProfile,
    Locator,
    LocatorKind,
    ParsedBlock,
    ParsedDocument,
)

# Preserve exact identifiers across boundaries; count Han characters and each
# complete identifier as budget units. The index uses its own search tokenizer.
_TOKENS = re.compile(r"[㐀-鿿]|[A-Za-z0-9_]+(?:[-./][A-Za-z0-9_]+)*|[^\w\s]", re.UNICODE)


def _pieces(text: str, target: int, overlap: int) -> list[tuple[str, int]]:
    matches = list(_TOKENS.finditer(text))
    result: list[tuple[str, int]] = []
    step = target - overlap
    for start in range(0, len(matches), step):
        end = min(start + target, len(matches))
        piece = text[matches[start].start() : matches[end - 1].end()].strip()
        if piece:
            result.append((piece, matches[start].start()))
        if end == len(matches):
            break
    return result


class Chunker:
    def split(
        self,
        document: ParsedDocument,
        *,
        kb_id: str,
        version_id: str,
        revision_id: str,
        profile: ChunkProfile,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        for block in document.blocks:
            if block.locator.kind in {LocatorKind.WORD_TABLE, LocatorKind.EXCEL_RANGE}:
                chunks.extend(
                    self.split_table(
                        block,
                        profile,
                        kb_id=kb_id,
                        version_id=version_id,
                        revision_id=revision_id,
                        start_ordinal=len(chunks),
                    )
                )
                continue
            # Do not cross source blocks: a chunk's locator must describe every
            # character it contains. A heading is included only when its source
            # block already includes it, not fabricated from metadata.
            for text, start in _pieces(block.text, profile.target_tokens, profile.overlap_tokens):
                locator = block.locator
                if locator.kind in {LocatorKind.TEXT_LINES, LocatorKind.MARKDOWN_LINES}:
                    start_line = (locator.start_line or 1) + block.text.count("\n", 0, start)
                    end_position = block.text.find(text, start) + len(text)
                    end_line = (locator.start_line or 1) + block.text.count("\n", 0, end_position)
                    locator = locator.model_copy(
                        update={"start_line": start_line, "end_line": end_line}
                    )
                chunks.append(
                    self._chunk(text, locator, kb_id, version_id, revision_id, len(chunks))
                )
        return chunks

    def split_table(
        self,
        block: ParsedBlock,
        profile: ChunkProfile,
        *,
        kb_id: str,
        version_id: str,
        revision_id: str,
        start_ordinal: int = 0,
    ) -> list[Chunk]:
        """Keep table rows together with their header; never invent cell coordinates."""
        lines = [line.strip() for line in block.text.splitlines() if line.strip()]
        if not lines:
            return []
        header = lines[0]
        # The header is source text; repeat it for each row instead of slicing
        # through a row and losing its column meaning. An oversized row remains
        # intact because partial table rows cannot be located independently.
        texts = [f"{header}\n{row}" for row in lines[1:]] if len(lines) > 1 else [header]
        return [
            self._chunk(text, block.locator, kb_id, version_id, revision_id, start_ordinal + i)
            for i, text in enumerate(texts)
        ]

    def map_locator(self, chunk: Chunk, source_blocks: list[ParsedBlock]) -> Locator:
        for block in source_blocks:
            locator = block.locator
            if locator.kind in {LocatorKind.WORD_TABLE, LocatorKind.EXCEL_RANGE}:
                if locator != chunk.locator:
                    continue
                lines = [line.strip() for line in block.text.splitlines() if line.strip()]
                expected = (
                    [f"{lines[0]}\n{line}" for line in lines[1:]] if len(lines) > 1 else lines
                )
                if chunk.text in expected:
                    return chunk.locator
                continue
            for match in re.finditer(re.escape(chunk.text), block.text):
                if locator.kind in {LocatorKind.TEXT_LINES, LocatorKind.MARKDOWN_LINES}:
                    if (chunk.locator.kind, chunk.locator.heading) != (
                        locator.kind,
                        locator.heading,
                    ):
                        continue
                    expected_start = (locator.start_line or 1) + block.text.count(
                        "\n", 0, match.start()
                    )
                    expected_end = (locator.start_line or 1) + block.text.count(
                        "\n", 0, match.end()
                    )
                    if (chunk.locator.start_line, chunk.locator.end_line) != (
                        expected_start,
                        expected_end,
                    ):
                        continue
                elif locator != chunk.locator:
                    continue
                return chunk.locator
        raise ValueError("chunk is not mapped to a source block")

    @staticmethod
    def _chunk(
        text: str,
        locator: Locator,
        kb_id: str,
        version_id: str,
        revision_id: str,
        ordinal: int,
    ) -> Chunk:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        identity = hashlib.sha256(
            f"{kb_id}\0{version_id}\0{revision_id}\0{ordinal}\0{digest}".encode()
        ).hexdigest()
        return Chunk(
            chunk_id=identity,
            kb_id=kb_id,
            version_id=version_id,
            revision_id=revision_id,
            content_hash=digest,
            text=text,
            locator=locator,
            ordinal=ordinal,
        )
