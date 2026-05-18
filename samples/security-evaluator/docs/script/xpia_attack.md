# XPIA - Cross-Prompt Injection Attack

## When to use XPIA

Use XPIA to test indirect prompt injection risks (for example: retrieved content, tool output, external text).

Suggested order:
1. Baseline
2. Redteam
3. XPIA (focused injection testing)

## What it is

XPIA tests indirect prompt injection. The attacker embeds hidden instructions
inside content that the model processes later (for example, retrieved text or
tool output).

## Why it matters

- Covers indirect injection risk not visible in direct chat-only tests
- Targets OWASP LLM02 and LLM08 style failures
- Useful for agentic and RAG pipelines

## Usage

```bash
# Default scenarios (LLM02, LLM08)
python scripts/app/main.py --attack-mode xpia

# Beginner-friendly first XPIA run
python scripts/app/main.py --attack-mode xpia --scenarios LLM02 --dry-run

# Scenario filter
python scripts/app/main.py --attack-mode xpia --scenarios LLM08

# Dry run
python scripts/app/main.py --attack-mode xpia --dry-run

# Standalone
python scripts/app/attacks/xpia_attack_runner.py --scenarios LLM02 LLM08
```

## Output

- Results are stored with `attack_mode=xpia`
- Console output includes workflow status and score

## Practical tip

Start with `LLM02`, then add `LLM08` once the first run is stable.

## Related docs

- [TAP Attack](tap_attack.md)
- [Crescendo Attack](crescendo_attack.md)
- [Technical Reference](technical_reference.md)
