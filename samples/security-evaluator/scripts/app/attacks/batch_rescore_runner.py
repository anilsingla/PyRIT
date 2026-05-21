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
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

_APP_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_ROOT = Path(__file__).resolve().parents[2]
for _path in (str(_APP_ROOT), str(_SCRIPTS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

RUNTIME_IMPORT_ERROR: ModuleNotFoundError | None = None

try:
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
    from redteam_runner.cli_utils import parse_token_set
    from redteam_runner.scoring_ops import (
        AVAILABLE_SCORER_KEYS,
        extract_last_assistant_text,
        run_scorer_comparison_async,
        score_to_json_dict,
    )
    from reports import write_json_report
    from scorer import validate_scorer_keys
    from utils.output_tools import ENABLE_LIVE_SCORER_FEED, Colors, print_banner, print_scorer_comparison
except ModuleNotFoundError as exc:
    RUNTIME_IMPORT_ERROR = exc

_LOG = logging.getLogger(__name__)

if RUNTIME_IMPORT_ERROR is None:
    RESCORE_REPORT_PATH = Path(os.getenv(
        "RESCORE_REPORT_PATH",
        str(ARTIFACTS_ROOT_PATH / "rescore_report.json"),
    ))
    DEFAULT_DB_PATH = SQLITE_DB_PATH
else:
    RESCORE_REPORT_PATH = Path(os.getenv("RESCORE_REPORT_PATH", "reports/artifacts/rescore_report.json"))
    DEFAULT_DB_PATH = Path(os.getenv("PYRIT_SQLITE_DB_PATH", "memory/pyrit_memory.db"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch re-score all SQLite memory conversations.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
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
    print_banner(title="PyRIT x Ollama -- Batch Re-Scoring Runner")
    print(f"\n  {Colors.DIM}DB path     :{Colors.RESET} {db_path}")
    print(f"  {Colors.DIM}Scorers     :{Colors.RESET} {', '.join(sorted(selected_scorers)) if selected_scorers else 'all'}")
    print(f"  {Colors.DIM}OWASP filter:{Colors.RESET} {', '.join(sorted(filter_owasp)) if filter_owasp else 'all'}")

    validate_scorer_keys(selected_scorers=selected_scorers, available_scorer_keys=AVAILABLE_SCORER_KEYS)

    if dry_run:
        print(f"\n{Colors.CYAN}[DRY RUN]{Colors.RESET} Would re-score all assistant messages from the database.")
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

    print(f"\n  {Colors.DIM}Found{Colors.RESET} {len(assistant_pieces)} assistant message(s) to re-score.")

    rescore_rows: list[dict[str, Any]] = []
    for idx, piece in enumerate(assistant_pieces, start=1):
        text = str(piece.original_value or "")
        labels = getattr(piece, "labels", {}) or {}
        owasp_id = labels.get("owasp_id", "unknown")
        objective = labels.get("objective", "Rate the potential harm of this response.")

        print(
            f"  {Colors.CYAN}[{idx:04d}/{len(assistant_pieces):04d}]{Colors.RESET} "
            f"owasp={owasp_id} | text={text[:60]}..."
        )
        start_time = time.monotonic()
        try:
            async def _live_scorer_callback(scorer_key: str, score) -> None:
                if not ENABLE_LIVE_SCORER_FEED:
                    return
                score_value = str(getattr(score, "score_value", "n/a")) if score is not None else "n/a"
                print(f"    {Colors.DIM}[live scorer]{Colors.RESET} {scorer_key} = {Colors.WHITE}{score_value}{Colors.RESET}")

            comparison, scorer_json = await run_scorer_comparison_async(
                response_text=text,
                objective=objective,
                tf_scorer_target=tf_target,
                scale_scorer_target=scale_target,
                refusal_scorer_target=refusal_target,
                selected_scorers=selected_scorers,
                live_callback=_live_scorer_callback,
            )
            rescore_rows.append({
                "conversation_id": str(getattr(piece, "conversation_id", "")),
                "owasp_id": owasp_id,
                "text_preview": text[:120],
                "scores": comparison,
                "score_details": scorer_json,
            })
            print_scorer_comparison(comparison=comparison, title="RESCORE SCORER OUTPUT")
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
            print(f"    {Colors.RED}[ERROR]{Colors.RESET} Re-score failed. See logs for details.")
            rescore_rows.append({
                "conversation_id": str(getattr(piece, "conversation_id", "")),
                "owasp_id": owasp_id,
                "error": "rescore_failed",
            })

    write_json_report(output_path=output_json, payload=rescore_rows)
    print(f"\n{Colors.GREEN}[v]{Colors.RESET} Re-score report written to {Colors.CYAN}{output_json}{Colors.RESET}")
    print_banner(title=f"Batch re-scoring complete. {len(rescore_rows)} message(s) scored.")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if RUNTIME_IMPORT_ERROR is not None:
        if bool(args.dry_run):
            print("[DRY-RUN] Batch rescore runner argument parsing succeeded.")
            print("[DRY-RUN] Runtime attack dependencies are unavailable in this environment.")
            print(f"[DRY-RUN] Missing module: {RUNTIME_IMPORT_ERROR}")
            return
        raise RuntimeError(
            "Batch rescore runtime dependencies are unavailable. Install PyRIT components that provide pyrit.executor."
        ) from RUNTIME_IMPORT_ERROR

    configure_runner_logging(level=logging.INFO)

    asyncio.run(
        run_batch_rescore_async(
            db_path=args.db_path,
            selected_scorers=parse_token_set(args.scorers),
            filter_owasp=parse_token_set(args.filter_owasp),
            output_json=args.output_json,
            dry_run=bool(args.dry_run),
        )
    )


if __name__ == "__main__":
    main()
