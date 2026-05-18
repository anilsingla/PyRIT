# Configuration Field Reference

This document explains the fields in `.env.local` and `.pyrit_config` used by the `samples/security-evaluator` workflow.

## `.env.local` fields

### Model configuration

- `OLLAMA_ENDPOINT`
  - Example: `http://localhost:11434/v1`
  - Description: Ollama API endpoint for local or remote model access.

- `ALLOW_REMOTE_OLLAMA_ENDPOINT`
  - Default: `false`
  - Description: If `true`, allows Ollama endpoints outside localhost.

- `OLLAMA_TARGET_MODEL`
  - Default: `llama3.2`
  - Description: The model being tested by attacks.

- `OLLAMA_ATTACKER_MODEL`
  - Default: `mistral`
  - Description: The adversarial model that generates attack prompts.

- `OLLAMA_CONVERTER_MODEL`
  - Default: `phi3`
  - Description: Model used for LLM-based prompt converter operations.

- `OLLAMA_TF_SCORER_MODEL`
  - Default: `phi3`
  - Description: Model used for true/false response scoring.

- `OLLAMA_SCALE_SCORER_MODEL`
  - Default: `phi3`
  - Description: Model used for float-scale response scoring.

- `OLLAMA_REFUSAL_SCORER_MODEL`
  - Default: `phi3`
  - Description: Model used for refusal detection scoring.

- `OLLAMA_SCORER_MODEL`
  - Default: `phi3`
  - Description: Generic fallback scorer model; used if individual scorer models are not set.

- `OLLAMA_MODEL`
  - Default: `llama2`
  - Description: Optional generic Ollama target model used by some examples; not required for the sample runner.

### Output and artifact settings

- `ARTIFACTS_ROOT_PATH`
  - Default: `reports`
  - Description: Base folder where run artifacts are written.

- `LOGS_ROOT_PATH`
  - Default: `logs`
  - Description: Root folder for logs, checkpoints, and production logging.

- `PYRIT_SQLITE_DB_PATH`
  - Default: `reports/pyrit_ollama_demo.db`
  - Description: SQLite database path for PyRIT memory storage.

- `SCORER_COMPARISON_CSV_PATH`
  - Default: `reports/scorer_comparison.csv`
  - Description: CSV file path for flattened scorer comparison output.

- `SCORER_OUTPUTS_JSON_PATH`
  - Default: `reports/scorer_outputs.json`
  - Description: Detailed JSON payload of scorer results.

- `BATCH_SCORER_CHECK_JSON_PATH`
  - Default: `reports/batch_scorer_check.json`
  - Description: Batch rescore metadata file path.

- `RUN_REPORT_JSON_PATH`
  - Default: `reports/run_report.json`
  - Description: Consolidated run summary file path.

- `REPORTS_ROOT_PATH`
  - Default: `reports/cases`
  - Description: Root directory for per-case hierarchical reports.

### Execution control

- `PYRIT_MAX_TURNS`
  - Default: `4`
  - Description: Number of turns for multi-turn redteam-style attack flows.

- `PRINT_DATASET_SEEDS`
  - Default: `false`
  - Description: When `true`, prints a preview of seed prompts loaded from datasets.

- `DATASET_PREVIEW_ROWS`
  - Default: `3`
  - Description: Number of dataset rows to print when seed preview is enabled.

- `EXPORT_DETAILED_SCORES_JSON`
  - Default: `true`
  - Description: When `true`, exports detailed scorer JSON alongside summaries.

- `RUN_ALL_AVAILABLE_DATASETS`
  - Default: `false`
  - Description: When `true`, the runner attempts every available dataset per scenario.

- `MAX_DATASETS_PER_SCENARIO`
  - Default: `0`
  - Description: Upper limit of datasets per scenario; `0` means unlimited.

- `OLLAMA_MAX_RETRIES_PER_SCENARIO`
  - Default: `3`
  - Description: Number of retry attempts before giving up on a scenario.

- `OLLAMA_RETRY_WAIT_SECONDS`
  - Default: `5`
  - Description: Seconds to wait between retries.

- `RESUME_INCOMPLETE_RUN`
  - Default: `true`
  - Description: Enables checkpoint resume support when a run stops early.

### TAP mode settings

- `TAP_WIDTH`
  - Default: `3`
  - Description: Number of parallel branches explored by TAP.

- `TAP_BRANCHING_FACTOR`
  - Default: `2`
  - Description: Child nodes generated per branch.

- `TAP_DEPTH`
  - Default: `5`
  - Description: Maximum depth of the TAP tree search.

### Crescendo mode settings

- `CRESCENDO_MAX_BACKTRACKS`
  - Default: `5`
  - Description: Maximum number of backtracks the Crescendo attack can perform.

- `CRESCENDO_MAX_TURNS`
  - Default: `10`
  - Description: Maximum conversation turns for Crescendo.

### Baseline mode settings

- `BASELINE_MAX_SEEDS`
  - Default: `0`
  - Description: Maximum seed prompts per scenario for baseline mode (`0` = unlimited).

- `BASELINE_REPORT_PATH`
  - Default: `reports/baseline_scan_report.json`
  - Description: Output path for baseline summary JSON.

### Batch rescore settings

- `RESCORE_REPORT_PATH`
  - Default: `reports/rescore_report.json`
  - Description: Output path for the batch rescore report.

### HTML report settings

- `HTML_REPORT_PATH`
  - Default: `reports/run_report.html`
  - Description: Output path for the generated HTML report.

- `MD_REPORT_PATH`
  - Default: `reports/run_report.md`
  - Description: Output path for the generated Markdown report.

### Optional PyRIT target defaults

These values are optional and not required for the local Ollama sample.
They are used by other PyRIT examples when a generic OpenAI-style frontend is present.

- `DEFAULT_OPENAI_FRONTEND_ENDPOINT`
- `DEFAULT_OPENAI_FRONTEND_KEY`
- `DEFAULT_OPENAI_FRONTEND_MODEL`
- `OPENAI_CHAT_ENDPOINT`
- `OPENAI_CHAT_KEY`
- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_ENDPOINT`
- `OPENAI_EMBEDDING_KEY`
- `OPENAI_EMBEDDING_MODEL`

## `.pyrit_config` fields

This file is used by PyRIT backend tools to initialize memory and runtime context.

- `memory_db_type`
  - Description: Backend type used for memory storage.
  - Example: `sqlite`

- `operator`
  - Description: Optional runtime operator label recorded with memory entries.
  - Example: `local_redteam`

- `operation`
  - Description: Optional operation name recorded with memory entries.
  - Example: `owasp_ollama_example`

- `initializers`
  - Description: Optional list of backend initializer tools.
  - Example: `[]`

- `env_files`
  - Description: List of environment files loaded before startup.
  - Example: `['./.env.local']`

- `silent`
  - Description: When `true`, reduces non-error logging from PyRIT backend tools.
  - Example: `false`

## Example `.pyrit_config`

```yaml
memory_db_type: sqlite
operator: local_redteam
operation: owasp_ollama_example
initializers: []
env_files:
  - ./.env.local
silent: false
```

## How to use these files

1. Copy the template files into `samples/security-evaluator`.
2. Edit `.env.local` to match your Ollama endpoint, models, and artifact paths.
3. Edit `.pyrit_config` only if you need to change memory backend behavior or env file locations.
4. Keep `.env.local` and `.pyrit_config` aligned with the `samples/security-evaluator` sample folder.
