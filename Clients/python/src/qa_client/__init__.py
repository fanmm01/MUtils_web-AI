"""Python SDK package. Exports only the public client surface."""

from __future__ import annotations

from .client import Client, QAError
from .sse import SSEEvent, decode_sse, resume_cursor

__all__ = ["Client", "QAError", "SSEEvent", "decode_sse", "resume_cursor"]
