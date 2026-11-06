"""Application settings.

Settings describe the *scaffold*: no runtime discovery, no model loading and no
database creation happens while settings are loaded.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from qa_contracts.base import ContractModel
from qa_contracts.models import RuntimeKind, RuntimeTarget

ScaffoldMode = Literal["scaffold", "operational"]


class SelectionLimits(ContractModel):
    max_candidate_kbs: int = Field(default=20, ge=1, le=200)
    max_selected_kbs: int = Field(default=3, ge=1, le=20)
    per_kb_candidate_budget: int = Field(default=20, ge=1, le=200)
    probe_concurrency: int = Field(default=4, ge=1, le=64)
    probe_timeout_ms: int = Field(default=1500, ge=1)


class ChunkingSettings(ContractModel):
    """No default size: the values must come from a corpus analysis decision."""

    target_tokens: int | None = Field(default=None, ge=1)
    overlap_tokens: int | None = Field(default=None, ge=0)
    keyword_profile: str = "zh-bm25-v1"

    @property
    def configured(self) -> bool:
        return self.target_tokens is not None and self.overlap_tokens is not None


class Settings(ContractModel):
    mode: ScaffoldMode = "scaffold"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    data_dir: Path = Path("var")
    allowed_origins: list[str] = Field(default_factory=list)
    #: Server-side allow-list. Clients may only reference ``target_id``.
    runtime_targets: list[RuntimeTarget] = Field(default_factory=list)
    #: Server-side authorized local roots (``root_id`` → absolute path).
    source_roots: dict[str, Path] = Field(default_factory=dict)
    selection: SelectionLimits = Field(default_factory=SelectionLimits)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    default_history_policy: Literal["reset_on_scope_change", "carry_user_questions"] = (
        "reset_on_scope_change"
    )

    @property
    def is_scaffold(self) -> bool:
        return self.mode == "scaffold"


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    """Read ``QA_*`` environment variables without printing or persisting secrets."""
    import json
    import os

    env = os.environ if environ is None else environ
    raw_targets = env.get("QA_RUNTIME_TARGETS", "").strip()
    targets: list[RuntimeTarget] = []
    if raw_targets:
        for entry in json.loads(raw_targets):
            targets.append(
                RuntimeTarget(
                    target_id=entry["target_id"],
                    kind=RuntimeKind(entry.get("kind", "ollama")),
                    display_name=entry.get("display_name", ""),
                )
            )
    raw_origins = env.get("QA_ALLOWED_ORIGINS", "").strip()
    origins = [item for item in raw_origins.split(",") if item] if raw_origins else []
    raw_root = env.get("QA_SOURCE_ROOTS", "").strip()
    roots = json.loads(raw_root) if raw_root else {}
    target_tokens = env.get("QA_CHUNK_TARGET_TOKENS", "").strip()
    overlap_tokens = env.get("QA_CHUNK_OVERLAP_TOKENS", "").strip()
    return Settings(
        mode=env.get("QA_MODE", "scaffold"),
        host=env.get("QA_HOST", "127.0.0.1"),
        port=int(env.get("QA_PORT", "8000")),
        data_dir=Path(env.get("QA_DATA_DIR", "var")),
        allowed_origins=origins,
        runtime_targets=targets,
        source_roots={key: Path(value) for key, value in roots.items()},
        selection=SelectionLimits(
            max_candidate_kbs=int(env.get("QA_MAX_CANDIDATE_KBS", "20")),
            max_selected_kbs=int(env.get("QA_MAX_SELECTED_KBS", "3")),
            probe_timeout_ms=int(env.get("QA_PROBE_TIMEOUT_MS", "1500")),
        ),
        chunking=ChunkingSettings(
            target_tokens=int(target_tokens) if target_tokens else None,
            overlap_tokens=int(overlap_tokens) if overlap_tokens else None,
            keyword_profile=env.get("QA_KEYWORD_PROFILE", "zh-bm25-v1"),
        ),
    )
