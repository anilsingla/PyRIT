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
python scripts/app/report/generate_html_report.py \
  --scorer-json reports/scorer_outputs.json \
  --cases-dir reports/cases \
  --run-report reports/run_report.json \
  --output-html reports/run_report.html \
  --open
```

## Output sections

- Run metadata
- Scenario summary table
- Case details with scorer values

## Related docs

- [Batch Re-Scoring](batch_scoring.md)
- [Baseline Scan](baseline_scan.md)
- [Technical Reference](technical_reference.md)
