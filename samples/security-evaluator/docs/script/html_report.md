# HTML and Markdown Report Generator

## What it is

This utility builds a self-contained HTML report (and optional Markdown report)
from run artifacts.

## Inputs

- `scorer_outputs.json`
- `run_report.json`
- per-case JSON files under `reports/cases`

## Usage

```bash
# Generate HTML report
python scripts/app/main.py --attack-mode report

# Generate and open report
python scripts/app/main.py --attack-mode report --open

# Generate custom HTML + Markdown outputs
python scripts/app/main.py --attack-mode report \
  --output-html reports/my_report.html \
  --output-md reports/my_report.md

# Standalone
python scripts/app/utils/generate_html_report.py \
  --scorer-json reports/scorer_outputs.json \
  --cases-dir reports/cases \
  --run-report reports/run_report.json \
  --output-html reports/run_report.html \
  --open
```

## Output sections

- Run metadata
- Scenario summary table
- Dataset -> scorer hierarchy table
- Per-test-case execution summary table and result
- Case details with scorer values

## JSON Output For GUI / SQLite Import

The `--output-json` artifact now includes:

- `dataset_scorer_hierarchy`: grouped by dataset and scorer usage/stats
- `test_case_execution_summaries`: one execution summary per test case
- `gui_sqlite_import_payload.rows`: GUI import payload rows
- `rows`: top-level alias for compatibility with `scripts/analysis/import_scorer_json_to_memory.py`

When a run uses all datasets, all scorers, or both, the generator also writes:

- `all_selection_comparison_report.json`: per-run dataset and scorer comparison report

Example:

```bash
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json reports/report_summary.json \
  --db-path reports/gui_import.db
```

## Related docs

- [Batch Re-Scoring](batch_scoring.md)
- [Baseline Scan](baseline_scan.md)
- [Technical Reference](technical_reference.md)
