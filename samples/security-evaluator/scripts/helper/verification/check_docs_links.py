#!/usr/bin/env python3
"""Check that local markdown links inside the security-evaluator sample resolve."""

from __future__ import annotations

import re
import sys
from pathlib import Path


SAMPLE_DIR = Path(__file__).resolve().parents[3]

LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")


def _check_file(*, file_path: Path) -> list[str]:
    """Return unresolved local links in one markdown file."""
    unresolved: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"{file_path}: unreadable ({exc})"]

    for match in LINK_PATTERN.finditer(content):
        target = match.group(1).split("#", 1)[0].strip()
        if not target:
            continue
        resolved = (file_path.parent / target).resolve()
        if not resolved.exists():
            unresolved.append(f"{file_path.relative_to(SAMPLE_DIR)} -> {target}")
    return unresolved


def main() -> int:
    """Check all markdown files under the sample pack."""
    markdown_files = sorted(SAMPLE_DIR.rglob("*.md"))
    unresolved: list[str] = []

    for markdown_file in markdown_files:
        unresolved.extend(_check_file(file_path=markdown_file))

    if unresolved:
        print("DOC_LINK_SANITY_FAIL")
        for item in unresolved[:100]:
            print(item)
        return 1

    print("DOC_LINK_SANITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
