"""SSE decoding shared by answer and job streams.

TCP chunks are not event boundaries: a UTF-8 character or a ``data:`` line may
split across chunks. Decode incrementally and only emit on a blank line.
"""

from __future__ import annotations

import codecs
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field


@dataclass(slots=True)
class SSEEvent:
    """A decoded server-sent event."""

    id: int | None = None
    event: str | None = None
    data: str = ""
    retry: int | None = None
    fields_extra: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict[str, object]:
        import json

        return json.loads(self.data) if self.data else {}


def decode_sse(byte_chunks: Iterable[bytes]) -> Iterator[SSEEvent]:
    """Incrementally decode an SSE byte stream.

    Handles multi-line ``data:`` fields, comments (heartbeats), ``id``/
    ``retry`` fields and UTF-8 sequences split across chunks.
    """
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    data_lines: list[str] = []
    event_name: str | None = None
    event_id: int | None = None
    retry: int | None = None

    def emit() -> SSEEvent | None:
        nonlocal data_lines, event_name, event_id, retry
        if not data_lines and event_name is None:
            return None
        event = SSEEvent(
            id=event_id,
            event=event_name,
            data="\n".join(data_lines),
            retry=retry,
        )
        data_lines = []
        event_name = None
        return event

    for chunk in byte_chunks:
        buffer += decoder.decode(chunk)
        while True:
            newline = _find_line_end(buffer)
            if newline is None:
                break
            line, buffer = buffer[: newline[0]], buffer[newline[1] :]
            if line == "":
                event = emit()
                if event is not None:
                    yield event
                continue
            if line.startswith(":"):
                continue  # heartbeat / comment
            name, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if name == "data":
                data_lines.append(value)
            elif name == "event":
                event_name = value
            elif name == "id":
                try:
                    event_id = int(value)
                except ValueError:
                    event_id = None
            elif name == "retry":
                try:
                    retry = int(value)
                except ValueError:
                    retry = None
    buffer += decoder.decode(b"", final=True)
    if buffer:
        line = buffer
        if line and not line.startswith(":"):
            name, _, value = line.partition(":")
            if name == "data":
                data_lines.append(value[1:] if value.startswith(" ") else value)
    event = emit()
    if event is not None:
        yield event


def _find_line_end(buffer: str) -> tuple[int, int] | None:
    """Return ``(line_length, next_index)`` for the first complete line."""
    for index, char in enumerate(buffer):
        if char == "\n":
            end = index
            if end > 0 and buffer[end - 1] == "\r":
                end -= 1
            return end, index + 1
    return None


def resume_cursor(events: Iterable[SSEEvent]) -> int | None:
    """Last replayable sequence number seen, for ``Last-Event-ID``."""
    last: int | None = None
    for event in events:
        if event.id is not None:
            last = event.id
    return last
