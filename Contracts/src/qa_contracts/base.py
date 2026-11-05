"""Shared, transport-agnostic contracts for every backend module.

Only data models, error codes and Protocol definitions live here. Importing this
package must not depend on FastAPI, a database driver or a model SDK.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

#: Bumped only by a Contract Gate when a breaking change is frozen.
SCHEMA_VERSION = 1

#: Opaque server-generated identifier.
ID = Annotated[str, Field(min_length=1, max_length=256)]


def utc_now() -> datetime:
    """Return an aware UTC timestamp; all contract timestamps are UTC."""
    return datetime.now(UTC)


class ContractModel(BaseModel):
    """Base for every shared DTO.

    ``extra="forbid"`` keeps clients from smuggling undisclosed fields (for
    example a provider URL into a discovery request) past validation.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Page[T](ContractModel):
    """Cursor-paginated response envelope."""

    items: list[T] = Field(default_factory=list)
    next_cursor: str | None = None
