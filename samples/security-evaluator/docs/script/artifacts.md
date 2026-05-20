# Artifacts and Outputs

This guide explains what files are created after you run the sample and where to find them.

## Start here

If you are new, run:

```bash
python scripts/app/main.py --dry-run
```

Then run a baseline or red-team attack and inspect the generated files below.

## Main output locations

After a run, look in these folders:

- `reports/<attack_mode>/<datasets>/<scorers>/<timestamp>/` - JSON and CSV summaries for one run
- `reports/<attack_mode>/<datasets>/<scorers>/<timestamp>/cases/` - per-case reports, grouped by scenario, dataset, seed group, and scorer
- `logs/` - runtime and production logs
- `pyrit_sec_eval_logs/` - standalone runner dual-output logs (screen + file)

## Key files

- `scorer_outputs.json` - detailed scorer payloads for each case
- `scorer_comparison.csv` - flattened comparison data for spreadsheets
- `run_report.json` - run summary and output manifest
- `batch_scorer_check.json` - batch scorer applicability details
- `baseline_scan_report.json` - baseline-specific summary
- `rescore_report.json` - rescoring output when using `--attack-mode rescore`

## Example case layout

```text
reports/redteam/datasets__airt_illegal__harmbench/scorers__self_ask_true_false__refusal/20260515T120000Z/
  scorer_comparison.csv
  scorer_outputs.json
  run_report.json
  cases/
    llm01_prompt_injection/
      airt_illegal/
        group_1/
          self_ask_true_false/
            case_00001_scenario_00000.json
```

## What to use each artifact for

- Use `scorer_outputs.json` when you want to import results into the GUI.
- Use `scorer_comparison.csv` when you want fast spreadsheet analysis.
- Use `run_report.json` when you want a compact manifest of the run.
- Use `cases/` when you want the full hierarchical details for one case.

## Recommended workflow

1. Run `--dry-run` first.
2. Run `baseline` for a simple control result.
3. Run `redteam` for the main workflow.
4. Open the HTML report; optionally open the GUI (see [GUI Tutorial](../setup/gui_setup.md) for import steps).
5. Use the run-specific folder under `reports/` and its `cases/` subfolder for deeper analysis.

## Related docs

- [Script Quickstart](quickstart.md)
- [Baseline Scan](baseline_scan.md)
- [HTML Report](html_report.md)
- [GUI Tutorial](../setup/gui_setup.md)
