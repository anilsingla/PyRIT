# Quickstart: Running the Red-Team Script

Get the Ollama + SQLite OWASP red-team script up and running in 5 minutes.

## Setup (pick one)

### Option A: Local machine

Linux/macOS:

```bash
# Setup PyRIT and SQLite
cd samples/security-evaluator
bash scripts/installers/setup_sqlite_linux.sh
```

Windows PowerShell:

```powershell
Set-Location samples/security-evaluator
.\scripts\installers\setup_sqlite_windows.ps1
```

### Option B: Docker

```bash
cd docker
docker-compose up -d
docker-compose exec pyrit bash
cd samples/security-evaluator
```

## Run the script

```bash
# Start Ollama locally first
ollama serve

# In a new terminal, run the red-team script
python scripts/app/main.py
```

The script will:

1. Discover built-in datasets
2. Initialize SQLite memory
3. Execute 10 OWASP scenarios with converters
4. Score each response with 6 scorers
5. Retry failed scenarios
6. Export results to CSV, JSON, and per-case reports
7. Print summary tables

## Outputs

```
reports/               ← CSV, JSON exports
reports/cases/         ← Per-scorer per-dataset reports
logs/                            ← Production log + checkpoint
```

## Common commands

**Run a quick dry-run (no prompts sent):**

```bash
python scripts/app/main.py --dry-run --local-datasets-only
```

**Run the standalone RedTeam runner (dual screen+file logs):**

```bash
python scripts/app/attacks/redteam_attack_runner.py --dry-run
python scripts/app/attacks/redteam_attack_runner.py --scorers self_ask_true_false refusal
```

Standalone runner logs are written to `pyrit_sec_eval_logs/` while still streaming to the console.

**Test with smaller dataset:**

```bash
MAX_DATASETS_PER_SCENARIO=1 python scripts/app/main.py
```

**Use different Ollama models:**

```bash
OLLAMA_TARGET_MODEL=neural-chat OLLAMA_ATTACKER_MODEL=llama2 \
  python scripts/app/main.py
```

**Resume interrupted run:**

```bash
RESUME_INCOMPLETE_RUN=true python scripts/app/main.py
```

## Analyzing results

### CSV summary

```bash
cat reports/scorer_comparison.csv
```

Shows per-scenario scorer agreement and weighted confidence.

### Full JSON details

```bash
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json reports/scorer_outputs.json
```

Then open PyRIT GUI to browse results.

### Per-case drill-down

```bash
ls reports/cases/llm01_prompt_injection/
```

Find individual case JSON files for detailed analysis.

## Environment customization

Create a `.env` file or export variables:

```bash
# Models
OLLAMA_TARGET_MODEL=mistral
OLLAMA_ATTACKER_MODEL=llama3.2

# Execution
PYRIT_MAX_TURNS=5
OLLAMA_MAX_RETRIES_PER_SCENARIO=2

# Output
RUN_ALL_AVAILABLE_DATASETS=true
MAX_DATASETS_PER_SCENARIO=2

# Debugging
DEBUG=true
PRINT_DATASET_SEEDS=false
```

For a complete list, see [Usage Guide](usage_guide.md).

## Troubleshooting

**"Connection refused" or "Cannot reach Ollama"**

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Or restart
ollama serve
```

**"Model not found"**

```bash
# List available models
ollama list

# Pull a model
ollama pull llama3.2
```

**"Database locked"**

- Another instance is running the script
- Wait for it to finish or use a different `PYRIT_SQLITE_DB_PATH`

**Script hangs or times out**

- Lower `PYRIT_MAX_TURNS` to reduce per-scenario complexity
- Increase `OLLAMA_RETRY_WAIT_SECONDS` for slow systems

## Next steps

- [Full Usage Guide](usage_guide.md) for all configuration options
- [Technical Reference](technical_reference.md) for script internals
- [Custom Dataset Guide](custom_dataset_guide.md) to author datasets
- [PyRIT GUI Tutorial](../setup/gui_setup.md) for visual analysis

