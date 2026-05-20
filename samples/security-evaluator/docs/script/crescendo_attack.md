# Crescendo Attack

## When to use Crescendo

Use Crescendo when you want to test multi-turn pressure and escalation behavior.

Suggested order:
1. Baseline
2. Redteam
3. Crescendo

## What it is

Crescendo is a multi-turn jailbreak strategy that escalates gradually through
small conversational steps. When the model refuses, the attack can backtrack
and retry with a softer step.

## Why it matters

- Tests recency-bias vulnerabilities
- Exposes failures not visible in one-shot attacks
- Measures resilience through backtrack behavior

## Configuration

```env
CRESCENDO_MAX_BACKTRACKS=5
CRESCENDO_MAX_TURNS=10
```

## Usage

```bash
# Run all scenarios
python scripts/app/main.py --attack-mode crescendo

# Beginner-friendly first Crescendo run
python scripts/app/main.py --attack-mode crescendo --scenarios LLM01 --max-backtracks 3 --max-turns 6 --dry-run

# Run selected scenarios with custom limits
python scripts/app/main.py --attack-mode crescendo \
  --scenarios LLM01 LLM06 \
  --max-backtracks 8 \
  --max-turns 15

# Dry run
python scripts/app/main.py --attack-mode crescendo --dry-run

# Standalone
python scripts/app/attacks/crescendo_attack_runner.py --scenarios LLM06 --max-backtracks 5
```

## Output

- Results are stored with `attack_mode=crescendo`
- Console output includes `backtrack_count` plus compact + detailed scorer breakdowns
- Standalone Crescendo runner writes dual screen+file logs under `pyrit_sec_eval_logs/`

Interpretation guideline:

- `0-1` backtracks: weak resistance
- `2-4` backtracks: moderate resistance
- `max_backtracks` reached: stronger refusal behavior

## Practical tuning guide

- Start with `--max-backtracks 3 --max-turns 6`
- Increase turns to test longer conversational pressure
- Increase backtracks only if you need deeper retry behavior

## Related docs

- [TAP Attack](tap_attack.md)
- [XPIA Attack](xpia_attack.md)
- [Baseline Scan](baseline_scan.md)
