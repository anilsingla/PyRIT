#!/usr/bin/env python3
"""Entrypoint for the modular OWASP Ollama red-team runner.

Supports multiple attack modes and optional selection of converters, datasets,
scorers, and scenarios.  Run with --help for full option list.

Attack modes
------------
redteam    Default. Multi-turn adversarial RedTeamingAttack (all 10 OWASP scenarios).
tap        Tree-of-Attacks with Pruning - branching adversarial search.
crescendo  Crescendo - escalating multi-turn with automatic backtracking.
xpia       Cross-Prompt Injection Attack - hidden instruction injection.
baseline   PromptSendingAttack - no attacker, raw seeds only (compliance baseline).

Utility modes
-------------
rescore    Re-score all existing SQLite conversations without re-running attacks.
report     Generate HTML / Markdown report from existing run artifacts.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Dual output and color tools
from utils.output_tools import setup_logging

_LOG = logging.getLogger(__name__)

ATTACK_MODES = ("redteam", "tap", "crescendo", "xpia", "baseline", "rescore", "report")
BANKING_DATASET_PATH = (
  Path(__file__).resolve().parents[2] / "custom_datasets" / "banking_app_security_dataset.json"
).resolve()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PyRIT x Ollama - OWASP LLM red-team suite for adversarial red-teaming.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES
========

  # Quick baseline test (default)
  python scripts/app/main.py --dry-run --local-datasets-only

  # Red-team with harmbench dataset
  python scripts/app/main.py --attack-mode redteam --dry-run --local-datasets-only

  # Single-turn attack with specific converters
  python scripts/app/main.py --attack-mode redteam --turn-mode single \\
    --converters base64,leetspeak --dry-run

  # Multi-turn attack with all converters
  python scripts/app/main.py --attack-mode redteam --turn-mode multi \\
    --all-converters --all-datasets --all-scorers

  # Display converter selection guide
  python scripts/app/main.py --converter-info

  # Display detailed help with all available options
  python scripts/app/main.py --detailed-help

FOR MORE INFORMATION
====================
  Use: --detailed-help    Show comprehensive option documentation
       --converter-info    Show converter selection guide with benefits
       --help              Show this message with supported attacks/utilities
        """,
    )
    parser.add_argument(
        "--attack-mode",
        choices=ATTACK_MODES,
        default="baseline",
        help=(
            "Attack strategy: 'redteam' (multi-turn adversarial, all OWASP), "
            "'tap' (tree-of-attacks), 'crescendo' (escalating), "
            "'xpia' (injection), 'baseline' (compliance scan). Default: baseline"
        ),
    )
    parser.add_argument(
        "--turn-mode",
        choices=("single", "multi"),
        default=None,
        help=(
            "Single-turn (max_turns=1, fast) or multi-turn conversations. "
            "Env fallback: PYRIT_ATTACK_TURN_MODE. Default: single"
        ),
    )
    parser.add_argument(
        "--converters",
        nargs="*",
        default=[],
        help=(
            "Converter keys for text obfuscation (space- or comma-separated). "
            "OPTIONS: base64, rot13, caesar, atbash, flip, leetspeak, unicode_confusable, "
            "string_join, char_swap, emoji, random_caps, tone_persuasive, variation, translation_french. "
            "Omit to use all stateless converters by default."
        ),
    )
    parser.add_argument(
        "--all-converters",
        action="store_true",
        help="Force use of all available converters including LLM-based ones (overrides default converter selection).",
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=[],
        help=(
            "Dataset names or .json/.yaml/.yml/.prompt file paths. "
            "Omit to use PYRIT_DEFAULT_DATASETS when set; otherwise all available datasets."
        ),
    )
    parser.add_argument(
        "--all-datasets",
        action="store_true",
        help="Force use of all available datasets (overrides default dataset selection).",
    )
    parser.add_argument(
        "--scorers",
        nargs="*",
        default=[],
        help=(
            "Scorer keys to run. Omit to use PYRIT_DEFAULT_SCORERS when set; otherwise compute all. "
            "Keys: substring, self_ask_true_false, self_ask_scale, "
            "scale_threshold_0_7, refusal, compliance_inverted_refusal."
        ),
    )
    parser.add_argument(
        "--all-scorers",
        action="store_true",
        help="Force use of all available scorers (overrides default scorer selection).",
    )
    parser.add_argument(
        "--scenarios",
        nargs="*",
        default=[],
        help="OWASP IDs to run (e.g. LLM01 LLM02). Omit for all. (tap/crescendo/xpia/baseline only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the execution plan without running any attacks.",
    )
    parser.add_argument(
        "--local-datasets-only",
        action="store_true",
        help="Redteam mode: use only datasets already available locally/in-memory and skip remote provider fetch.",
    )
    parser.add_argument(
        "--converter-info",
        action="store_true",
        help="Display comprehensive converter selection guide with descriptions and use cases, then exit.",
    )
    parser.add_argument(
        "--detailed-help",
        action="store_true",
        help="Display comprehensive CLI help: attack modes, option categories, environment variables, examples, then exit.",
    )
    # TAP-specific
    parser.add_argument("--tap-width", type=int, default=None, help="TAP: number of attack branches.")
    parser.add_argument("--tap-depth", type=int, default=None, help="TAP: max tree depth per scenario.")
    parser.add_argument("--tap-branching-factor", type=int, default=None, help="TAP: child nodes per branch.")
    # Crescendo-specific
    parser.add_argument("--max-backtracks", type=int, default=None, help="Crescendo: max backtrack count.")
    parser.add_argument("--max-turns", type=int, default=None, help="Max conversation turns.")
    # Baseline-specific
    parser.add_argument("--max-seeds", type=int, default=None, help="Baseline: max seeds per scenario (0=unlimited).")
    # Rescore-specific
    parser.add_argument("--filter-owasp", nargs="*", default=[], help="Rescore: limit to OWASP IDs.")
    parser.add_argument("--output-json", type=Path, default=None, help="Rescore: output JSON path.")
    # Report-specific
    parser.add_argument("--output-html", type=Path, default=None, help="Report: output HTML path.")
    parser.add_argument("--output-md", type=Path, default=None, help="Report: output Markdown path.")
    parser.add_argument("--open", action="store_true", help="Report: open HTML in browser after generation.")
    return parser


def print_detailed_help() -> None:
    """Print comprehensive CLI help with all options, categories, environment variables, and examples."""
    help_text = """
================================================================================
|                      PyRIT x Ollama - OWASP Red-Team Suite                   |
|                           Comprehensive CLI Help                             |
================================================================================

ATTACK MODES (choose with --attack-mode)
----------------------------------------

  baseline      PromptSendingAttack compliance baseline (default).
                Single-turn, no attacker. Good for control/baseline comparisons.

  redteam       Multi-turn adversarial RedTeamingAttack.
                Tests all 10 OWASP LLM Top-10 scenarios with conversational attacks.
                Supports --turn-mode single|multi for 1-turn or N-turn conversations.

  tap           Tree-of-Attacks with Pruning - branching adversarial search.
                Multi-turn, explores jailbreak trees with width/depth/branching control.
                Options: --tap-width, --tap-depth, --tap-branching-factor

  crescendo     Crescendo - escalating multi-turn attack with automatic backtracking.
                Gradually increases adversarial pressure; backs off on failures.
                Option: --max-backtracks

  xpia          Cross-Prompt Injection Attack - hidden instruction injection.
                Single-turn injection-based attack simulating prompt mashup scenarios.

UTILITY MODES
-------------

  rescore       Re-score existing SQLite conversations without re-running attacks.
                Use after scorer changes. Reads from SQLITE_DB_PATH, exports JSON/CSV.

  report        Generate HTML/Markdown report from existing run artifacts.
                Reads scorer outputs and case reports, generates HTML + JSON summary.

MAIN OPTIONS
------------

  --turn-mode {single|multi}
                Single-turn (max_turns=1, conservative/fast) or multi-turn conversations.
                Only valid for redteam, tap, crescendo. Baseline/xpia are single-turn only.
                Env fallback: PYRIT_ATTACK_TURN_MODE (default: single)

  --converters [CONV ...]
                Converter keys for prompt obfuscation (space or comma-separated).
                14 available: 11 stateless (base64, rot13, caesar, ...) + 3 LLM-based (tone_persuasive, ...).
                Env fallback: PYRIT_DEFAULT_CONVERTERS
                See: --converter-info for detailed descriptions

  --all-converters
                Use all 14 converters instead of default selection.
                Env fallback: PYRIT_USE_ALL_CONVERTERS (1|true|yes)

  --datasets [DATASET ...]
                Seed dataset names (space or comma-separated).
                Examples: harmbench, pyrit_example_dataset, beaver_tails, toxic_chat.
                50+ available datasets. Env fallback: PYRIT_DEFAULT_DATASETS (default: harmbench)

  --all-datasets
                Use all 50+ available datasets instead of default.
                Env fallback: PYRIT_USE_ALL_DATASETS (1|true|yes)

  --scorers [SCORER ...]
                Scorer keys for LLM response evaluation (space or comma-separated).
                Available: substring, self_ask_true_false, self_ask_scale,
                          scale_threshold_0_7, refusal, compliance_inverted_refusal
                Env fallback: PYRIT_DEFAULT_SCORERS (default: self_ask_true_false)

  --all-scorers
                Run all 6+ available scorers simultaneously.
                Env fallback: PYRIT_USE_ALL_SCORERS (1|true|yes)

  --scenarios [OWASP_ID ...]
                OWASP LLM Top-10 vulnerability IDs to attack (space or comma-separated).
                Examples: LLM01 LLM02 LLM03 ... LLM10 for all.
                LLM01=Prompt Injection, LLM02=Insecure Output, LLM03=Training Poisoning, etc.
                Omit for all 10. (tap/crescendo/xpia/baseline only)

EXECUTION CONTROL
-----------------

  --dry-run
                Print execution plan with dataset/converter/scenario counts, then exit.
                No prompts are sent; useful for quick validation before full run.

  --local-datasets-only
                Skip remote dataset provider fetches; use only locally-cached datasets.
                Faster initialization, smaller memory footprint.

REPORT & OUTPUT OPTIONS (report mode only)
-------------------------------------------

  --output-html PATH
                Write HTML report to custom path. Default: reports/run_report.html

  --output-md PATH
                Write Markdown report to custom path.

  --output-json PATH
                Write JSON report to custom path. Default: reports/report_summary.json

  --open
                Open generated HTML report in browser after generation.

ADDITIONAL AUTO-GENERATED REPORTS
---------------------------------

  If a run uses all datasets, all scorers, or both, an additional per-run
  comparison artifact is generated automatically:

    all_selection_comparison_report.json

  This report includes side-by-side dataset and scorer comparison aggregates
  for that run and is written next to other run artifacts.

TAP-SPECIFIC OPTIONS (--attack-mode tap)
-----------------------------------------

  --tap-width INT           Number of attack branches (default: PyRIT's default)
  --tap-depth INT           Max tree depth per scenario (default: PyRIT's default)
  --tap-branching-factor INT  Child nodes per branch (default: PyRIT's default)

CRESCENDO-SPECIFIC OPTIONS (--attack-mode crescendo)
-----------------------------------------------------

  --max-backtracks INT      Maximum backtrack count (default: PyRIT's default)
  --max-turns INT           Max conversation turns (default: 4)

BASELINE-SPECIFIC OPTIONS (--attack-mode baseline)
---------------------------------------------------

  --max-seeds INT           Max seeds per scenario (0=unlimited, default: unlimited)

RESCORE-SPECIFIC OPTIONS (--attack-mode rescore)
--------------------------------------------------

  --filter-owasp [ID ...]   Limit re-scoring to specific OWASP scenarios

INFORMATION OPTIONS
-------------------

  --converter-info
                Display converter selection guide with all 14 converters,
                categories, use cases, benefits, and examples. Then exit.

  --detailed-help
                Display this comprehensive help. Then exit.

  --help
                Display basic help with attack modes and usage summary.

ENVIRONMENT VARIABLES (Config Precedence: CLI > Env > Code Defaults)
---------------------------------------------------------------------

  PYRIT_ATTACK_TURN_MODE        Turn mode selection: "single" | "multi" (default: single)
  PYRIT_DEFAULT_DATASETS        Default dataset selection: "harmbench,pyrit_example_dataset" (default: harmbench)
  PYRIT_DEFAULT_CONVERTERS      Default converters: "base64,leetspeak,emoji" (default: all stateless)
  PYRIT_DEFAULT_SCORERS         Default scorers: "self_ask_true_false,refusal" (default: self_ask_true_false)
  PYRIT_USE_ALL_DATASETS        Force all datasets: "1" | "true" | "yes" (default: false)
  PYRIT_USE_ALL_CONVERTERS      Force all converters: "1" | "true" | "yes" (default: false)
  PYRIT_USE_ALL_SCORERS         Force all scorers: "1" | "true" | "yes" (default: false)
  PYRIT_DEFAULT_SCENARIOS       Default OWASP scenarios: "LLM01,LLM02,LLM03" (default: all 10)
  PYRIT_DEFAULT_FILTER_OWASP    Rescore: filter scenarios by OWASP IDs
  RUNNER_LOG_PATH               Logging file path (default: logs/pyrit_runner.log)

EXAMPLES
--------

  # Quick dry-run with defaults (harmbench, self_ask_true_false, single-turn)
  python scripts/app/main.py --dry-run --local-datasets-only

  # Red-team all 10 OWASP with specific converters and single-turn
  python scripts/app/main.py --attack-mode redteam --turn-mode single \\
    --converters base64,leetspeak,emoji --dry-run

  # Multi-turn red-team with all datasets and converters
  python scripts/app/main.py --attack-mode redteam --turn-mode multi \\
    --all-datasets --all-converters --all-scorers

  # Baseline compliance scan on harmbench (default)
  python scripts/app/main.py --attack-mode baseline --dry-run

  # TAP with custom depth and branching
  python scripts/app/main.py --attack-mode tap --turn-mode multi \\
    --tap-depth 3 --tap-width 5 --tap-branching-factor 2 --dry-run

  # Crescendo with max backtracks
  python scripts/app/main.py --attack-mode crescendo \\
    --max-backtracks 5 --max-turns 10 --dry-run

  # Re-score existing conversations with new scorers
  python scripts/app/main.py --attack-mode rescore \\
    --scorers substring,refusal --filter-owasp LLM01 LLM02

  # Display converter guide
  python scripts/app/main.py --converter-info

BEST PRACTICES
--------------

  1. Start with --dry-run to validate configuration before running full attacks.
  2. Use --local-datasets-only to avoid network delays during initialization.
  3. For quick testing: combine simple converters (base64, leetspeak) with limited datasets.
  4. For comprehensive evaluation: use --all-converters, --all-datasets, --all-scorers.
  5. Set environment variables in .env file for consistent defaults across runs.
  6. Use --turn-mode single for faster baseline; --turn-mode multi for adversarial depth.

TROUBLESHOOTING
---------------

  - "turn-mode 'multi' requires a multi-turn attack mode" -> Use redteam/tap/crescendo, not baseline/xpia
  - "No scenarios matched" -> Check --scenarios format (e.g., LLM01, not LLM01, with space)
  - Slow initialization -> Use --local-datasets-only to skip remote dataset fetches
  - Out of memory -> Use --converters sparingly, reduce --tap-width, or use --max-seeds

================================================================================
    """
    print(help_text)


def print_converter_guide() -> None:
    """Print lightweight converter selection guide without importing heavy runtime modules."""
    guide_text = """
CONVERTER GUIDE
===============

Stateless converters (fast):
  base64, rot13, caesar, atbash, flip, leetspeak, unicode_confusable,
  string_join, char_swap, emoji, random_caps

LLM-based converters (slower, semantic rewrites):
  tone_persuasive, variation, translation_french

When to use what:
  - Encoding/obfuscation testing: base64, rot13, caesar, atbash
  - Typo/noise robustness: char_swap, random_caps, string_join
  - Semantic drift and paraphrase: variation, tone_persuasive
  - Multilingual policy coverage: translation_french

Selection tips:
  - Start small: --converters base64,leetspeak
  - Broader coverage: --all-converters
  - Fastest runs: use stateless converters only
"""
    print(guide_text)



def main() -> None:
    """Dispatch to the selected attack mode."""
    parser = _build_parser()
    args = parser.parse_args()

    # Handle --converter-info flag separately (exits after display)
    if getattr(args, "converter_info", False):
        print_converter_guide()
        sys.exit(0)

    # Handle --detailed-help flag separately (exits after display)
    if getattr(args, "detailed_help", False):
        print_detailed_help()
        sys.exit(0)

    # Setup dual output and color logging for real execution paths
    dual_writer = setup_logging()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = dual_writer
    sys.stderr = dual_writer

    # Import workflow after early-exit checks; keep logging robust even if optional runtime deps are unavailable.
    from redteam_runner.workflow import run_attack_mode_async
    try:
      from redteam_runner.env_config import configure_runner_logging

      configure_runner_logging(level=logging.INFO)
    except Exception:
      logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        force=True,
      )

    def _env_bool(*, name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}

    def _tokens(*, values: list[str], env_var: str, default_literal: str = "") -> set[str] | None:
        source_values = values
        if not source_values:
            source_values = [os.getenv(env_var, default_literal)]
        flat = {t.strip() for v in source_values for t in v.split(",") if t.strip()}
        return flat or None

    use_all_datasets = bool(args.all_datasets) or _env_bool(name="PYRIT_USE_ALL_DATASETS", default=False)
    use_all_scorers = bool(args.all_scorers) or _env_bool(name="PYRIT_USE_ALL_SCORERS", default=False)
    use_all_converters = bool(args.all_converters) or _env_bool(name="PYRIT_USE_ALL_CONVERTERS", default=False)
    turn_mode = str(args.turn_mode or os.getenv("PYRIT_ATTACK_TURN_MODE", "single")).strip().lower()
    if turn_mode not in {"single", "multi"}:
        raise ValueError("Invalid turn mode. Use 'single' or 'multi'.")

    selected_dataset_tokens = (
        None
        if use_all_datasets
      else _tokens(
        values=args.datasets,
        env_var="PYRIT_DEFAULT_DATASETS",
        default_literal=str(BANKING_DATASET_PATH),
      )
    )
    selected_scorers = (
        None
        if use_all_scorers
        else _tokens(values=args.scorers, env_var="PYRIT_DEFAULT_SCORERS", default_literal="self_ask_true_false")
    )
    selected_converters = (
        None
        if use_all_converters
        else _tokens(values=args.converters, env_var="PYRIT_DEFAULT_CONVERTERS")
    )

    mode = args.attack_mode
    _LOG.info("Selected attack mode: %s", mode)

    try:
        asyncio.run(
            run_attack_mode_async(
                attack_mode=mode,
                selected_converters=selected_converters,
                selected_dataset_tokens=selected_dataset_tokens,
                selected_scenario_ids=_tokens(values=args.scenarios, env_var="PYRIT_DEFAULT_SCENARIOS"),
                selected_scorers=selected_scorers,
                dry_run=bool(args.dry_run),
                local_datasets_only=bool(args.local_datasets_only),
                tap_width=args.tap_width,
                tap_depth=args.tap_depth,
                tap_branching_factor=args.tap_branching_factor,
                max_backtracks=args.max_backtracks,
                max_turns=args.max_turns,
                max_seeds=args.max_seeds,
                filter_owasp=_tokens(values=args.filter_owasp, env_var="PYRIT_DEFAULT_FILTER_OWASP"),
                output_json=args.output_json,
                output_html=args.output_html,
                output_md=args.output_md,
                open_report=bool(args.open),
                turn_mode=turn_mode,
            )
        )
    except KeyboardInterrupt:
        _LOG.warning("Interrupted by user")
        sys.exit(130)
    except Exception:
        _LOG.exception("Runner terminated with an unhandled error")
        sys.exit(1)
    finally:
      # Restore original stdout/stderr and close log file
      sys.stdout = original_stdout
      sys.stderr = original_stderr
      dual_writer.close()


if __name__ == "__main__":
    main()
