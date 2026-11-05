"""Structure-aware chunking placeholder (A2 owner).

Chunks keep a locator back to the parsed source; a table header is inherited by
its rows. Split sizes are decided by corpus analysis in P2, not guessed here.
"""

from __future__ import annotations

from qa_contracts.knowledge import Chunk, Locator, ParsedBlock, ParsedDocument

from . import unimplemented


class ChunkProfile:
    def __init__(self, target_tokens: int = 320, overlap_tokens: int = 40) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens


class Chunker:
    def split(self, document: ParsedDocument, profile: ChunkProfile) -> list[Chunk]:
        raise unimplemented("kb.chunking.split")

    def split_table(self, block: ParsedBlock, profile: ChunkProfile) -> list[Chunk]:
        raise unimplemented("kb.chunking.split_table")

    def map_locator(self, chunk: Chunk, source_blocks: list[ParsedBlock]) -> Locator:
        raise unimplemented("kb.chunking.map_locator")
