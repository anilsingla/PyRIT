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
10. [Optional PyRIT GUI setup](#10-optional-pyrit-gui-setup)
11. [Optional export/import reports for GUI analysis](#11-optional-export-and-import-reports-for-gui-analysis)
12. [HTML, CSV, and raw JSON analysis](#12-html-csv-and-raw-json-analysis)
13. [Best practices & common patterns](#13-best-practices--common-patterns)
14. [Troubleshooting](#13-troubleshooting)
15. [PyRIT documentation and reference links](#14-pyrit-documentation-and-reference-links)

## 1. Document hub for PyRIT security evaluator

Use these documents together to understand the sample and the PyRIT platform.

- [About PyRIT](../../../doc/about_pyrit.md) — core PyRIT purpose, architecture context, and design intent.
- [PyRIT glossary](../../../doc/glossary.md) — definitions of PyRIT concepts and terminology.
- [Start Here](../START_HERE.md) — step-by-step sample flow from first run to advanced attacks.
- [Local installation](./setup/local_setup.md) — install dependencies on Windows, Linux, or macOS.
- [Docker setup](./setup/docker_setup.md) — run PyRIT inside Docker with host Ollama support.
- [GUI tutorial](./setup/gui_setup.md) — optional analysis interface for local or Docker use.
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
2. Install and configure Ollama locally.
3. Install and configure local SQLite for PyRIT memory.
4. Create and activate a virtual environment in `samples/security-evaluator`.
5. Install PyRIT and sample dependencies.

Recommended Ollama setup scripts:

Windows (PowerShell):

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_ollama_windows.ps1
```

Linux/macOS:

```bash
cd samples/security-evaluator
bash scripts/installers/setup_ollama_linux.sh
```

These scripts install Ollama, start/verify the local endpoint, pull default models, and run a non-interactive model check.

Recommended SQLite setup scripts:

Windows (PowerShell):

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_sqlite_windows.ps1
```

Linux/macOS:

```bash
cd samples/security-evaluator
bash scripts/installers/setup_sqlite_linux.sh
```

These scripts install SQLite, prepare Python environment, and run a PyRIT SQLite smoke test.

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

5. Install/verify local SQLite setup:

```bash
bash scripts/installers/setup_sqlite_linux.sh   # Linux/macOS
```

On Windows PowerShell:

```powershell
.\scripts\installers\setup_sqlite_windows.ps1
```

6. Verify Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

7. Copy the sample config templates:

```bash
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config
```

On Windows:

```powershell
Copy-Item config/.env.local.example .env.local
Copy-Item config/.pyrit_config.example .pyrit_config
```

8. Edit `.env.local` to match your Ollama endpoint and models.

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

**Always run `--dry-run` first** to validate setup before running actual attacks:

```bash
cd samples/security-evaluator
python scripts/app/main.py --dry-run
```

What `--dry-run` does:
- Validates configuration (`.env`, `.pyrit_config`, Ollama endpoint)
- Plans the attack without sending any prompts or scoring
- Estimates resource requirements and runtime
- Catches configuration errors early (saves hours of wasted execution)
- Does NOT access the LLM or generate scores

### First real test

Run the baseline mode once (simplest, fastest real attack):

```bash
python scripts/app/main.py --attack-mode baseline
```

Expected result: Generates `reports/baseline_scan_report.json`, `scorer_outputs.json`, and `scorer_comparison.csv`.

Typical runtime: 5-15 minutes depending on model size and dataset count.

### Targeted runner smoke matrix

Use this matrix after code changes to quickly validate each standalone runner entrypoint.

```bash
python scripts/app/attacks/crescendo_attack_runner.py --scenarios LLM01 --dry-run
python scripts/app/attacks/tap_attack_runner.py --scenarios LLM01 --dry-run
python scripts/app/attacks/redteam_attack_runner.py --converters base64 --dry-run
python scripts/app/attacks/xpia_attack_runner.py --scenarios LLM02 --dry-run
python scripts/app/attacks/baseline_scan_runner.py --scenarios LLM01 --dry-run
python scripts/app/attacks/batch_rescore_runner.py --dry-run
```

Expected behavior:
- Dry-run confirms argument parsing and execution planning.
- No prompts are sent and no live attacks run.
- If runtime attack modules are missing in your environment, runners exit gracefully and print a clear missing module message (for example `No module named 'pyrit.executor'`).

Live run prerequisite:
- For real attack execution (non-dry-run), install the full PyRIT runtime components that provide `pyrit.executor`.

Output controls (environment flags):
- `ENABLE_WAIT_SPINNER=true|false` controls spinner display while waiting for long async steps.
- `ENABLE_LIVE_SCORER_FEED=true|false` controls streaming per-scorer results as each scorer completes.

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

### Complete CLI parameter reference

The application accepts these top-level values and flags:

- `--attack-mode`: `redteam`, `tap`, `crescendo`, `xpia`, `baseline`, `rescore`, `report`
- `--turn-mode`: `single`, `multi` (multi is valid only for `redteam`, `tap`, `crescendo`)
- `--converters`: comma-separated or space-separated converter keys
  - Available keys: `base64`, `rot13`, `caesar`, `atbash`, `flip`, `leetspeak`, `unicode_confusable`, `string_join`, `char_swap`, `emoji`, `random_caps`, `tone_persuasive`, `variation`, `translation_french`
- `--all-converters`: run all converter keys
- `--datasets`: dataset names and/or custom dataset file paths (`.json`, `.yaml`, `.yml`, `.prompt`)
- `--all-datasets`: run all available datasets
- `--scorers`: comma-separated or space-separated scorer keys
  - Available keys: `substring`, `self_ask_true_false`, `self_ask_scale`, `scale_threshold_0_7`, `refusal`, `compliance_inverted_refusal`
- `--all-scorers`: run all available scorers
- `--scenarios`: OWASP IDs such as `LLM01 ... LLM10`
- `--dry-run`: plan only, no attack execution
- `--local-datasets-only`: skip remote dataset provider fetch
- `--converter-info`: print converter guide and exit
- `--detailed-help`: print comprehensive help and exit

Mode-specific parameters:

- TAP (`--attack-mode tap`)
  - `--tap-width <int>`
  - `--tap-depth <int>`
  - `--tap-branching-factor <int>`
- Crescendo (`--attack-mode crescendo`)
  - `--max-backtracks <int>`
  - `--max-turns <int>`
- Baseline (`--attack-mode baseline`)
  - `--max-seeds <int>` (`0` means unlimited)
- Rescore (`--attack-mode rescore`)
  - `--filter-owasp <LLM IDs...>`
  - `--output-json <path>`
- Report (`--attack-mode report`)
  - `--output-html <path>`
  - `--output-md <path>`
  - `--output-json <path>`
  - `--open`

### Single-turn and multi-turn behavior by mode

- Multi-turn supported: `redteam`, `tap`, `crescendo`
- Single-turn only: `baseline`, `xpia`
- Turn mode not applicable: `rescore`, `report`

If `--turn-mode multi` is used with `baseline` or `xpia`, the runner returns a validation error.

### Per-mode command examples

#### 1) Redteam mode

Single-turn example:

```bash
python scripts/app/main.py --attack-mode redteam --turn-mode single --scenarios LLM01 --converters base64,leetspeak --datasets harmbench --scorers self_ask_true_false --dry-run
```

Multi-turn example:

```bash
python scripts/app/main.py --attack-mode redteam --turn-mode multi --all-converters --all-datasets --all-scorers
```

#### 2) TAP mode

Single-turn example (forces depth to one turn behavior):

```bash
python scripts/app/main.py --attack-mode tap --turn-mode single --scenarios LLM01 --tap-width 3 --tap-depth 5 --tap-branching-factor 2 --dry-run
```

Multi-turn example:

```bash
python scripts/app/main.py --attack-mode tap --turn-mode multi --scenarios LLM01 LLM02 --tap-width 5 --tap-depth 4 --tap-branching-factor 2
```

#### 3) Crescendo mode

Single-turn example:

```bash
python scripts/app/main.py --attack-mode crescendo --turn-mode single --scenarios LLM06 --max-backtracks 5 --max-turns 10 --dry-run
```

Multi-turn example:

```bash
python scripts/app/main.py --attack-mode crescendo --turn-mode multi --scenarios LLM06 LLM08 --max-backtracks 6 --max-turns 12
```

#### 4) XPIA mode

XPIA supports single-turn behavior.

Single-turn example:

```bash
python scripts/app/main.py --attack-mode xpia --scenarios LLM02 LLM08 --dry-run
```

Multi-turn note: not supported for XPIA.

#### 5) Baseline mode

Baseline is single-turn control scanning.

Single-turn example:

```bash
python scripts/app/main.py --attack-mode baseline --scenarios LLM01 LLM03 --datasets harmbench --scorers self_ask_true_false --max-seeds 5
```

Multi-turn note: not supported for baseline.

#### 6) Rescore mode

Rescore recomputes scores from existing memory records.

Example:

```bash
python scripts/app/main.py --attack-mode rescore --scorers self_ask_true_false,refusal --filter-owasp LLM01 LLM02 --output-json reports/rescore_report_custom.json
```

#### 7) Report mode

Report mode renders outputs from existing artifacts.

Example:

```bash
python scripts/app/main.py --attack-mode report --output-html reports/run_report.html --output-md reports/run_report.md --output-json reports/report_summary.json --open
```

### Understanding automatic report generation vs report rendering

This is a critical distinction that prevents confusion:

**Automatic Report Generation (default behavior):**
- Every attack run (`redteam`, `tap`, `crescendo`, `xpia`, `baseline`) **automatically generates reports** after completion.
- Reports are written to `reports/` folder without any extra command needed.
- You get JSON, CSV, and per-case artifacts by default.
- Use `--open` flag to automatically open the HTML report in your browser after the attack finishes.

Example: Run an attack and auto-open the report in browser:
```bash
python scripts/app/main.py --attack-mode redteam --scenarios LLM01 --open
# Automatically generates: reports/scorer_outputs.json, scorer_comparison.csv, run_report.html
# And opens run_report.html in your browser
```

**Report Rendering Mode (`--attack-mode report`):**
- This is a **utility mode** that does NOT run any attacks.
- It only **regenerates HTML/Markdown/JSON formats** from existing attack artifacts.
- Use this when you want to:
  - Reformat existing results to HTML/Markdown without re-running attacks (saves time)
  - Generate custom report output paths
  - Create multiple output formats from a single run's data
  - Regenerate reports after modifying scorer logic (Rescore first, then Report)

Example: Regenerate reports from existing run data with custom output paths:
```bash
# First, run an attack (generates artifacts)
python scripts/app/main.py --attack-mode redteam --scenarios LLM01

# Later, regenerate reports in different formats without re-running:
python scripts/app/main.py --attack-mode report --output-html custom_report.html --output-md custom_report.md --open
# No attacks run; just reformats existing data and opens HTML in browser
```

**The `--open` flag:**
- Works with any attack mode that generates reports or with `report` mode.
- Opens the generated HTML file in your default browser immediately after generation.
- Saves you from manually navigating to the file.

| Scenario | Command | What happens |
|----------|---------|--------------|
| Run attack + view report | `python scripts/app/main.py --attack-mode redteam --open` | Executes attacks, auto-generates reports, opens HTML in browser |
| Run attack (no auto-open) | `python scripts/app/main.py --attack-mode redteam` | Executes attacks, auto-generates reports, saves to disk |
| Regenerate from existing data | `python scripts/app/main.py --attack-mode report --open` | NO attacks; reformats existing artifacts, opens HTML in browser |
| Re-score + regenerate | `python scripts/app/main.py --attack-mode rescore && python scripts/app/main.py --attack-mode report --open` | Re-scores existing data, then regenerates reports from new scores |

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

## 10. Optional PyRIT GUI setup

This section is optional. The unified container workflow does not require the GUI.

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

## 11. Optional export and import reports for GUI analysis

Use these steps only if you want to move results into the optional GUI workflow.

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

## 13. Best practices & common patterns

### Always validate before long runs

1. Start with `--dry-run` to catch config errors in seconds, not hours:

```bash
python scripts/app/main.py --attack-mode redteam --all-datasets --dry-run
```

2. After validation, run with a single dataset to test end-to-end:

```bash
python scripts/app/main.py --attack-mode redteam --datasets harmbench --scorers self_ask_true_false --open
```

3. Once working, scale up to full tests:

```bash
python scripts/app/main.py --attack-mode redteam --all-datasets --all-scorers --open
```

### Checkpoint and resume incomplete runs

If a run is interrupted (network loss, process crash), resume from last checkpoint:

```bash
export RESUME_INCOMPLETE_RUN=true
python scripts/app/main.py --attack-mode redteam --all-datasets
```

This continues from where it stopped instead of restarting from beginning (saves time and resources).

### Common command patterns by scenario

**Scenario: Quick safety scan (5-10 minutes)**
```bash
python scripts/app/main.py --attack-mode baseline --scenarios LLM01 LLM02 --dry-run
python scripts/app/main.py --attack-mode baseline --scenarios LLM01 LLM02 --open
```

**Scenario: Comprehensive test of all converters and scorers (30+ minutes)**
```bash
python scripts/app/main.py --attack-mode redteam --turn-mode single --all-converters --all-scorers --datasets harmbench --dry-run
python scripts/app/main.py --attack-mode redteam --turn-mode single --all-converters --all-scorers --datasets harmbench
```

**Scenario: Multi-turn adversarial testing (60+ minutes)**
```bash
python scripts/app/main.py --attack-mode redteam --turn-mode multi --scenarios LLM01 LLM02 --dry-run
python scripts/app/main.py --attack-mode redteam --turn-mode multi --scenarios LLM01 LLM02 --open
```

**Scenario: Adaptive attack with tree-of-attacks (TAP mode, 20-40 minutes)**
```bash
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-width 3 --tap-depth 5 --tap-branching-factor 2 --dry-run
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-width 3 --tap-depth 5 --tap-branching-factor 2
```

**Scenario: Test new scoring logic on existing run**
```bash
# First, re-compute scores with new scorers
python scripts/app/main.py --attack-mode rescore --scorers self_ask_true_false,compliance_inverted_refusal --output-json reports/new_scores.json

# Then, render new reports from updated scores
python scripts/app/main.py --attack-mode report --output-html reports/updated_report.html --open
```

### Understanding model roles in configuration

PyRIT uses three types of models; configure them correctly in `.env.local`:

- **OLLAMA_TARGET_MODEL** — The model you are testing (red-team target). Use production or representative model.
- **OLLAMA_ATTACKER_MODEL** — The model that generates attack prompts (probing model). Can be smaller/cheaper; generates adversarial variations.
- **OLLAMA_*_SCORER_MODEL** — Models that evaluate target responses. Can differ by scoring type (TF, scale, refusal).

Best practice: Use your production model as the target, and a smaller efficient model for attacks/scoring to save compute.

### What makes a successful run?

Check these signs your attack completed successfully:

1. **Logs show completions**: `tail logs/pyrit_owasp_redteam_production.log` shows `Completed` or `Success` messages
2. **Report files exist**: `ls reports/` shows `scorer_outputs.json`, `scorer_comparison.csv`, run timestamp folders
3. **CSV has rows**: `wc -l reports/scorer_comparison.csv` shows more than just the header row
4. **Cases folder populated**: `ls reports/cases/ | wc -l` shows files (usually hundreds for multi-turn)
5. **No database lock errors**: Logs do NOT show `database is locked` or `SQLITE_BUSY` errors

If any are missing, check [Troubleshooting](#13-troubleshooting).

### Parallel execution constraints

⚠️ **Do NOT run multiple PyRIT instances simultaneously with the same `PYRIT_SQLITE_DB_PATH`.**

SQLite allows one writer at a time. Multiple instances will cause `database is locked` errors.

**Solution**: Use separate databases per run:

```bash
# Terminal 1: Run attack 1
export PYRIT_SQLITE_DB_PATH=./pyrit_run1.db
python scripts/app/main.py --attack-mode redteam --scenarios LLM01

# Terminal 2 (different shell): Run attack 2 with different DB
export PYRIT_SQLITE_DB_PATH=./pyrit_run2.db
python scripts/app/main.py --attack-mode redteam --scenarios LLM02
```

### Converter and scorer selection guide

**Converters** (transform prompts to evade detection):

| Converter | Use when | Purpose |
|-----------|----------|---------|
| `base64`, `rot13`, `caesar` | Testing encoding robustness | Obfuscation via encoding |
| `flip`, `atbash`, `char_swap` | Testing character manipulation | Character-level evasion |
| `emoji`, `unicode_confusable` | Testing Unicode handling | Unicode-based obfuscation |
| `leetspeak`, `random_caps`, `tone_persuasive` | Testing semantic robustness | Semantic-preserving variations |
| `translation_french` | Testing multilingual models | Cross-language robustness |
| `--all-converters` | Comprehensive evaluation | Full converter coverage |

**Scorers** (evaluate LLM response quality/safety):

| Scorer | Evaluates | Output |
|--------|-----------|--------|
| `substring` | Exact string match | Binary (pass/fail) |
| `self_ask_true_false` | LLM judgment via prompt | Binary (True/False) |
| `self_ask_scale` | LLM severity rating | 0-10 scale |
| `scale_threshold_0_7` | Response thresholds | Boolean above/below 0.7 |
| `refusal` | Refusal behavior | Did model refuse response |
| `compliance_inverted_refusal` | Safety compliance | Inverse refusal scoring |

Tip: Use multiple scorers to cross-validate results. Disagreement between scorers often indicates edge cases.

### OWASP LLM Security categories (--scenarios)

The `--scenarios` parameter uses OWASP LLM Top 10 security categories:

- `LLM01` — Prompt injection
- `LLM02` — Insecure output handling
- `LLM03` — Training data poisoning
- `LLM04` — Model denial of service
- `LLM05` — Supply chain vulnerabilities
- `LLM06` — Sensitive information disclosure
- `LLM07` — Insecure plugin design
- `LLM08` — Model theft
- `LLM09` — Unauthorized model access
- `LLM10` — Training data leakage

Tip: Start with `LLM01` (prompt injection) — it's the most testable. Add others as your testing matures.

## 13. Troubleshooting

### Common errors and solutions

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `Connection refused` at Ollama endpoint | Ollama not running or wrong host | Verify `curl http://localhost:11434/api/tags` works. Check `OLLAMA_ENDPOINT` in `.env.local` |
| `database is locked` | Multiple PyRIT instances using same DB | Use separate `PYRIT_SQLITE_DB_PATH` per instance or wait for first run to finish |
| `Failed to load .env` | Config file missing or syntax error | Verify `.env.local` and `.pyrit_config` exist in sample folder. Check for YAML syntax errors |
| `No datasets found` | Dataset path incorrect or files missing | Check `--datasets` parameter references real file. Use `--converter-info` to verify |
| `Unknown scorer: xxx` | Typo in scorer name or scorer not installed | Run `--detailed-help` to see available scorers. Check spelling exactly |
| `No valid OWASP scenarios` | Scenario ID typo (case-sensitive) | Use uppercase IDs: `LLM01 ... LLM10`, not lowercase or partial |
| `Memory backend initialization failed` | PyRIT config issue | Check `.pyrit_config` has valid `memory_db_type` and initializers. See [Configuration fields](./script/configuration_fields.md) |
| Empty `scorer_outputs.json` | Attack ran but produced no scoreable outputs | Check target model is responding. Check attack mode is valid for model. Verify scorer configurations |

### Debugging steps

1. **Validate setup without execution**:
   ```bash
   python scripts/app/main.py --attack-mode baseline --dry-run
   ```
   This reveals config errors in seconds.

2. **Check logs for details**:
   ```bash
   tail -f logs/pyrit_owasp_redteam_production.log
   ```
   Look for `ERROR`, `FAILED`, `exception` keywords.

3. **Test Ollama connectivity**:
   ```bash
   curl http://localhost:11434/api/tags
   curl http://localhost:11434/api/generate -d '{"model": "YOUR_MODEL", "prompt": "test"}'
   ```

4. **Verify database integrity**:
   ```bash
   sqlite3 /path/to/pyrit.db "SELECT COUNT(*) FROM prompts;"
   ```
   Should return a number (>0 for runs, 0 for fresh DB).

5. **Check disk space**:
   Reports and logs can grow large. Ensure `ARTIFACTS_ROOT_PATH` and `LOGS_ROOT_PATH` have >1 GB free.

### Performance tuning

- **Run taking too long?** Use `--dry-run` to see estimated time. Reduce `--tap-depth`, `--tap-width`, or `--max-turns`.
- **Out of memory?** Reduce `MAX_DATASETS_PER_SCENARIO` or use smaller models for attacker/scorer roles.
- **High disk usage?** Archive old `reports/` folders. CSV files can be deleted; keep JSON for future analysis.

### Getting more help

If you're still stuck:

1. Check the [PyRIT glossary](../../../doc/glossary.md) for terminology
2. Read the specific attack mode guide: [Attack modes overview](./script/attack_modes_overview.md)
3. Search existing GitHub issues: https://github.com/Azure/PyRIT/issues
4. Open a new issue with logs and error details

## 14. PyRIT documentation and reference links

Primary documentation sources:

- [PyRIT root README](../../README.md)
- [PyRIT repo docs index](https://github.com/Azure/PyRIT/blob/main/doc/README.md)
- [Local installation guide](./setup/local_setup.md)
- [Docker setup guide](./setup/docker_setup.md)
- [PyRIT GUI tutorial](./setup/gui_setup.md) (optional)
- [Complete sample usage reference](./script/usage_guide.md)

For sample-specific run details, use the guide links above and the central
[Security Evaluator User Guide](./SECURITY_EVALUATOR_USER_GUIDE.md).

### Optional API auth quickstart (disabled by default)

Use this only when you explicitly want API endpoint protection.

1. Keep local bind unless remote exposure is required:

```bash
export API_HOST=127.0.0.1
export API_ALLOW_REMOTE_HOST=false
```

2. Enable auth and define bearer token:

```bash
export API_AUTH_ENABLED=true
export API_BEARER_TOKEN=replace-with-strong-random-value
```

3. Start API service:

```bash
cd samples/security-evaluator
python -m api.run_api
```

4. Call protected endpoint:

```bash
curl -H "Authorization: Bearer replace-with-strong-random-value" \
  http://127.0.0.1:8088/api/v1/options
```

PowerShell equivalent:

```powershell
$env:API_HOST = "127.0.0.1"
$env:API_ALLOW_REMOTE_HOST = "false"
$env:API_AUTH_ENABLED = "true"
$env:API_BEARER_TOKEN = "replace-with-strong-random-value"
python -m api.run_api
```

---

## Quick Reference Card

### Setup validation

```bash
# Verify Ollama running
curl http://localhost:11434/api/tags

# Verify PyRIT installation
python -c "import pyrit; print(pyrit.__version__)"

# Validate config without executing attacks (ALWAYS do this first!)
python scripts/app/main.py --attack-mode baseline --dry-run
```

### Running attacks

```bash
# Simplest test (fastest, <15 min)
python scripts/app/main.py --attack-mode baseline --open

# Comprehensive single-turn test
python scripts/app/main.py --attack-mode redteam --turn-mode single --all-converters --all-scorers --open

# Multi-turn adversarial test
python scripts/app/main.py --attack-mode redteam --turn-mode multi --scenarios LLM01 LLM02 --open

# Tree-of-attacks test
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-depth 5 --tap-width 3

# Crescendo (progressive escalation)
python scripts/app/main.py --attack-mode crescendo --scenarios LLM06 --max-turns 10

# Cross-prompt injection analysis
python scripts/app/main.py --attack-mode xpia --scenarios LLM01 LLM02
```

### After attacks complete

```bash
# Regenerate reports in different formats
python scripts/app/main.py --attack-mode report --output-html custom.html --output-md custom.md --open

# Re-score with new scorers only (no attacks)
python scripts/app/main.py --attack-mode rescore --scorers compliance_inverted_refusal --output-json new_scores.json

# Re-generate report from new scores
python scripts/app/main.py --attack-mode report --open

# Open HTML report manually
open reports/run_report.html  # macOS
xdg-open reports/run_report.html  # Linux
start reports/run_report.html  # Windows
```

### Debugging

```bash
# Show detailed help
python scripts/app/main.py --detailed-help

# Show converter options
python scripts/app/main.py --converter-info

# Monitor running job
tail -f logs/pyrit_owasp_redteam_production.log

# Check database status
sqlite3 /path/to/pyrit.db "SELECT COUNT(*) FROM prompts, responses;"

# Resume interrupted run
export RESUME_INCOMPLETE_RUN=true
python scripts/app/main.py --attack-mode redteam --all-datasets
```

### Configuration tweaks

```bash
# Use single dataset for faster testing
python scripts/app/main.py --attack-mode redteam --datasets harmbench --open

# Use specific scenarios only
python scripts/app/main.py --attack-mode redteam --scenarios LLM01 LLM02 LLM06 --open

# Limit converter count (testing)
python scripts/app/main.py --attack-mode redteam --converters base64,leetspeak --open

# Skip remote dataset providers (offline mode)
python scripts/app/main.py --attack-mode redteam --local-datasets-only

# Run all available data
export RUN_ALL_AVAILABLE_DATASETS=true
export MAX_DATASETS_PER_SCENARIO=0  # unlimited
python scripts/app/main.py --attack-mode redteam
```

### Analysis workflows

```bash
# Export for sharing with stakeholders
python scripts/analysis/export_scorer_outputs_for_gui.py \
  --input-json reports/scorer_outputs.json \
  --output-dir exported_reports \
  --include-run-report \
  --include-comparison-csv

# Import into GUI for interactive analysis
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json reports/scorer_outputs.json \
  --db-path pyrit_gui.db

# Open GUI on Linux/macOS
cd doc/code && python pyrit_gui.py

# Open GUI on Windows (PowerShell)
cd doc\code; python pyrit_gui.py
# Then open browser to http://localhost:8501
```

---

## Recommended first path

1. [Start Here](../START_HERE.md)
2. [Local installation](./setup/local_setup.md) or [Docker setup](./setup/docker_setup.md)
3. [Quickstart](./script/quickstart.md)
4. [Best practices](./SECURITY_EVALUATOR_USER_GUIDE.md#13-best-practices--common-patterns)
5. [Custom dataset guide](./script/custom_dataset_guide.md)
6. [Report analysis](./script/report_analysis.md)
