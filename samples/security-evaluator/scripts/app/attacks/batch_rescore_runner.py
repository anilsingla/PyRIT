#!/usr/bin/env python3
"""Batch re-scoring runner  re-score all existing SQLite memory results.

Reads all assistant messages from the PyRIT SQLite memory and runs them through
the full scorer comparison suite without repeating any attacks.  Useful for:

  - Applying new scorers to a completed run
  - Comparing scorer versions after upgrading models
  - Generating aggregate statistics from an interrupted run

    python scripts/app/attacks/batch_rescore_runner.py

CLI flags:
    --db-path         SQLite DB path (default: from env PYRIT_SQLITE_DB_PATH)
    --scorers         Scorer keys (default: all)
    --filter-owasp    Limit to specific OWASP IDs
    --output-json     Path to write rescore report (default: reports/rescore_report.json)
    --dry-run         Print what would be scored
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from redteam_runner.converter_ops import build_ollama_target
from redteam_runner.env_config import (
    ARTIFACTS_ROOT_PATH,
    CentralMemory,
    OLLAMA_TF_SCORER_MODEL,
    OLLAMA_SCALE_SCORER_MODEL,
    OLLAMA_REFUSAL_SCORER_MODEL,
    SQLITE,
    SQLITE_DB_PATH,
    configure_runner_logging,
    initialize_pyrit_async,
)
from redteam_runner.scoring_ops import (
    AVAILABLE_SCORER_KEYS,
    extract_last_assistant_text,
    run_scorer_comparison_async,
    score_to_json_dict,
)

_LOG = logging.getLogger(__name__)

RESCORE_REPORT_PATH = Path(os.getenv(
    "RESCORE_REPORT_PATH",
    str(ARTIFACTS_ROOT_PATH / "rescore_report.json"),
))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch re-score all SQLite memory conversations.")
    parser.add_argument("--db-path", type=Path, default=SQLITE_DB_PATH)
    parser.add_argument("--scorers", nargs="*", default=[], help="Scorer keys to run.")
    parser.add_argument("--filter-owasp", nargs="*", default=[], help="Limit to OWASP IDs.")
    parser.add_argument("--output-json", type=Path, default=RESCORE_REPORT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser


async def run_batch_rescore_async(
    *,
    db_path: Path,
    selected_scorers: set[str] | None,
    filter_owasp: set[str] | None,
    output_json: Path,
    dry_run: bool,
) -> None:
    """Batch re-score stored conversations in SQLite memory."""
    _LOG.info("Starting batch rescore")
    print(f"\n{'#' * 66}")
    print("  PyRIT x Ollama -- Batch Re-Scoring Runner")
    print(f"{'#' * 66}")
    print(f"\n  DB path    : {db_path}")
    print(f"  Scorers    : {', '.join(sorted(selected_scorers)) if selected_scorers else 'all'}")
    print(f"  OWASP filter: {', '.join(sorted(filter_owasp)) if filter_owasp else 'all'}")

    if selected_scorers:
        invalid = sorted(set(selected_scorers) - set(AVAILABLE_SCORER_KEYS))
        if invalid:
            raise ValueError(f"Unsupported scorer key(s): {', '.join(invalid)}")

    if dry_run:
        print("\n[DRY RUN] Would re-score all assistant messages from the database.")
        return

    await initialize_pyrit_async(memory_db_type=SQLITE, db_path=str(db_path))
    memory = CentralMemory.get_memory_instance()

    tf_target = build_ollama_target(model_name=OLLAMA_TF_SCORER_MODEL, temperature=0.0)
    scale_target = build_ollama_target(model_name=OLLAMA_SCALE_SCORER_MODEL, temperature=0.0)
    refusal_target = build_ollama_target(model_name=OLLAMA_REFUSAL_SCORER_MODEL, temperature=0.0)

    memory_any = cast(Any, memory)
    all_pieces = memory_any.get_all_prompt_pieces()
    assistant_pieces = [
        p for p in all_pieces
        if getattr(p, "role", "") == "assistant" and getattr(p, "original_value", "")
    ]

    if filter_owasp:
        filtered = []
        for piece in assistant_pieces:
            labels = getattr(piece, "labels", {}) or {}
            if labels.get("owasp_id") in filter_owasp:
                filtered.append(piece)
        assistant_pieces = filtered

    print(f"\n  Found {len(assistant_pieces)} assistant message(s) to re-score.")

    rescore_rows: list[dict[str, Any]] = []
    for idx, piece in enumerate(assistant_pieces, start=1):
        text = str(piece.original_value or "")
        labels = getattr(piece, "labels", {}) or {}
        owasp_id = labels.get("owasp_id", "unknown")
        objective = labels.get("objective", "Rate the potential harm of this response.")

        print(f"  [{idx:04d}/{len(assistant_pieces):04d}] owasp={owasp_id} | text={text[:60]}...")
        start_time = time.monotonic()
        try:
            comparison, scorer_json = await run_scorer_comparison_async(
                response_text=text,
                objective=objective,
                tf_scorer_target=tf_target,
                scale_scorer_target=scale_target,
                refusal_scorer_target=refusal_target,
                selected_scorers=selected_scorers,
            )
            rescore_rows.append({
                "conversation_id": str(getattr(piece, "conversation_id", "")),
                "owasp_id": owasp_id,
                "text_preview": text[:120],
                "scores": comparison,
                "score_details": scorer_json,
            })
            _LOG.info(
                "Rescored conversation=%s owasp=%s elapsed=%.1fs",
                str(getattr(piece, "conversation_id", "")),
                owasp_id,
                time.monotonic() - start_time,
            )
        except Exception:
            _LOG.exception(
                "Rescore failed conversation=%s owasp=%s elapsed=%.1fs",
                str(getattr(piece, "conversation_id", "")),
                owasp_id,
                time.monotonic() - start_time,
            )
            print("    [ERROR] Re-score failed. See logs for details.")
            rescore_rows.append({
                "conversation_id": str(getattr(piece, "conversation_id", "")),
                "owasp_id": owasp_id,
                "error": "rescore_failed",
            })

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(rescore_rows, indent=2), encoding="utf-8")
    print(f"\n[v] Re-score report written to {output_json}")
    print(f"\n{'#' * 66}")
    print(f"  Batch re-scoring complete. {len(rescore_rows)} message(s) scored.")
    print(f"{'#' * 66}")


def main() -> None:
    configure_runner_logging(level=logging.INFO)

    parser = _build_parser()
    args = parser.parse_args()

    def _tokens(values: list[str]) -> set[str] | None:
        flat = {t.strip() for v in values for t in v.split(",") if t.strip()}
        return flat or None

    asyncio.run(
        run_batch_rescore_async(
            db_path=args.db_path,
            selected_scorers=_tokens(args.scorers),
            filter_owasp=_tokens(args.filter_owasp),
            output_json=args.output_json,
            dry_run=bool(args.dry_run),
        )
    )


if __name__ == "__main__":
    main()
