#!/usr/bin/env python3
"""
Optional utility: Import scorer_outputs.json rows into PyRIT SQLite memory as Score records.

This script is only needed if you want to use the optional PyRIT GUI to browse results
interactively. The unified container workflow stores results as JSON/CSV and does not
require this import step.

See: docs/setup/gui_setup.md
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Literal, cast

from common_utils import extract_dict_rows, load_json_dict
from pyrit.memory import CentralMemory
from pyrit.models import Score
from pyrit.setup import SQLITE, initialize_pyrit_async

ScoreTypeLiteral = Literal["true_false", "float_scale", "unknown"]


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(description="Import scorer JSON output into SQLite-backed PyRIT memory.")
    parser.add_argument(
        "--input-json",
        type=Path,
        default=Path("scorer_outputs.json"),
        help="Path to scorer outputs JSON produced by scripts/app/main.py",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("pyrit_ollama_demo.db"),
        help="Path to SQLite DB used by PyRIT.",
    )
    return parser


def _load_rows(*, input_json: Path) -> list[dict[str, object]]:
    """Load scorer rows from JSON file."""
    payload = load_json_dict(input_path=input_json)
    rows = extract_dict_rows(payload=payload, key="rows")
    return [cast(dict[str, object], row) for row in rows]


def _to_identifier(*, scorer_name: str, score_item: dict[str, object]) -> dict[str, object]:
    """Build a scorer identifier payload for Score construction."""
    scorer_identifier = score_item.get("scorer_identifier")
    if isinstance(scorer_identifier, dict):
        return scorer_identifier

    return {
        "class_name": scorer_name,
        "class_module": "samples.imported",
        "params": {},
    }


def _build_scores(*, rows: list[dict[str, object]]) -> list[Score]:
    """Convert scorer rows to Score objects."""
    scores_to_add: list[Score] = []

    for row in rows:
        scores_section = row.get("scores")
        if not isinstance(scores_section, dict):
            continue

        for scorer_name, raw_score_item in scores_section.items():
            if not isinstance(raw_score_item, dict):
                continue

            message_piece_id = raw_score_item.get("message_piece_id")
            score_type = raw_score_item.get("score_type")
            score_value = raw_score_item.get("score_value")

            if not message_piece_id or not isinstance(score_type, str) or score_value is None:
                continue

            if score_type not in {"true_false", "float_scale", "unknown"}:
                continue

            score_item: dict[str, object] = raw_score_item
            score_category_raw = score_item.get("score_category")
            score_metadata_raw = score_item.get("score_metadata")

            score_category = list(score_category_raw) if isinstance(score_category_raw, list) else []
            score_metadata = dict(score_metadata_raw) if isinstance(score_metadata_raw, dict) else {}

            scores_to_add.append(
                Score(
                    score_value=str(score_value),
                    score_value_description=str(score_item.get("score_value_description") or ""),
                    score_type=cast(ScoreTypeLiteral, score_type),
                    score_rationale=str(score_item.get("score_rationale") or ""),
                    score_category=score_category,
                    score_metadata=score_metadata,
                    objective=str(score_item.get("objective") or ""),
                    message_piece_id=str(message_piece_id),
                    scorer_class_identifier=_to_identifier(scorer_name=str(scorer_name), score_item=score_item),
                )
            )

    return scores_to_add


async def _import_async(*, input_json: Path, db_path: Path) -> int:
    """Import scores into SQLite-backed memory."""
    await initialize_pyrit_async(memory_db_type=SQLITE, db_path=str(db_path.resolve()))
    memory = CentralMemory.get_memory_instance()

    rows = _load_rows(input_json=input_json)
    scores_to_add = _build_scores(rows=rows)

    if not scores_to_add:
        print("No importable score rows found in JSON.")
        return 0

    memory.add_scores_to_memory(scores=scores_to_add)
    print(f"Imported {len(scores_to_add)} score rows into {db_path.resolve()}")
    return 0


def main() -> int:
    """Run CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()

    input_json: Path = args.input_json
    db_path: Path = args.db_path

    if not input_json.exists():
        print(f"Input JSON file not found: {input_json}")
        return 2

    try:
        return asyncio.run(_import_async(input_json=input_json, db_path=db_path))
    except Exception as exc:
        print(f"Import failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
