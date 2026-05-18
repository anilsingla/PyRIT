#!/usr/bin/env python3
"""HTML / Markdown run report generator.

Reads the scorer outputs JSON and per-case JSON reports produced by the runner
and generates a self-contained HTML report with:

  - Per-OWASP-scenario summary table (pass/fail, weighted confidence, scorer breakdown)
  - Conversation transcript per case
  - Side-by-side scorer comparison per case
  - Aggregate statistics section

    python scripts/app/report/generate_html_report.py

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
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from redteam_runner.env_config import (
    ARTIFACTS_ROOT_PATH,
    REPORTS_ROOT_PATH,
    SCORER_OUTPUTS_JSON_PATH,
    RUN_REPORT_JSON_PATH,
    configure_runner_logging,
)

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
        return json.loads(path.read_text(encoding="utf-8"))
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

  <h2>Case Details</h2>
  {cases_html or "<p><em>No per-case report files found in cases directory.</em></p>"}

</body>
</html>"""

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(full_html, encoding="utf-8")
    _LOG.info("HTML report written: %s", output_html)
    print(f"[v] HTML report written to {output_html}")

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
        },
        "summary": {
            "scenario_row_count": len(scorer_rows),
            "run_report_keys": sorted(list(run_meta.keys())) if isinstance(run_meta, dict) else [],
        },
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

## Case Details

{cases_md}
"""
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(full_md, encoding="utf-8")
        _LOG.info("Markdown report written: %s", output_md)
        print(f"[v] Markdown report written to {output_md}")

    return output_html


def main() -> None:
    configure_runner_logging(level=logging.INFO)

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
