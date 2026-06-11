"""Central attack-mode workflow dispatcher for security-evaluator runners."""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path

from redteam_runner.reporting_ops import build_run_artifacts_root, build_run_report_paths


ARTIFACTS_ROOT_PATH = Path(os.getenv("ARTIFACTS_ROOT_PATH", "reports")).resolve()
MAX_TURNS = int(os.getenv("PYRIT_MAX_TURNS", "4"))
SQLITE_DB_PATH = Path(
    os.getenv("PYRIT_SQLITE_DB_PATH", str((ARTIFACTS_ROOT_PATH / "pyrit_ollama_demo.db").resolve()))
).resolve()


def _maybe_generate_report(
    *,
    should_generate_report: bool,
    run_paths: dict[str, Path],
    output_html: Path | None,
    output_md: Path | None,
    output_json: Path | None,
    open_report: bool,
) -> Path | None:
    if not should_generate_report:
        return None

    from utils.generate_html_report import generate_html_report

    default_html = run_paths["run_report_html"]
    output_path = generate_html_report(
        scorer_json_path=run_paths["scorer_outputs_json"],
        cases_dir=run_paths["cases_root"],
        run_report_path=run_paths["run_report_json"],
        output_html=output_html or default_html,
        output_md=output_md,
        output_json=output_json or run_paths["report_summary_json"],
    )
    if open_report:
        webbrowser.open(output_path.as_uri())
    return output_path


async def run_attack_mode_async(
    *,
    attack_mode: str,
    selected_converters: set[str] | None,
    selected_dataset_tokens: set[str] | None,
    selected_scenario_ids: set[str] | None,
    selected_scorers: set[str] | None,
    dry_run: bool,
    local_datasets_only: bool,
    tap_width: int | None,
    tap_depth: int | None,
    tap_branching_factor: int | None,
    max_backtracks: int | None,
    max_turns: int | None,
    max_seeds: int | None,
    filter_owasp: set[str] | None,
    output_json: Path | None,
    output_html: Path | None,
    output_md: Path | None,
    open_report: bool,
    turn_mode: str,
) -> Path | None:
    """Dispatch selected attack mode via the modular attacks/report runners.

    Attack-mode quick guide:
    - redteam: Full OWASP multi-turn red-team workflow. Use for broad end-to-end evaluation.
    - tap: Tree-of-Attacks with Pruning. Use for branching jailbreak exploration and depth search.
    - crescendo: Escalating multi-turn attack with backtracking. Use for gradual pressure tests.
    - xpia: Cross-Prompt Injection simulation. Use for indirect prompt-injection scenarios.
    - baseline: Prompt-only compliance scan (no attacker). Use as a control/baseline comparison.
    - rescore: Re-score existing memory records. Use after scorer changes without re-running attacks.
    - report: Generate HTML/Markdown outputs from artifacts. Use for stakeholder reporting.
    """
    should_generate_report = not dry_run and attack_mode != "report"
    is_multi_turn_mode = attack_mode in {"redteam", "tap", "crescendo"}
    if turn_mode == "multi" and not is_multi_turn_mode and attack_mode not in {"report", "rescore"}:
        raise ValueError(
            "turn-mode 'multi' requires a multi-turn attack mode: redteam, tap, or crescendo."
        )

    redteam_max_turns_override = 1 if turn_mode == "single" and attack_mode == "redteam" else max_turns
    tap_depth_override = 1 if turn_mode == "single" and attack_mode == "tap" else tap_depth
    crescendo_max_turns_override = 1 if turn_mode == "single" and attack_mode == "crescendo" else max_turns

    run_root = build_run_artifacts_root(
        attack_mode=attack_mode,
        dataset_names=sorted(selected_dataset_tokens) if selected_dataset_tokens else ["all_datasets"],
        scorer_names=sorted(selected_scorers) if selected_scorers else ["all_scorers"],
    )
    run_paths = build_run_report_paths(run_root=run_root)

    if dry_run and attack_mode != "report":
        print("[DRY-RUN] Attack mode validation successful.")
        print(f"[DRY-RUN] mode={attack_mode}")
        print(f"[DRY-RUN] datasets={sorted(selected_dataset_tokens) if selected_dataset_tokens else ['all_datasets']}")
        print(f"[DRY-RUN] scorers={sorted(selected_scorers) if selected_scorers else ['all_scorers']}")
        print(f"[DRY-RUN] converters={sorted(selected_converters) if selected_converters else ['default_or_all']}")
        return None

    # redteam: Full orchestration against OWASP scenarios using shared datasets,
    # converters, scorers, retries, and reporting. Choose this for primary runs.
    if attack_mode == "redteam":
        from attacks.redteam_attack_runner import run_redteam_suite_async

        await run_redteam_suite_async(
            selected_converters=selected_converters,
            selected_dataset_tokens=selected_dataset_tokens,
            selected_scorers=selected_scorers,
            dry_run=dry_run,
            local_datasets_only=local_datasets_only,
            max_turns_override=redteam_max_turns_override,
            report_root=run_root,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # tap: Tree-of-Attacks with Pruning; explores multiple adversarial branches
    # and prunes weak paths. Choose when you need wider/deeper jailbreak search.
    if attack_mode == "tap":
        from attacks.tap_attack_runner import run_tap_suite_async

        await run_tap_suite_async(
            selected_scenario_ids=selected_scenario_ids,
            selected_dataset_names=selected_dataset_tokens,
            selected_scorers=selected_scorers,
            width=tap_width or int(os.getenv("TAP_WIDTH", "3")),
            branching_factor=tap_branching_factor or int(os.getenv("TAP_BRANCHING_FACTOR", "2")),
            depth=tap_depth_override or int(os.getenv("TAP_DEPTH", "5")),
            dry_run=dry_run,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # crescendo: Gradual escalation with configurable backtracking and turn limits.
    # Choose when testing persistence and conversational pressure over time.
    if attack_mode == "crescendo":
        from attacks.crescendo_attack_runner import run_crescendo_suite_async

        await run_crescendo_suite_async(
            selected_scenario_ids=selected_scenario_ids,
            selected_dataset_names=selected_dataset_tokens,
            selected_scorers=selected_scorers,
            max_backtracks=max_backtracks or int(os.getenv("CRESCENDO_MAX_BACKTRACKS", "5")),
            max_turns=crescendo_max_turns_override or int(os.getenv("CRESCENDO_MAX_TURNS", str(MAX_TURNS))),
            dry_run=dry_run,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # xpia: Cross-Prompt Injection Attack simulation for hidden/indirect
    # instruction channels. Choose for LLM02/LLM08-style injection risks.
    if attack_mode == "xpia":
        from attacks.xpia_attack_runner import run_xpia_suite_async

        await run_xpia_suite_async(
            selected_scenario_ids=selected_scenario_ids,
            selected_dataset_tokens=selected_dataset_tokens,
            dry_run=dry_run,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # baseline: Sends prompts without an adversarial attacker to measure default
    # model behavior. Choose as a control for comparing attack uplift.
    if attack_mode == "baseline":
        from attacks.baseline_scan_runner import run_baseline_suite_async

        await run_baseline_suite_async(
            selected_scenario_ids=selected_scenario_ids,
            selected_dataset_names=selected_dataset_tokens,
            selected_scorers=selected_scorers,
            max_seeds=max_seeds if max_seeds is not None else int(os.getenv("BASELINE_MAX_SEEDS", "0")),
            dry_run=dry_run,
            report_root=run_root,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # rescore: Re-runs selected scorers against stored conversations in SQLite.
    # Choose when scorer logic/models change and you want fast recomputation.
    if attack_mode == "rescore":
        from attacks.batch_rescore_runner import run_batch_rescore_async

        default_output = Path(os.getenv("RESCORE_REPORT_PATH", str(run_root / "rescore_report.json")))
        await run_batch_rescore_async(
            db_path=SQLITE_DB_PATH,
            selected_scorers=selected_scorers,
            filter_owasp=filter_owasp,
            output_json=output_json or default_output,
            dry_run=dry_run,
        )
        return _maybe_generate_report(
            should_generate_report=should_generate_report,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=None,
            open_report=open_report,
        )

    # report: Produces human-readable artifacts from prior run outputs.
    # Choose for HTML/Markdown summaries and sharing results.
    if attack_mode == "report":
        return _maybe_generate_report(
            should_generate_report=True,
            run_paths=run_paths,
            output_html=output_html,
            output_md=output_md,
            output_json=output_json,
            open_report=open_report,
        )

    raise ValueError(f"Unsupported attack mode: {attack_mode}")
