# TAP - Tree-of-Attacks with Pruning

## When to use TAP

Use TAP after you complete a baseline run. TAP is an advanced mode for deeper jailbreak exploration.

Suggested order:
1. Baseline
2. Redteam
3. TAP

## What it is

TAP is a systematic multi-branch jailbreak strategy. Instead of trying one
attack prompt, TAP expands a tree of attack variants and prunes weak branches.

## Why it matters

- Better coverage than one-shot attacks
- Finds jailbreak phrasings missed by linear exploration
- Produces more stable red-team signal per OWASP scenario

## Core parameters

- `width`: number of parallel branches
- `branching_factor`: number of children per branch
- `depth`: max branch depth

## Configuration

```env
TAP_WIDTH=3
TAP_BRANCHING_FACTOR=2
TAP_DEPTH=5
```

## Usage

```bash
# All scenarios
python scripts/app/main.py --attack-mode tap

# Beginner-friendly first TAP run
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-width 2 --tap-depth 2 --dry-run

# Scenario subset with custom tree shape
python scripts/app/main.py --attack-mode tap \
  --scenarios LLM01 LLM07 \
  --tap-width 5 --tap-branching-factor 2 --tap-depth 8

# Dry run
python scripts/app/main.py --attack-mode tap --dry-run

# Standalone
python scripts/app/attacks/tap_attack_runner.py --scenarios LLM01 --width 3 --depth 5
```

## Output

- Attack results are persisted in SQLite memory with `attack_mode=tap`
- Console prints per-scenario outcome and scorer comparison

Generate a visual report:

```bash
python scripts/app/main.py --attack-mode report --output-html reports/tap_report.html --open
```

## Compare with baseline

```bash
python scripts/app/main.py --attack-mode baseline --scenarios LLM01
python scripts/app/main.py --attack-mode tap --scenarios LLM01
```

Use baseline vs TAP deltas to quantify attack lift.

## Practical tuning guide

- Start small: `--tap-width 2 --tap-depth 2`
- Increase depth if attacks look too shallow
- Increase width if outcomes are unstable across runs
- Keep branching factor low first (`2`) to control cost/time
