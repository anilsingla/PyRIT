# PyRIT GUI Report Export / Import

This guide explains how to move generated PyRIT report data from one machine to another and import it into the PyRIT GUI for interactive analysis.

## When to use this

Use this workflow when your red-team run happens on a different host than the GUI environment, for example:

- Run the security evaluator on a workstation with Ollama and GPU access.
- Copy generated JSON reports to a separate analysis host with the PyRIT GUI installed.
- Import the report data into SQLite so the GUI can display it.

## Export the report artifact

The primary export artifact is:

- `reports/scorer_outputs.json` — the detailed scorer output payload used by the GUI import tool.

If you want to copy additional files for reference, export these too:

- `reports/run_report.json` — run summary and totals
- `reports/scorer_comparison.csv` — flattened scores for spreadsheet analysis

### Recommended export command

From the sample root directory:

```bash
python scripts/analysis/export_scorer_outputs_for_gui.py \
  --input-json reports/scorer_outputs.json \
  --output-dir ./exported_gui_reports \
  --include-run-report \
  --include-comparison-csv
```

This creates a portable directory:

```text
exported_gui_reports/
  scorer_outputs.json
  run_report.json
  scorer_comparison.csv
```

### Copy the exported data to the GUI host

Use your preferred file transfer method:

- `scp`, `rsync`, or `sftp`
- network share or mapped drive
- USB thumb drive

Example:

```bash
scp -r exported_gui_reports user@gui-host:/tmp/pyrit_data
```

## Import into the GUI SQLite database

On the GUI host, use the existing import script to load `scorer_outputs.json` into a SQLite database.

```bash
cd samples/security-evaluator
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json /tmp/pyrit_data/scorer_outputs.json \
  --db-path /tmp/pyrit_ollama_gui.db
```

If you already have a database and want to append new reports, point to the same `--db-path`.

## Alternate workflow: copy the SQLite database file

If you already have a populated SQLite database from an earlier run, you can also copy the database file directly to the GUI host and open it from there.

```bash
scp /tmp/pyrit_ollama_demo.db user@gui-host:/tmp/pyrit_ollama_gui.db
```

Then start the GUI with that database:

```bash
export PYRIT_SQLITE_DB_PATH=/tmp/pyrit_ollama_gui.db
cd doc/code
python pyrit_gui.py
```

## Verify GUI import

- Start the GUI: `http://localhost:8501`
- Confirm the imported run by filtering on dataset, model, or execution date.
- If no data appears, ensure the import script and SQLite DB path match the host environment.

## Related documents

- [GUI Tutorial](./gui_setup.md)
- [Report analysis](../script/report_analysis.md)
- [Artifacts and outputs](../script/artifacts.md)
