"""Report the environment the scaffold relies on.

Read-only: does not start a service, load a model, download weights or scan a
browser machine or LAN. A tool absent from PATH is reported as unknown, not as
proof the machine lacks it. Real protocol probing remains an authorized API
action in later phases.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Tools whose *presence on PATH* is reported. Conversion/OCR remain optional.
OPTIONAL_TOOLS = ("go", "node", "npm", "soffice", "tesseract", "gcc")

CONVERSION_TOOLS = ("soffice",)
OCR_TOOLS = ("tesseract",)


@dataclass
class ToolStatus:
    name: str
    found: bool
    path: str | None = None
    note: str = ""


@dataclass
class CapabilityReport:
    """PATH-visible optional tools; absence is not proof of non-installation."""

    tools: list[ToolStatus] = field(default_factory=list)
    conversion_available: bool = False
    ocr_available: bool = False
    note: str = "PATH check only; install locations and other accounts were not inspected"


@dataclass
class EnvironmentReport:
    python: str
    platform: str
    root: str
    capabilities: CapabilityReport = field(default_factory=CapabilityReport)


@dataclass
class DiscoveryHintReport:
    """Server allow-list names only; nothing was probed."""

    configured_targets: list[str] = field(default_factory=list)
    probed: bool = False
    note: str = "hint only; real protocol probing requires an authorized API action"


def inspect_runtime() -> EnvironmentReport:
    return EnvironmentReport(
        python=platform.python_version(),
        platform=platform.platform(),
        root=str(ROOT),
        capabilities=inspect_optional_tools(),
    )


def inspect_optional_tools() -> CapabilityReport:
    by_name: dict[str, ToolStatus] = {}
    for tool in OPTIONAL_TOOLS:
        path = shutil.which(tool)
        by_name[tool] = ToolStatus(
            name=tool,
            found=path is not None,
            path=path,
            note="" if path else "not found on PATH; install location may still exist",
        )
    return CapabilityReport(
        tools=list(by_name.values()),
        conversion_available=any(by_name[name].found for name in CONVERSION_TOOLS),
        ocr_available=any(by_name[name].found for name in OCR_TOOLS),
    )


def inspect_model_runtime_candidates(
    config: Mapping[str, object] | None = None,
) -> DiscoveryHintReport:
    raw = (config or {}).get("runtime_targets", [])
    if isinstance(raw, str):
        targets = [item for item in raw.split(",") if item.strip()]
    else:
        targets = [str(item) for item in raw]  # type: ignore[union-attr]
    return DiscoveryHintReport(configured_targets=targets)


def main() -> int:
    report = inspect_runtime()
    payload = asdict(report)
    configured = os.environ.get("QA_RUNTIME_TARGETS", "")
    payload["model_runtime"] = asdict(
        inspect_model_runtime_candidates({"runtime_targets": configured})
    )
    payload["python_executable"] = sys.executable
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
