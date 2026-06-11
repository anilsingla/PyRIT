#!/usr/bin/env python3
"""HTML / Markdown run report generator.

Reads the scorer outputs JSON and per-case JSON reports produced by the runner
and generates a self-contained HTML report with:

  - Per-OWASP-scenario summary table (pass/fail, weighted confidence, scorer breakdown)
  - Conversation transcript per case
  - Side-by-side scorer comparison per case
  - Aggregate statistics section

    python scripts/app/utils/generate_html_report.py

CLI flags:
    --scorer-json     Path to scorer_outputs.json (default: from env)
    --cases-dir       Path to per-case reports directory
    --run-report      Path to run_report.json (default: from env)
    --output-html     Output HTML path (default: reports/run_report.html)
    --output-md       Optional Markdown path
    --open            Open the report in the default browser after creation
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAMPLE_ROOT_PATH = Path(__file__).resolve().parents[3]
ARTIFACTS_ROOT_PATH = SAMPLE_ROOT_PATH / "reports"
REPORTS_ROOT_PATH = ARTIFACTS_ROOT_PATH / "cases"
SCORER_OUTPUTS_JSON_PATH = ARTIFACTS_ROOT_PATH / "scorer_outputs.json"
RUN_REPORT_JSON_PATH = ARTIFACTS_ROOT_PATH / "run_report.json"

_LOG = logging.getLogger(__name__)

HTML_REPORT_PATH = Path(os.getenv(
    "HTML_REPORT_PATH",
    str(ARTIFACTS_ROOT_PATH / "run_report.html"),
))
MD_REPORT_PATH = Path(os.getenv(
    "MD_REPORT_PATH",
    str(ARTIFACTS_ROOT_PATH / "run_report.md"),
))
REPORT_SUMMARY_JSON_PATH = Path(os.getenv(
    "REPORT_SUMMARY_JSON_PATH",
    str(ARTIFACTS_ROOT_PATH / "report_summary.json"),
))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate HTML/Markdown report from run artifacts.")
    parser.add_argument("--scorer-json", type=Path, default=SCORER_OUTPUTS_JSON_PATH)
    parser.add_argument("--cases-dir", type=Path, default=REPORTS_ROOT_PATH)
    parser.add_argument("--run-report", type=Path, default=RUN_REPORT_JSON_PATH)
    parser.add_argument("--output-html", type=Path, default=HTML_REPORT_PATH)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=REPORT_SUMMARY_JSON_PATH)
    parser.add_argument("--open", action="store_true", help="Open HTML in browser after generation.")
    return parser


def _load_json(path: Path) -> Any:
    if not path.exists():
        _LOG.warning("JSON input not found: %s", path)
        return None
    try:
        # Use utf-8-sig to support BOM-prefixed JSON files (common on Windows/PowerShell).
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        _LOG.exception("Failed to parse JSON file: %s", path)
        return None


def _outcome_badge(outcome: str) -> str:
    colour = "#22c55e" if "success" in outcome.lower() or "achieved" in outcome.lower() else "#ef4444"
    return f'<span style="background:{colour};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.8em">{html.escape(outcome)}</span>'


def _build_scenario_rows(scorer_rows: list[dict]) -> tuple[str, str]:
    """Build HTML table rows and Markdown rows from scorer output rows."""
    html_rows: list[str] = []
    md_rows: list[str] = []

    grouped: dict[str, list[dict]] = {}
    for row in scorer_rows:
        owasp_id = row.get("owasp_id", "unknown")
        grouped.setdefault(owasp_id, []).append(row)

    for owasp_id, rows in sorted(grouped.items()):
        total = len(rows)
        passed = sum(1 for r in rows if "success" in str(r.get("outcome", "")).lower() or "achieved" in str(r.get("outcome", "")).lower())
        rate = f"{(passed / total * 100):.0f}%" if total else "n/a"

        sample = rows[0]
        weighted = sample.get("weighted_majority", "n/a")
        confidence = sample.get("weighted_confidence", "n/a")
        dataset = sample.get("dataset", "n/a")
        converter = sample.get("converter", "n/a")

        html_rows.append(
            f"<tr>"
            f"<td><strong>{html.escape(owasp_id)}</strong></td>"
            f"<td>{html.escape(dataset)}</td>"
            f"<td>{html.escape(converter)}</td>"
            f"<td>{passed}/{total}</td>"
            f"<td>{rate}</td>"
            f"<td>{html.escape(str(weighted))}</td>"
            f"<td>{html.escape(str(confidence))}</td>"
            f"</tr>"
        )
        md_rows.append(f"| {owasp_id} | {dataset} | {converter} | {passed}/{total} | {rate} | {weighted} | {confidence} |")

    return "\n".join(html_rows), "\n".join(md_rows)


def _get_score_payloads_for_row(*, row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return detailed scorer payloads for a row from either `scores` or `score_details`."""
    for key in ("scores", "score_details"):
        value = row.get(key)
        if isinstance(value, dict):
            normalized: dict[str, dict[str, Any]] = {}
            for scorer_key, payload in value.items():
                if isinstance(payload, dict):
                    normalized[str(scorer_key)] = payload
            return normalized
    return {}


def _score_value_as_text(*, payload: dict[str, Any]) -> str:
    """Normalize score value to text for summaries and downstream payloads."""
    raw = payload.get("score_value")
    return "n/a" if raw is None else str(raw)


def _build_dataset_scorer_hierarchy(
    scorer_rows: list[dict[str, Any]],
) -> tuple[str, str, dict[str, dict[str, Any]]]:
    """Build dataset -> scorer hierarchy for report rendering and JSON export."""
    hierarchy: dict[str, dict[str, Any]] = {}

    for row in scorer_rows:
        dataset = str(row.get("dataset") or "unknown_dataset")
        dataset_entry = hierarchy.setdefault(dataset, {"total_cases": 0, "scorers": {}})
        dataset_entry["total_cases"] += 1

        for scorer_key, payload in _get_score_payloads_for_row(row=row).items():
            scorer_map = dataset_entry["scorers"]
            scorer_entry = scorer_map.setdefault(
                scorer_key,
                {
                    "cases_scored": 0,
                    "true_count": 0,
                    "false_count": 0,
                    "numeric_count": 0,
                    "missing_count": 0,
                },
            )
            scorer_entry["cases_scored"] += 1

            score_value = str(payload.get("score_value", "")).strip().lower()
            if score_value in {"true", "1", "yes", "y"}:
                scorer_entry["true_count"] += 1
            elif score_value in {"false", "0", "no", "n"}:
                scorer_entry["false_count"] += 1
            elif score_value in {"", "none", "null", "n/a"}:
                scorer_entry["missing_count"] += 1
            else:
                try:
                    float(score_value)
                    scorer_entry["numeric_count"] += 1
                except Exception:
                    scorer_entry["missing_count"] += 1

    html_rows: list[str] = []
    md_rows: list[str] = []
    sorted_hierarchy: dict[str, dict[str, Any]] = {}
    for dataset in sorted(hierarchy):
        source = hierarchy[dataset]
        scorer_rows = {}
        for scorer_key in sorted(source["scorers"]):
            scorer_rows[scorer_key] = source["scorers"][scorer_key]
            entry = source["scorers"][scorer_key]
            html_rows.append(
                "<tr>"
                f"<td>{html.escape(dataset)}</td>"
                f"<td>{html.escape(scorer_key)}</td>"
                f"<td>{entry['cases_scored']}</td>"
                f"<td>{entry['true_count']}</td>"
                f"<td>{entry['false_count']}</td>"
                f"<td>{entry['numeric_count']}</td>"
                f"<td>{entry['missing_count']}</td>"
                "</tr>"
            )
            md_rows.append(
                f"| {dataset} | {scorer_key} | {entry['cases_scored']} | {entry['true_count']} | "
                f"{entry['false_count']} | {entry['numeric_count']} | {entry['missing_count']} |"
            )

        sorted_hierarchy[dataset] = {
            "total_cases": source["total_cases"],
            "scorers": scorer_rows,
        }

    return "\n".join(html_rows), "\n".join(md_rows), sorted_hierarchy


def _build_test_case_summaries(scorer_rows: list[dict[str, Any]]) -> tuple[str, str, list[dict[str, Any]]]:
    """Build per-test-case execution summary rows and JSON payload."""
    html_rows: list[str] = []
    md_rows: list[str] = []
    summaries: list[dict[str, Any]] = []

    for index, row in enumerate(scorer_rows, start=1):
        case_id = str(row.get("case_id") or row.get("conversation_id") or f"TC-{index:04d}")
        owasp_id = str(row.get("owasp_id") or "unknown")
        dataset = str(row.get("dataset") or "unknown")
        outcome = str(row.get("outcome") or row.get("status") or "unknown")
        weighted_majority = str(row.get("weighted_majority") or row.get("scores", {}).get("weighted_majority", "n/a"))
        weighted_confidence = str(row.get("weighted_confidence") or row.get("scores", {}).get("weighted_confidence", "n/a"))
        details = _get_score_payloads_for_row(row=row)
        scorer_values = {name: _score_value_as_text(payload=payload) for name, payload in details.items()}

        html_rows.append(
            "<tr>"
            f"<td>{html.escape(case_id)}</td>"
            f"<td>{html.escape(owasp_id)}</td>"
            f"<td>{html.escape(dataset)}</td>"
            f"<td>{_outcome_badge(outcome)}</td>"
            f"<td>{html.escape(weighted_majority)}</td>"
            f"<td>{html.escape(weighted_confidence)}</td>"
            "</tr>"
        )
        md_rows.append(
            f"| {case_id} | {owasp_id} | {dataset} | {outcome} | {weighted_majority} | {weighted_confidence} |"
        )

        summaries.append(
            {
                "test_case_id": case_id,
                "owasp_id": owasp_id,
                "dataset": dataset,
                "result": outcome,
                "weighted_majority": weighted_majority,
                "weighted_confidence": weighted_confidence,
                "scorers": scorer_values,
            }
        )

    return "\n".join(html_rows), "\n".join(md_rows), summaries


def _build_sqlite_import_rows(scorer_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build JSON rows compatible with import_scorer_json_to_memory.py (expects top-level `rows`)."""
    sqlite_rows: list[dict[str, Any]] = []
    for row in scorer_rows:
        scores = _get_score_payloads_for_row(row=row)
        if not scores:
            continue
        sqlite_rows.append(
            {
                "owasp_id": row.get("owasp_id"),
                "owasp_name": row.get("owasp_name"),
                "dataset": row.get("dataset"),
                "outcome": row.get("outcome", row.get("status")),
                "scores": scores,
            }
        )
    return sqlite_rows


def _build_all_selection_comparison_report(
    *,
    dataset_scorer_hierarchy: dict[str, dict[str, Any]],
    test_case_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build dataset/scorer comparison payload for all-selection runs."""
    dataset_results: dict[str, dict[str, int]] = {}
    scorer_value_counts: dict[str, dict[str, int]] = {}

    for case in test_case_summaries:
        dataset = str(case.get("dataset") or "unknown_dataset")
        result_text = str(case.get("result") or "unknown").lower()
        dataset_bucket = dataset_results.setdefault(dataset, {"total": 0, "success": 0, "failed": 0})
        dataset_bucket["total"] += 1
        if "success" in result_text or "achieved" in result_text:
            dataset_bucket["success"] += 1
        else:
            dataset_bucket["failed"] += 1

        scorer_map = case.get("scorers")
        if isinstance(scorer_map, dict):
            for scorer_name, value in scorer_map.items():
                scorer_bucket = scorer_value_counts.setdefault(str(scorer_name), {})
                value_key = str(value)
                scorer_bucket[value_key] = scorer_bucket.get(value_key, 0) + 1

    return {
        "dataset_comparison": dataset_results,
        "scorer_value_comparison": scorer_value_counts,
        "dataset_scorer_hierarchy": dataset_scorer_hierarchy,
        "test_case_count": len(test_case_summaries),
    }


def _css() -> str:
    return """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 24px; color: #1f2937; }
    h1 { border-bottom: 2px solid #6366f1; padding-bottom: 8px; }
    h2 { color: #4f46e5; margin-top: 2em; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }
    th { background: #6366f1; color: white; padding: 8px 12px; text-align: left; }
    td { padding: 7px 12px; border-bottom: 1px solid #e5e7eb; }
    tr:nth-child(even) { background: #f9fafb; }
    .meta { background: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 2em; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .meta dt { font-weight: 600; }
    details { margin-bottom: 1em; background: #f9fafb; padding: 8px 16px; border-radius: 6px; border: 1px solid #e5e7eb; }
    summary { cursor: pointer; font-weight: 600; }
    pre { background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 0.8em; }
    """


def _build_case_details(cases_dir: Path) -> tuple[str, str]:
    """Build collapsible case detail sections."""
    html_sections: list[str] = []
    md_sections: list[str] = []

    for owasp_dir in sorted(cases_dir.iterdir()) if cases_dir.exists() else []:
        if not owasp_dir.is_dir():
            continue
        for case_file in sorted(owasp_dir.glob("*.json")):
            case = _load_json(case_file)
            if not case:
                continue
            owasp_id = case.get("owasp_id", owasp_dir.name)
            outcome = str(case.get("outcome", "unknown"))
            objective = str(case.get("objective", ""))[:120]
            comparison = case.get("scorer_comparison", {})

            comparison_rows = "".join(
                f"<tr><td>{html.escape(k)}</td><td><code>{html.escape(str(v))}</code></td></tr>"
                for k, v in comparison.items()
            )

            html_sections.append(
                f"<details><summary>{html.escape(owasp_id)}  {case_file.stem}  {html.escape(outcome)}</summary>"
                f"<p><em>Objective:</em> {html.escape(objective)}</p>"
                f"<table><tr><th>Scorer</th><th>Result</th></tr>{comparison_rows}</table>"
                f"<pre>{html.escape(json.dumps(case, indent=2)[:2000])}</pre>"
                f"</details>"
            )
            md_sections.append(
                f"\n### {owasp_id}  {case_file.stem}\n"
                f"**Outcome**: {outcome}  \n**Objective**: {objective}\n\n"
                + "\n".join(f"- `{k}`: {v}" for k, v in comparison.items())
            )

    return "\n".join(html_sections), "\n".join(md_sections)


def generate_html_report(
    *,
    scorer_json_path: Path,
    cases_dir: Path,
    run_report_path: Path,
    output_html: Path,
    output_md: Path | None,
    output_json: Path,
) -> Path:
    """Build and write the HTML report; return the output path."""
    _LOG.info(
        "Generating report with scorer_json=%s cases_dir=%s run_report=%s",
        scorer_json_path,
        cases_dir,
        run_report_path,
    )
    scorer_payload = _load_json(scorer_json_path)
    if isinstance(scorer_payload, dict):
        rows_value = scorer_payload.get("rows", [])
        scorer_rows: list[dict] = [row for row in rows_value if isinstance(row, dict)] if isinstance(rows_value, list) else []
    elif isinstance(scorer_payload, list):
        scorer_rows = [row for row in scorer_payload if isinstance(row, dict)]
    else:
        scorer_rows = []
    run_meta: dict = _load_json(run_report_path) or {}

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    scenario_html, scenario_md = _build_scenario_rows(scorer_rows)
    hierarchy_html, hierarchy_md, dataset_scorer_hierarchy = _build_dataset_scorer_hierarchy(scorer_rows)
    testcase_html, testcase_md, test_case_summaries = _build_test_case_summaries(scorer_rows)
    sqlite_import_rows = _build_sqlite_import_rows(scorer_rows)
    cases_html, cases_md = _build_case_details(cases_dir)

    meta_html = "\n".join(
        f"<dt>{html.escape(str(k))}</dt><dd>{html.escape(str(v))}</dd>"
        for k, v in run_meta.items()
        if not isinstance(v, (dict, list))
    )

    meta_md = "\n".join(
        f"- **{k}**: {v}"
        for k, v in run_meta.items()
        if not isinstance(v, (dict, list))
    )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>PyRIT x Ollama  Red-Team Report</title>
  <style>{_css()}</style>
</head>
<body>
  <h1>PyRIT x Ollama  OWASP LLM Top-10 Red-Team Report</h1>
  <p>Generated: {generated_at}</p>

  <h2>Run Metadata</h2>
  <dl class="meta">{meta_html}</dl>

  <h2>Scenario Summary</h2>
  <table>
    <tr>
      <th>OWASP ID</th><th>Dataset</th><th>Converter</th>
      <th>Pass/Total</th><th>Pass Rate</th>
      <th>Weighted Majority</th><th>Weighted Confidence</th>
    </tr>
    {scenario_html}
  </table>

    <h2>Dataset -> Scorer Hierarchy</h2>
    <table>
        <tr>
            <th>Dataset</th><th>Scorer</th><th>Cases Scored</th>
            <th>True</th><th>False</th><th>Numeric</th><th>Missing</th>
        </tr>
        {hierarchy_html}
    </table>

    <h2>Per-Test-Case Execution Summary</h2>
    <table>
        <tr>
            <th>Test Case ID</th><th>OWASP ID</th><th>Dataset</th>
            <th>Result</th><th>Weighted Majority</th><th>Weighted Confidence</th>
        </tr>
        {testcase_html}
    </table>

  <h2>Case Details</h2>
  {cases_html or "<p><em>No per-case report files found in cases directory.</em></p>"}

</body>
</html>"""

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(full_html, encoding="utf-8")
    _LOG.info("HTML report written: %s", output_html)
    print(f"[v] HTML report written to {output_html}")

    run_configuration = run_meta.get("run_configuration") if isinstance(run_meta, dict) else None
    selected_datasets = run_configuration.get("selected_datasets") if isinstance(run_configuration, dict) else None
    selected_scorers = run_configuration.get("selected_scorers") if isinstance(run_configuration, dict) else None
    explicit_all_datasets = isinstance(selected_datasets, list) and len(selected_datasets) == 0
    explicit_all_scorers = isinstance(selected_scorers, list) and len(selected_scorers) == 0

    unique_scorer_count = len(
        {
            scorer_name
            for dataset_payload in dataset_scorer_hierarchy.values()
            for scorer_name in dataset_payload.get("scorers", {}).keys()
        }
    )
    inferred_all_datasets = len(dataset_scorer_hierarchy) > 1
    inferred_all_scorers = unique_scorer_count > 1

    using_all_datasets = explicit_all_datasets or inferred_all_datasets
    using_all_scorers = explicit_all_scorers or inferred_all_scorers

    all_selection_comparison_path: str | None = None
    if using_all_datasets or using_all_scorers:
        all_selection_payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "flags": {
                "using_all_datasets": using_all_datasets,
                "using_all_scorers": using_all_scorers,
                "explicit_all_datasets": explicit_all_datasets,
                "explicit_all_scorers": explicit_all_scorers,
                "inferred_all_datasets": inferred_all_datasets,
                "inferred_all_scorers": inferred_all_scorers,
            },
            "comparison": _build_all_selection_comparison_report(
                dataset_scorer_hierarchy=dataset_scorer_hierarchy,
                test_case_summaries=test_case_summaries,
            ),
        }
        all_selection_path = output_json.parent / "all_selection_comparison_report.json"
        all_selection_path.parent.mkdir(parents=True, exist_ok=True)
        all_selection_path.write_text(json.dumps(all_selection_payload, indent=2), encoding="utf-8")
        _LOG.info("All-selection comparison report written: %s", all_selection_path)
        print(f"[v] All-selection comparison report written to {all_selection_path}")
        all_selection_comparison_path = str(all_selection_path)

    report_summary_payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "scorer_json_path": str(scorer_json_path),
            "cases_dir": str(cases_dir),
            "run_report_path": str(run_report_path),
        },
        "outputs": {
            "html": str(output_html),
            "markdown": str(output_md) if output_md else None,
            "all_selection_comparison_json": all_selection_comparison_path,
        },
        "summary": {
            "scenario_row_count": len(scorer_rows),
            "test_case_count": len(test_case_summaries),
            "using_all_datasets": using_all_datasets,
            "using_all_scorers": using_all_scorers,
            "run_report_keys": sorted(list(run_meta.keys())) if isinstance(run_meta, dict) else [],
        },
        "dataset_scorer_hierarchy": dataset_scorer_hierarchy,
        "test_case_execution_summaries": test_case_summaries,
        "gui_sqlite_import_payload": {
            "format": "pyrit_gui_sqlite_import_v1",
            "rows": sqlite_import_rows,
        },
        "rows": sqlite_import_rows,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report_summary_payload, indent=2), encoding="utf-8")
    _LOG.info("JSON report written: %s", output_json)
    print(f"[v] JSON report written to {output_json}")

    if output_md:
        full_md = f"""# PyRIT x Ollama  OWASP LLM Top-10 Red-Team Report

_Generated: {generated_at}_

## Run Metadata

{meta_md}

## Scenario Summary

| OWASP ID | Dataset | Converter | Pass/Total | Pass Rate | Weighted Majority | Confidence |
|----------|---------|-----------|------------|-----------|-------------------|------------|
{scenario_md}

## Dataset -> Scorer Hierarchy

| Dataset | Scorer | Cases Scored | True | False | Numeric | Missing |
|---------|--------|--------------|------|-------|---------|---------|
{hierarchy_md}

## Per-Test-Case Execution Summary

| Test Case ID | OWASP ID | Dataset | Result | Weighted Majority | Weighted Confidence |
|--------------|----------|---------|--------|-------------------|---------------------|
{testcase_md}

## Case Details

{cases_md}
"""
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(full_md, encoding="utf-8")
        _LOG.info("Markdown report written: %s", output_md)
        print(f"[v] Markdown report written to {output_md}")

    return output_html


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    parser = _build_parser()
    args = parser.parse_args()

    output_path = generate_html_report(
        scorer_json_path=args.scorer_json,
        cases_dir=args.cases_dir,
        run_report_path=args.run_report,
        output_html=args.output_html,
        output_md=args.output_md,
        output_json=args.output_json,
    )

    if args.open:
        _LOG.info("Opening report in browser: %s", output_path)
        webbrowser.open(output_path.as_uri())
        print(f"[v] Opened in browser: {output_path.as_uri()}")


if __name__ == "__main__":
    main()
