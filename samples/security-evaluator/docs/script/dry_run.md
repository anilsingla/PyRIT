# Dry Run Mode

## What it is

`--dry-run` prints the execution plan without sending requests to Ollama or
running attacks.

## Usage examples

```bash
python scripts/app/main.py --dry-run
python scripts/app/main.py --attack-mode tap --dry-run --scenarios LLM01
python scripts/app/main.py --attack-mode crescendo --dry-run --scenarios LLM06
python scripts/app/main.py --attack-mode xpia --dry-run
python scripts/app/main.py --attack-mode baseline --dry-run --max-seeds 5
python scripts/app/main.py --attack-mode rescore --dry-run --filter-owasp LLM01
```

## Why use it

- Validate scenario and dataset filters
- Confirm selected scorer keys
- Verify run scope before long executions

## Related docs

- [Attack Modes Overview](attack_modes_overview.md)
- [Usage Guide](usage_guide.md)
