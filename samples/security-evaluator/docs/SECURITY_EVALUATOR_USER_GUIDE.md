# PyRIT Security Evaluator User Guide

This guide is the central starting point for the `samples/security-evaluator` sample.
It collects the critical user-facing documentation for setup, configuration, attack modes, and analysis.

## Full guide index

1. [Central documentation hub](#1-document-hub-for-pyrit-security-evaluator)
2. [Install dependencies](#2-install-all-dependencies)
3. [Configure `.env` and `.pyrit_config`](#3-configure-env-and-pyrit_config)
4. [Install PyRIT and this sample](#4-install-pyrit-and-this-sample)
5. [Run attack modes](#5-execute-a-very-simple-quick-test)
6. [Report artifacts and outputs](#6-reports-generated-and-significance)
7. [Attack mode selection and tuning](#7-advanced-tests-and-attack-types)
8. [Execute all datasets tests](#8-execute-all-datasets-tests)
9. [Custom dataset authoring](#9-custom-dataset-authoring)
10. [PyRIT GUI setup](#10-pyrit-gui-setup)
11. [Export/import reports for GUI analysis](#11-export-and-import-reports-for-gui-analysis)
12. [HTML, CSV, and raw JSON analysis](#12-html-csv-and-raw-json-analysis)
13. [Troubleshooting](#13-troubleshooting)
14. [PyRIT documentation and reference links](#14-pyrit-documentation-and-reference-links)

## 1. Document hub for PyRIT security evaluator

Use these documents together to understand the sample and the PyRIT platform.

- [Start Here](../START_HERE.md) — step-by-step sample flow from first run to advanced attacks.
- [Local installation](./setup/local_setup.md) — install dependencies on Windows, Linux, or macOS.
- [Docker setup](./setup/docker_setup.md) — run PyRIT inside Docker with host Ollama support.
- [GUI tutorial](./setup/gui_setup.md) — run the PyRIT analysis GUI locally or in Docker.
- [Complete usage reference](./script/usage_guide.md) — environment variables, options, and feature descriptions.
- [Configuration field reference](./script/configuration_fields.md) — `.env` and `.pyrit_config` fields with explanations.
- [Quickstart](./script/quickstart.md) — the fastest way to run a simple sample execution.
- [Attack modes overview](./script/attack_modes_overview.md) — compare modes and get command examples.
- [Artifacts and outputs](./script/artifacts.md) — generated files and how they are organized.
- [Report analysis](./script/report_analysis.md) — how to interpret results, CSV/JSON output, and GUI analysis.
- [Custom dataset guide](./script/custom_dataset_guide.md) — author custom PyRIT datasets.

## 2. Install all dependencies

### Local installation

1. Install Python 3.11 or 3.12.
2. Install Ollama locally and run it.
3. Create and activate a virtual environment in `samples/security-evaluator`.
4. Install PyRIT and sample dependencies.

See: [Local installation](./setup/local_setup.md)

### Docker installation

1. Install Docker and Docker Compose on the host.
2. Start the PyRIT container from the repository `docker/` folder.
3. Configure the container to reach host Ollama.

See: [Docker setup](./setup/docker_setup.md)

## 3. Configure `.env` and `.pyrit_config`

The sample uses two configuration layers:

- `.env.local` — runtime environment variables for the sample runner.
- `.pyrit_config` — PyRIT backend configuration used by initialization and memory setup.

For a full list of fields and explanations, see:

- [Configuration fields reference](./script/configuration_fields.md)

### Main documents should list key required fields

In `.env.local`:

- `OLLAMA_ENDPOINT`
- `OLLAMA_TARGET_MODEL`
- `OLLAMA_ATTACKER_MODEL`
- `OLLAMA_TF_SCORER_MODEL`
- `OLLAMA_SCALE_SCORER_MODEL`
- `OLLAMA_REFUSAL_SCORER_MODEL`
- `ARTIFACTS_ROOT_PATH`
- `LOGS_ROOT_PATH`
- `PYRIT_SQLITE_DB_PATH`
- `RUN_ALL_AVAILABLE_DATASETS`
- `MAX_DATASETS_PER_SCENARIO`
- `RESUME_INCOMPLETE_RUN`

In `.pyrit_config`:

- `memory_db_type`
- `operator`
- `operation`
- `initializers`
- `env_files`
- `silent`

## 4. Install PyRIT and this sample application

### Local install (layman steps)

1. Open a terminal.
2. Navigate to the sample folder:

```bash
cd samples/security-evaluator
```

3. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\Activate      # Windows PowerShell
```

4. Install PyRIT and dependencies:

```bash
pip install --upgrade pip
pip install pyrit
```

5. Verify Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

6. Copy the sample config templates:

```bash
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config
```

On Windows:

```powershell
Copy-Item config/.env.local.example .env.local
Copy-Item config/.pyrit_config.example .pyrit_config
```

7. Edit `.env.local` to match your Ollama endpoint and models.

### Docker install (layman steps)

1. Open a terminal on your Docker host.
2. Navigate to the repository root.

```bash
cd docker
```

3. Start the containers:

```bash
docker-compose up -d
```

4. Enter the PyRIT container shell:

```bash
docker-compose exec pyrit bash
```

5. From inside the container:

```bash
cd samples/security-evaluator
python app/main.py --dry-run
```

For details: [Docker setup](./setup/docker_setup.md)

## 5. Execute a very simple quick test

### Quick test command

Run a dry run first to verify setup without sending prompts:

```bash
cd samples/security-evaluator
python scripts/app/main.py --dry-run
```

### First real test

Run the baseline mode once:

```bash
python scripts/app/main.py --attack-mode baseline
```

This is the simplest real test and gives you the initial report files.

For details: [Quickstart](./script/quickstart.md)

## 6. Reports generated and significance

The sample produces these outputs:

- `reports/` — root folder for run artifacts.
- `reports/<attack_mode>/<datasets>/<scorers>/<timestamp>/` — run-specific folder.
- `reports/cases/` — per-case hierarchical JSON files.
- `reports/scorer_outputs.json` — detailed scorer output payloads.
- `reports/scorer_comparison.csv` — spreadsheet-friendly comparison table.
- `reports/run_report.json` — run manifest and summary.
- `reports/baseline_scan_report.json` — baseline mode summary.
- `reports/rescore_report.json` — output of the `rescore` mode.
- `logs/pyrit_owasp_redteam_production.log` — runtime and checkpoint logs.

For how to analyze the reports, see:

- [Artifacts and outputs](./script/artifacts.md)
- [Report analysis](./script/report_analysis.md)

## 7. Advanced tests and attack types

### Attack mode commands

- Default red-team:

```bash
python scripts/app/main.py --attack-mode redteam
```

- TAP mode:

```bash
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-width 5
```

- Crescendo mode:

```bash
python scripts/app/main.py --attack-mode crescendo --scenarios LLM06 --max-turns 10
```

- XPIA mode:

```bash
python scripts/app/main.py --attack-mode xpia
```

- Baseline mode:

```bash
python scripts/app/main.py --attack-mode baseline --max-seeds 5
```

- Rescore mode:

```bash
python scripts/app/main.py --attack-mode rescore --scorers self_ask_true_false
```

- Report generation:

```bash
python scripts/app/main.py --attack-mode report --open
```

### Single-turn vs multi-turn

- `--turn-mode single` forces one-turn conversations in redteam, TAP, or Crescendo.
- `--turn-mode multi` enables multi-turn behavior where supported.

Example:

```bash
python scripts/app/main.py --attack-mode redteam --turn-mode single
```

### Expected reports

Each attack mode writes the same artifact families, with mode-specific summaries:

- baseline: `baseline_scan_report.json`
- redteam: full `scorer_outputs.json`, `scorer_comparison.csv`, per-case `reports/cases/`
- tap/crescendo/xpia: `scorer_outputs.json`, `scorer_comparison.csv`, `run_report.json`
- rescore: `rescore_report.json`

For the mode comparison and explanations, see:

- [Attack modes overview](./script/attack_modes_overview.md)
- [Baseline scan](./script/baseline_scan.md)
- [TAP attack](./script/tap_attack.md)
- [Crescendo attack](./script/crescendo_attack.md)
- [XPIA attack](./script/xpia_attack.md)

## 8. Execute all datasets tests

To run every available dataset for each scenario:

```bash
export RUN_ALL_AVAILABLE_DATASETS=true
export MAX_DATASETS_PER_SCENARIO=0
python scripts/app/main.py --attack-mode redteam
```

To limit dataset count per scenario:

```bash
export RUN_ALL_AVAILABLE_DATASETS=true
export MAX_DATASETS_PER_SCENARIO=2
python scripts/app/main.py --attack-mode redteam
```

If you need a smaller run for review:

```bash
export RUN_ALL_AVAILABLE_DATASETS=false
python scripts/app/main.py --attack-mode redteam
```

For dataset authoring and execution details, see:

- [Custom dataset guide](./script/custom_dataset_guide.md)
- [Artifacts and outputs](./script/artifacts.md)

## 9. Custom dataset authoring

Use this guide when you need to add new attack cases, seed prompts, or scenario labels.
The custom dataset workflow is useful for:

- Testing new OWASP categories or user intent classes
- Adding specialized prompt payloads for your own red-team scenarios
- Validating input before running against Ollama

Read the full instructions here:

- [Custom dataset guide](./script/custom_dataset_guide.md)

## 10. PyRIT GUI setup

### Local GUI setup

1. Install PyRIT locally and run a sample script.
2. From the repository root, start the GUI:

```bash
cd doc/code
python pyrit_gui.py
```

3. Open `http://localhost:8501` in a browser.

### Docker GUI setup

Use the existing Docker compose definition from `docker/docker-compose.yaml`.
If Ollama runs on the host, set the endpoint inside the container:

```yaml
services:
  pyrit-gui:
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
```

On Linux, replace `host.docker.internal` with the host gateway IP.

### GUI analysis flow

- Import `reports/scorer_outputs.json` into SQLite.
- Open the GUI and filter by OWASP ID, dataset, or scorer.
- Drill into per-case JSON details.

See: [GUI tutorial](./setup/gui_setup.md)

## 11. Export and import reports for GUI analysis

The recommended portable artifact for GUI analysis is `reports/scorer_outputs.json`.
If the run happens on a different host than the GUI, copy that JSON file to the GUI machine
and import it into a SQLite database.

Use the existing import tool:

```bash
cd samples/security-evaluator
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json /path/to/scorer_outputs.json \
  --db-path /path/to/pyrit_gui.db
```

To make export easier, use the helper script:

```bash
python scripts/analysis/export_scorer_outputs_for_gui.py \
  --input-json reports/scorer_outputs.json \
  --output-dir exported_gui_reports \
  --include-run-report \
  --include-comparison-csv
```

Then transfer `exported_gui_reports/scorer_outputs.json` to the GUI host and import it.

If you already have an existing SQLite DB, copy the DB file directly instead of importing JSON:

```bash
scp /tmp/pyrit_ollama_demo.db gui-host:/tmp/pyrit_ollama_gui.db
```

Then start the GUI with:

```bash
export PYRIT_SQLITE_DB_PATH=/tmp/pyrit_ollama_gui.db
cd doc/code
python pyrit_gui.py
```

See: [GUI report transfer guide](./setup/gui_data_transfer.md)

## 12. HTML, CSV, and raw JSON analysis

PyRIT generates multiple artifact types for flexible post-run analysis:

- `reports/scorer_outputs.json` — detailed per-case scorer payloads.
- `reports/scorer_comparison.csv` — flattened comparison table for spreadsheets.
- `reports/run_report.json` — summary of the run and totals.
- `reports/cases/` — per-case JSON files for direct programmatic analysis.

For either GUI or offline workflows, use the dedicated analysis guide:

- [Report analysis](./script/report_analysis.md)
- [Artifacts and outputs](./script/artifacts.md)

## 13. Troubleshooting

Common problems and where to find help:

- Ollama endpoint unreachable: check [Docker setup](./setup/docker_setup.md#troubleshooting).
- Missing GUI data: ensure `scorer_outputs.json` imported into SQLite and `PYRIT_SQLITE_DB_PATH` points to the correct DB.
- Run errors or bad prompts: review `logs/pyrit_owasp_redteam_production.log`.
- Dataset authoring issues: use [Custom dataset guide](./script/custom_dataset_guide.md#common-gotchas).

## 14. PyRIT documentation and reference links

Primary documentation sources:

- [PyRIT root README](../../README.md)
- [PyRIT repo docs index](https://github.com/Azure/PyRIT/blob/main/doc/README.md)
- [Local installation guide](./setup/local_setup.md)
- [Docker setup guide](./setup/docker_setup.md)
- [PyRIT GUI tutorial](./setup/gui_setup.md)
- [Complete sample usage reference](./script/usage_guide.md)

For sample-specific run details, use the guide links above and the central
[Security Evaluator User Guide](./SECURITY_EVALUATOR_USER_GUIDE.md).

---

## Recommended first path

1. [Start Here](../START_HERE.md)
2. [Local installation](./setup/local_setup.md) or [Docker setup](./setup/docker_setup.md)
3. [Quickstart](./script/quickstart.md)
4. [Custom dataset guide](./script/custom_dataset_guide.md)
5. [Report analysis](./script/report_analysis.md)
