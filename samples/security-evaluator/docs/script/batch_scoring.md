# Batch Re-Scoring

## What it is

Batch re-scoring reads stored assistant outputs from SQLite memory and runs the
selected scorer suite again without rerunning attacks.

## Why it matters

- Apply new scorers to historical outputs
- Re-evaluate with upgraded scorer models
- Produce updated reports quickly

## Configuration

```env
RESCORE_REPORT_PATH=reports/rescore_report.json
```

## Usage

```bash
# Re-score all stored outputs
python scripts/app/main.py --attack-mode rescore

# Filter by OWASP IDs
python scripts/app/main.py --attack-mode rescore --filter-owasp LLM01 LLM02

# Restrict scorer keys
python scripts/app/main.py --attack-mode rescore --scorers self_ask_true_false refusal

# Custom output JSON
python scripts/app/main.py --attack-mode rescore --output-json reports/rescore_v2.json

# Dry run
python scripts/app/main.py --attack-mode rescore --dry-run

# Standalone
python scripts/app/attacks/batch_rescore_runner.py --filter-owasp LLM01 --scorers self_ask_true_false
```

## Output

- Writes JSON rows with conversation id, OWASP id, score summary, and details
- Keeps original attack evidence intact while updating analysis layer

## Related docs

- [HTML Report](html_report.md)
- [Technical Reference](technical_reference.md)
- [Baseline Scan](baseline_scan.md)
