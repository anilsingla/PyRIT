from __future__ import annotations

from typing import Iterable


def parse_token_set(values: Iterable[str]) -> set[str] | None:
    """Convert space/comma-separated CLI values into a normalized token set."""
    parsed = {token.strip() for value in values for token in value.split(",") if token.strip()}
    return parsed or None
