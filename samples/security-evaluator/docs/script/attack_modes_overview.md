# Attack Modes Overview

Use attack modes with:

```bash
python scripts/app/main.py --attack-mode <mode>
```

## Mode comparison

| Mode | Backend | Attacker LLM | Multi-turn | Best for |
|---|---|---:|---:|---|
| `redteam` | `RedTeamingAttack` | yes | yes | Default OWASP sweep |
| `tap` | `TAPAttack` | yes | yes | Systematic jailbreak search |
| `crescendo` | `CrescendoAttack` | yes | yes | Escalation and backtracking |
| `xpia` | `XPIATestWorkflow` | no | no | Indirect prompt injection |
| `baseline` | `PromptSendingAttack` | no | no | Baseline compliance rate |
| `rescore` | scorer pipeline | no | no | Re-score stored outputs |
| `report` | report generator | no | no | HTML/Markdown report generation |

## Quick examples

```bash
python scripts/app/main.py
python scripts/app/main.py --attack-mode tap --scenarios LLM01 --tap-width 5
python scripts/app/main.py --attack-mode crescendo --scenarios LLM06 --max-turns 12
python scripts/app/main.py --attack-mode xpia
python scripts/app/main.py --attack-mode baseline --max-seeds 5
python scripts/app/main.py --attack-mode rescore --scorers self_ask_true_false
python scripts/app/main.py --attack-mode report --open
```

Standalone runner examples:

```bash
python scripts/app/attacks/redteam_attack_runner.py --dry-run
python scripts/app/attacks/tap_attack_runner.py --scenarios LLM01 --width 3 --depth 5
python scripts/app/attacks/crescendo_attack_runner.py --scenarios LLM06 --max-backtracks 5
python scripts/app/attacks/redteam_attack_runner.py --converters base64 --dry-run
```

Notes:
- Standalone TAP/Crescendo/Redteam runners now emit both compact and detailed scorer logs.
- Standalone runners also write dual screen+file logs via `pyrit_sec_eval_logs/`.
- Spinner and live scorer feed are configurable via `ENABLE_WAIT_SPINNER` and `ENABLE_LIVE_SCORER_FEED`.
- In dependency-limited environments, runner `--dry-run` still validates CLI paths and surfaces the missing runtime module clearly.

## Related docs

- [TAP Attack](tap_attack.md)
- [Crescendo Attack](crescendo_attack.md)
- [XPIA Attack](xpia_attack.md)
- [Baseline Scan](baseline_scan.md)
- [Batch Rescore](batch_scoring.md)
- [HTML Report](html_report.md)
- [Dry Run](dry_run.md)
