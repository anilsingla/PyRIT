# Baseline Scan - PromptSendingAttack

## Start here (recommended first mode)

If you are new to this sample, run baseline first. It is the easiest mode to understand.

Quick run:

```bash
python scripts/app/main.py --attack-mode baseline
```

## What it is

Baseline scan uses `PromptSendingAttack` to send raw prompts without an
adversarial attacker. This gives the default compliance rate before applying
stronger attacks.

## Why it matters

- Establishes a reference safety baseline
- Helps quantify attack lift (attack rate minus baseline rate)
- Useful for regression checks across model changes

## When to use baseline vs other modes

- Use baseline when you want a clean starting point.
- Use redteam/TAP/Crescendo after baseline to measure extra risk under stronger attacks.

## Configuration

```env
BASELINE_MAX_SEEDS=0
BASELINE_REPORT_PATH=reports/baseline_scan_report.json
```

## Usage

```bash
# Full baseline scan
python scripts/app/main.py --attack-mode baseline

# Fast smoke test (recommended first command)
python scripts/app/main.py --attack-mode baseline --max-seeds 3

# Limit seeds for fast checks
python scripts/app/main.py --attack-mode baseline --max-seeds 5

# Scenario and dataset filter
python scripts/app/main.py --attack-mode baseline --scenarios LLM01 --datasets airt_illegal

# Dry run
python scripts/app/main.py --attack-mode baseline --dry-run

# Standalone
python scripts/app/attacks/baseline_scan_runner.py --scenarios LLM01 --max-seeds 10
```

## Output

- Writes JSON to `baseline_scan_report.json`
- Includes per-scenario totals, compliant count, refused count, and rate

Typical interpretation:

- `>50%` compliance: critical baseline risk
- `10-50%` compliance: concerning
- `<10%` compliance: lower baseline risk, still run adversarial modes

## Next step

After baseline, run:
- [TAP Attack](tap_attack.md) for branching search
- [Crescendo Attack](crescendo_attack.md) for gradual escalation

## Related docs

- [TAP Attack](tap_attack.md)
- [Crescendo Attack](crescendo_attack.md)
- [HTML Report](html_report.md)
