# PyRIT Red-Team Scripts

This folder contains the complete red-team execution environment organized by workflow and purpose. All scripts expect to be run from the `samples/security-evaluator/` directory.

New to this sample? Start with [START_HERE.md](../START_HERE.md) for a simple step-by-step path from first run to advanced modes.

For a complete, sequential security evaluator walkthrough, see [../docs/SECURITY_EVALUATOR_USER_GUIDE.md](../docs/SECURITY_EVALUATOR_USER_GUIDE.md).

## API and Service Hosting

This sample now includes optional API and service files outside `scripts/`:

- `api/` exposes runner operations over HTTP/HTTPS via FastAPI.
- `scripts/installers/app_service/` provides optional service wrappers for Linux (systemd), macOS (launchd), and Windows (NSSM scripts).

See:

- [API quick reference](../api/README.md)
- [API full setup guide](../api/API_SETUP_GUIDE.md)
- [Services quick reference](installers/app_service/README.md)
- [Services all-environments guide](installers/app_service/SERVICES_GUIDE.md)
- [Artifacts and outputs](../docs/script/artifacts.md)
- [Interactive installer](installers/install_security_evaluator.py) - Guided setup for dependencies and config files

## Folder Structure

```
scripts/
+-- app/                  Main red-team execution orchestrator
|   +-- main.py           Dispatch entrypoint for all attack modes
|   +-- attacks/          Attack mode runners
|   |   +-- tap_attack_runner.py         Tree-of-Attacks with Pruning
|   |   +-- crescendo_attack_runner.py   Gradual multi-turn escalation
|   |   +-- xpia_attack_runner.py        Cross-Prompt Injection
|   |   +-- baseline_scan_runner.py      Default compliance scan
|   |   +-- batch_rescore_runner.py      Re-score existing DB results
|   +-- utils/
|       +-- generate_html_report.py      HTML/Markdown report generator
+-- analysis/             Result analysis and database import tools
+-- helper/               Setup and dataset helper scripts
```

---

## Attack Modes

All attack modes are launched via `app/main.py` with the `--attack-mode` flag:

```bash
python scripts/app/main.py --attack-mode <mode>
```

| Mode | Description | Key flags |
|------|-------------|-----------|
| `redteam` *(default)* | Standard multi-turn red-teaming | `--converters`, `--scorers`, `--datasets` |
| `tap` | Tree-of-Attacks with Pruning | `--tap-width`, `--tap-depth`, `--tap-branching-factor` |
| `crescendo` | Gradual multi-turn escalation | `--max-backtracks`, `--max-turns` |
| `xpia` | Cross-Prompt Injection | `--scenarios LLM02 LLM08` |
| `baseline` | Compliance scan (no attacker) | `--max-seeds` |
| `rescore` | Re-score stored DB results | `--filter-owasp`, `--scorers`, `--output-json` |
| `report` | Generate HTML/Markdown report | `--output-html`, `--output-md`, `--open` |

Use `--dry-run` with any mode to preview the execution plan without sending requests.

See full documentation in [`docs/script/attack_modes_overview.md`](../docs/script/attack_modes_overview.md).

---

## Workflow: Quick Start

### Phase 0: Configure environment and PyRIT config (first step)
```bash
# From samples/security-evaluator/

# Linux/macOS
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config

# Windows PowerShell
Copy-Item config/.env.local.example .env.local
Copy-Item config/.pyrit_config.example .pyrit_config
```

Model defaults in these templates include:
- Runner models in use: `llama3.2` (target), `mistral` (attacker), `phi3` (converter and scorers)
- PyRIT template defaults: `gpt-4o` (chat/frontend), `text-embedding-3-small` (embedding), `llama2` (generic Ollama target examples)

Optional preflight check:
```bash
python scripts/helper/verification/validate_redteam_config.py
```

If root config files are missing, create them from the templates:
```bash
python scripts/helper/verification/validate_redteam_config.py --fix
```

### Phase 1: Setup (run once)
```bash
cd samples/security-evaluator

# Linux/macOS
bash scripts/installers/setup_sqlite_linux.sh

# Windows
scripts\installers\setup_sqlite_windows.ps1
```

### Phase 2: Run Red Team Attack
```bash
cd samples/security-evaluator
python scripts/app/main.py
```

Selection examples:
```bash
# Run only specific converter / dataset / scorer choices
python scripts/app/main.py --converters base64 rot13 --datasets custom_datasets/banking_app_security_dataset.json --scorers substring self_ask_true_false

# Use a custom dataset file if a requested dataset is not built into PyRIT
python scripts/app/main.py --datasets ..\my_custom_dataset.prompt

# Run one built-in dataset and one custom dataset file together
python scripts/app/main.py --datasets custom_datasets/banking_app_security_dataset.json ..\my_custom_dataset.json

# Run with the included banking-app custom dataset sample
python scripts/app/main.py --datasets custom_datasets/banking_app_security_dataset.json
```

If no selectors are passed:
- datasets default to `custom_datasets/banking_app_security_dataset.json`
- scorers default to `self_ask_true_false`
- converters use each scenario's default mapped converter

This generates:
- `reports/scorer_outputs.json`  - All scorer results
- `reports/scorer_comparison.csv`  - Comparative analysis
- `reports/run_report.json`  - Run metadata
- `reports/report_summary.json`  - Hierarchical dataset->scorer summary + per-test-case execution summary + GUI import rows
- `reports/all_selection_comparison_report.json`  - Additional dataset/scorer comparison report when all datasets/scorers are used
- `reports/cases/`  - Per-case JSON reports (hierarchical)
- `reports/pyrit_ollama_demo.db`  - SQLite database with all results

### Phase 3: Analyze Results

**Option A: Command-line / notebook analysis** (primary)

**Option B: GUI analysis** *(optional — not required by the unified container workflow)*
```bash
# Follow docs/setup/gui_setup.md for optional GUI analysis setup
```

**Option C: Command-line analysis**
```bash
cd samples/security-evaluator/scripts/analysis

# View summary statistics
python analyze_json_reports.py --input-dir ../../reports/cases

# Export to CSV
python analyze_json_reports.py --format csv --output analysis.csv

# Query SQLite database
python query_sqlite_database.py --query count

# Get scores for specific scenario
python query_sqlite_database.py --query scores --filter-scenario LLM01
```

**Option D: Quick sanity checks**
```bash
cd samples/security-evaluator
python scripts/helper/verification/check_docs_links.py
python scripts/helper/verification/smoke_test_runner.py
python scripts/helper/verification/verify_sample_coverage.py
```

The coverage verifier validates that scripts support all scorer keys, all-datasets/all-scorers selection, report and log artifact structure, and the included banking custom dataset file.

---

## Folder Details

### `app/`
**Purpose**: Execute red-team attacks

| Script | Purpose | Usage |
|--------|---------|-------|
| `main.py` | Main OWASP LLM Top-10 red-team orchestrator | `python app/main.py` |

**Features**:
- Multi-turn RedTeamingAttack with 6-scorer comparison
- Automatically loads all PyRIT datasets
- Applies rotating converter set per scenario
- Persists all results to SQLite
- Hierarchical per-case report generation
- Retry logic with checkpoints
- Resume from interruption

---

### `analysis/`
**Purpose**: Analyze, import, and query red-team results

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_json_reports.py` | Batch analysis of per-case JSON reports | `python analysis/analyze_json_reports.py --input-dir ../../reports/cases` |
| `query_sqlite_database.py` | Direct SQLite database queries without GUI | `python analysis/query_sqlite_database.py --query count` |
| `import_scorer_json_to_memory.py` | *(optional)* Import scorer JSON into PyRIT SQLite memory for GUI analysis | `python analysis/import_scorer_json_to_memory.py --input-json ../../reports/scorer_outputs.json` |
| `import_json_helper.py` | *(optional)* Fallback manual JSON importer for GUI SQLite import (if primary unavailable) | `python analysis/import_json_helper.py --input ../../reports/scorer_outputs.json` |

**Common Workflows**:

1. **View summary statistics**
   ```bash
   python analysis/analyze_json_reports.py \
     --input-dir ../../reports/cases \
     --format summary
   ```

2. **Analyze specific OWASP scenario**
   ```bash
   python analysis/analyze_json_reports.py \
     --scenario LLM01 \
     --format detailed
   ```

3. **Export results to CSV for spreadsheet**
   ```bash
   python analysis/analyze_json_reports.py \
     --format csv \
     --output results.csv
   ```

4. **Query database for specific scorer**
   ```bash
   python analysis/query_sqlite_database.py \
     --query scores \
     --filter-scorer "GptClassifier"
   ```

5. **Get success rate statistics**
   ```bash
   python analysis/query_sqlite_database.py --query count
   ```

6. **Import report summary JSON into GUI SQLite (hierarchy + case summaries preserved)**
  ```bash
  python analysis/import_scorer_json_to_memory.py \
    --input-json ../../reports/report_summary.json
  ```

---

### `installers/`
**Purpose**: Environment and dependency initialization scripts
### `helper/`
**Purpose**: Script helpers and scaffold generators

| Script | Purpose | Usage |
|--------|---------|-------|
| `create_custom_dataset.py` | Generate custom dataset scaffold in JSON or PyRIT `.prompt`, and optionally emit PyRIT Python builder code | `python helper/dataset/create_custom_dataset.py --dataset-name my_dataset --description "My prompts" --dataset-type multi-turn --output-format pyrit-prompt --emit-pyrit-code` |
| `create_custom_dataset_production.py` | Generate production-ready dataset outputs with strict validation, atomic writes, and optional PyRIT parser validation | `python helper/dataset/create_custom_dataset_production.py --dataset-name prod_dataset --description "Production dataset" --dataset-type multi-turn --prompt "Turn 1" --prompt "Turn 2" --objective "Evaluate behavior" --output-format both` |
| `custom_dataset_validator.py` | Validate starter schema and PyRIT-compatible datasets | `python helper/dataset/custom_dataset_validator.py custom_dataset.json` |
| `production_dataset_validator.py` | Apply strict production dataset checks (naming, objective/group consistency, sequence continuity) | `python helper/dataset/production_dataset_validator.py custom_dataset.production.prompt` |
| `import_custom_dataset_to_memory.py` | Import `.json/.yaml/.yml/.prompt` datasets into SQLite memory in one command | `python helper/dataset/import_custom_dataset_to_memory.py --input custom_dataset.production.prompt --db-path reports/pyrit_ollama_demo.db` |

---


| Script | Purpose | Platform |
|--------|---------|----------|
| `setup_sqlite_linux.sh` | Install SQLite3 and Python dependencies | Linux/macOS |
| `setup_sqlite_windows.ps1` | Install SQLite3 and Python dependencies | Windows |

**Run once before first use**:
```bash
cd installers
# Linux/macOS
bash setup_sqlite_linux.sh

# Windows
.\setup_sqlite_windows.ps1
```

---

## Full Command Reference

### 1. **Initial Setup**
```bash
# Windows
scripts\installers\setup_sqlite_windows.ps1

# Linux/macOS
bash scripts/installers/setup_sqlite_linux.sh
```

### 2. **Run Red Team**
```bash
python scripts/app/main.py
```

### 3. **Analyze Results**

**Summary analysis**:
```bash
python scripts/analysis/analyze_json_reports.py \
  --input-dir reports/cases \
  --format summary
```

**Filter by scenario**:
```bash
python scripts/analysis/analyze_json_reports.py \
  --scenario LLM01 \
  --format detailed
```

**Export to CSV**:
```bash
python scripts/analysis/analyze_json_reports.py \
  --format csv \
  --output my_results.csv
```

**Database queries** (when SQLite import complete):
```bash
# List scorers
python scripts/analysis/query_sqlite_database.py --query scorers

# Show statistics
python scripts/analysis/query_sqlite_database.py --query count

# Get specific scores
python scripts/analysis/query_sqlite_database.py \
  --query scores \
  --filter-scenario LLM01 \
  --export scores_llm01.csv
```

### 4. **Import to GUI** (optional)
```bash
# Option 1: Use main importer
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json reports/scorer_outputs.json

# Option 2: Use fallback importer (if above fails)
python scripts/analysis/import_json_helper.py \
  --input reports/scorer_outputs.json
```

---

## Output Locations

After running `app/main.py`:

```
reports/
+-- artifacts/
|   +-- scorer_outputs.json           All scorer results (JSON)
|   +-- scorer_comparison.csv         Scorer comparison matrix
|   +-- run_report.json               Run metadata and timing
|   +-- cases/                        Per-case hierarchical reports
|       +-- LLM01/
|       |   +-- OWASP_LLM01_Red_Team_Risk.json
|       +-- LLM02/
|       |   +-- OWASP_LLM02_Insecure_Output_Handling.json
|       +-- ...

logs/
+-- run_TIMESTAMP.log                Production logs
+-- error_TIMESTAMP.log               Error logs

pyrit_ollama_demo.db                 SQLite database with all results
```

---

## Troubleshooting

### Setup Issues
See: `../docs/setup/README.md`

### Red Team Execution Issues
- Check: `logs/error_TIMESTAMP.log`
- Ensure: Ollama is running (`ollama serve`)
- Verify: Required models are installed (`ollama pull llama3.2 mistral phi3`)

### Analysis Issues
- **Analyze script shows "no reports found"**: Check `reports/cases/` directory exists
- **Database query shows empty results** *(only relevant if using optional GUI)*: Run importer: `python analysis/import_scorer_json_to_memory.py`
- **Import fails** *(only relevant if using optional GUI)*: Use fallback: `python analysis/import_json_helper.py`

---

## Next Steps

1. **First time**: Run setup → `app/main.py` → View results
2. **Iterate**: Modify converter/scorer sets in `app/main.py`
3. **Custom data**: Use `helper/dataset/custom_dataset_validator.py` to validate custom datasets
4. **Advanced**: See `docs/script/technical_reference.md` for PyRIT internals

---

## Documentation

- **Setup Guide**: `../docs/setup/README.md`
- **Script Usage**: `../docs/script/usage_guide.md`
- **Custom Datasets**: `../docs/script/custom_dataset_guide.md`
- **Technical Reference**: `../docs/script/technical_reference.md`

