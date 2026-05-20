"""Common helpers for JSON report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_report(*, output_path: Path, payload: Any) -> Path:
    """Write JSON report payload with consistent UTF-8 + indentation settings."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
