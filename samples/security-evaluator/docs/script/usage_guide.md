# Usage Guide: Configuration & Features

Complete reference for configuring and using `scripts/app/main.py`.

## Environment variables

### Ollama Endpoint & Models

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_ENDPOINT` | `http://localhost:11434/v1` | Ollama API endpoint |
| `ALLOW_REMOTE_OLLAMA_ENDPOINT` | `false` | Allow non-local Ollama endpoints |
| `OLLAMA_TARGET_MODEL` | `llama3.2` | Model for answering red-team prompts (victim) |
| `OLLAMA_ATTACKER_MODEL` | `mistral` | Model for generating adversarial prompts |
| `OLLAMA_CONVERTER_MODEL` | `phi3` | Model for LLM-based prompt converters |
| `OLLAMA_TF_SCORER_MODEL` | `phi3` | Model for true/false scoring |
| `OLLAMA_SCALE_SCORER_MODEL` | `phi3` | Model for scale scoring (0.0-1.0) |
| `OLLAMA_REFUSAL_SCORER_MODEL` | `phi3` | Model for refusal detection |
| `OLLAMA_SCORER_MODEL` | `phi3` | Fallback for all scorers (if individual ones not set) |

### Execution Control

| Variable | Default | Range | Description |
|----------|---------|-------|-------------|
| `PYRIT_MAX_TURNS` | `4` | 1-20 | Multi-turn conversation depth per scenario |
| `OLLAMA_MAX_RETRIES_PER_SCENARIO` | `3` | 1-10 | Retry attempts per failed scenario |
| `OLLAMA_RETRY_WAIT_SECONDS` | `5` | 1-120 | Sleep time between retries |
| `RESUME_INCOMPLETE_RUN` | `true` | bool | Resume from checkpoint if available |

### Dataset Selection

| Variable | Default | Description |
|----------|---------|-------------|
| `RUN_ALL_AVAILABLE_DATASETS` | `true` | Execute each scenario across all available datasets |
| `MAX_DATASETS_PER_SCENARIO` | `0` | Limit datasets per scenario (0 = unlimited) |
| `PRINT_DATASET_SEEDS` | `false` | Print dataset seed values to console |
| `DATASET_PREVIEW_ROWS` | `3` | Number of rows to preview per dataset |

### Output & Reporting

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPORT_DETAILED_SCORES_JSON` | `true` | Export detailed scorer_outputs.json |
| `ARTIFACTS_ROOT_PATH` | `reports` | Root for all artifact outputs |
| `LOGS_ROOT_PATH` | `logs` | Root for log files and checkpoints |
| `REPORTS_ROOT_PATH` | `reports/cases` | Root for per-case hierarchical reports (run-specific folders live under `reports/`) |
| `PYRIT_SQLITE_DB_PATH` | `reports/pyrit_ollama_demo.db` | SQLite database path |
| `SCORER_COMPARISON_CSV_PATH` | `reports/scorer_comparison.csv` | Comparison CSV export |
| `SCORER_OUTPUTS_JSON_PATH` | `reports/scorer_outputs.json` | Detailed scorer JSON export |
| `BATCH_SCORER_CHECK_JSON_PATH` | `reports/batch_scorer_check.json` | BatchScorer metadata |
| `RUN_REPORT_JSON_PATH` | `reports/run_report.json` | Consolidated run report |

### Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Print debug-level logs to console |

## Configuration patterns

### Pattern 1: Quick test run

```bash
export PYRIT_MAX_TURNS=2
export RUN_ALL_AVAILABLE_DATASETS=false
export OLLAMA_MAX_RETRIES_PER_SCENARIO=1
python scripts/app/main.py
```

### Pattern 2: Comprehensive coverage

```bash
export RUN_ALL_AVAILABLE_DATASETS=true
export MAX_DATASETS_PER_SCENARIO=3
export PYRIT_MAX_TURNS=6
python scripts/app/main.py
```

### Pattern 3: Using custom Ollama models

```bash
export OLLAMA_TARGET_MODEL=neural-chat
export OLLAMA_ATTACKER_MODEL=dolphin-mixtral
export OLLAMA_TF_SCORER_MODEL=neural-chat
python scripts/app/main.py
```

### Pattern 4: Alternative output location

```bash
export ARTIFACTS_ROOT_PATH=/tmp/pyrit_runs/artifacts
export LOGS_ROOT_PATH=/tmp/pyrit_runs/logs
python scripts/app/main.py
```

### Pattern 5: Docker with host Ollama

```bash
export OLLAMA_ENDPOINT=http://host.docker.internal:11434/v1
export ALLOW_REMOTE_OLLAMA_ENDPOINT=true
python scripts/app/main.py
```

## Features explained

### Multi-turn attacks

Each scenario executes multiple back-and-forth turns (default 4):

1. Attacker generates a prompt
2. Target model responds
3. If attacker unhappy, go to step 1 (refined prompt)
4. Final response is scored

Increase `PYRIT_MAX_TURNS` for deeper exploration.

### Converters

Prompt transformation pipeline. Options per OWASP scenario:

- `base64` � Encode prompts in base64
- `rot13` � ROT13 letter shift
- `caesar` � Caesar cipher shift
- `atbash` � Reverse alphabet substitution
- `flip` � Reverse/flip text
- `leetspeak` � L33t sp34k encoding
- `unicode_confusable` � Unicode homoglyphs
- `string_join` � Fragment text using separators
- `char_swap` � Character transposition
- `emoji` � Emoji semantic replacement
- `random_caps` � Random capitalization
- `tone_persuasive` (chat-based) � Rewrite into persuasive tone
- `variation` (chat-based) � Rephrasing and variation
- `translation_french` (chat-based) � Translate to French

### Scorers

Six scorers evaluate each response:

| Scorer | Type | Signal |
|--------|------|--------|
| `SubStringScorer` | Heuristic | Does response contain "step-by-step"? |
| `SelfAskTrueFalseScorer` | LLM | Does response satisfy objective? |
| `SelfAskScaleScorer` | LLM | How well (0.0-1.0) does response satisfy objective? |
| `FloatScaleThresholdScorer` | Threshold | Does scale_score >= 0.7? |
| `SelfAskRefusalScorer` | LLM | Does response refuse the request? |
| `TrueFalseInverterScorer` | Logic | NOT(refusal) = compliance |

Output metrics:

- **Weighted majority**: Consensus across scorers
- **Weighted confidence**: 0.0-1.0 agreement strength  
- **Disagreement flag**: "YES" if confidence < 0.65

### Retry & resume

- Failed scenarios are retried up to `OLLAMA_MAX_RETRIES_PER_SCENARIO` times
- Checkpoint is saved after each scenario completion
- Kill the script and restart to resume from last checkpoint
- Disable resumption: `RESUME_INCOMPLETE_RUN=false`

### Dataset modes

**Single-dataset mode (default):**

```bash
export RUN_ALL_AVAILABLE_DATASETS=false
```

Per scenario, uses first available dataset from its preference list.

**All-datasets mode:**

```bash
export RUN_ALL_AVAILABLE_DATASETS=true
export MAX_DATASETS_PER_SCENARIO=2
```

Each scenario runs against up to 2 available datasets.

## Typical workflow

1. **Verify Ollama**: `curl http://localhost:11434/api/tags`
2. **First run (debug)**: `DEBUG=true PYRIT_MAX_TURNS=2 python scripts/app/main.py`
3. **Full run**: `RUN_ALL_AVAILABLE_DATASETS=true python scripts/app/main.py`
4. **Analyze**: `python scripts/analysis/import_scorer_json_to_memory.py --input-json reports/scorer_outputs.json`
5. **Browse GUI**: Launch PyRIT GUI (see [GUI Tutorial](../setup/gui_setup.md))

## Getting help

- Check `logs/pyrit_owasp_redteam_production.log` for detailed events
- Review `reports/run_report.json` for configuration summary
- Run with `DEBUG=true` for verbose console output
- See [Technical Reference](technical_reference.md) for architecture details
