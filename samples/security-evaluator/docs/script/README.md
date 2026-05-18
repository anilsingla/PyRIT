# Red-Team Script Documentation

Comprehensive guide to the Ollama + SQLite OWASP red-team sample scripts.

## Quick navigation

- **[Quickstart](quickstart.md)**  - Get running in 5 minutes
- **[Usage Guide](usage_guide.md)**  - Configuration, features, environment variables  
- **[Technical Reference](technical_reference.md)**  - Script internals and architecture
- **[Custom Dataset Guide](custom_dataset_guide.md)**  - Create and validate datasets

### Attack modes

- **[Attack Modes Overview](attack_modes_overview.md)**  - Comparison table and workflow guide
- **[TAP Attack](tap_attack.md)**  - Tree-of-Attacks with Pruning (systematic jailbreak search)
- **[Crescendo Attack](crescendo_attack.md)**  - Gradual multi-turn escalation
- **[XPIA Attack](xpia_attack.md)**  - Cross-Prompt Injection via external content (LLM02/LLM08)
- **[Baseline Scan](baseline_scan.md)**  - Default compliance rate without an attacker
- **[Batch Rescore](batch_scoring.md)**  - Re-score stored conversations with new scorers
- **[HTML Report](html_report.md)**  - Generate a visual HTML/Markdown report
- **[Dry Run](dry_run.md)**  - Preview execution plan without sending requests

## Overview

The `scripts/app/main.py` script orchestrates multi-turn red-team attacks against local LLMs:

- **10 OWASP LLM Top-10 scenarios** with harmful objectives
- **Converters** to transform prompts (base64, rot13, unicode, tone variation, translation)
- **Multi-scorer evaluation** (true/false, float scale, refusal detection, compliance checking)
- **Resilient execution** with retry/resume and checkpointing
- **Rich reporting**: CSV, JSON, per-case hierarchical outputs

## Output structure

```
reports/
  artifacts/
    pyrit_ollama_demo.db              # SQLite memory
    scorer_comparison.csv             # Flattened scorer results
    scorer_outputs.json               # Detailed scorer payloads
    batch_scorer_check.json           # BatchScorer applicability metadata
    run_report.json                   # Consolidated run summary
    cases/                            # Per-case hierarchical reports
      llm01_prompt_injection/
        airt_illegal/
          group_1/
            self_ask_true_false/
              case_00001_scenario_00000.json
logs/
  pyrit_owasp_redteam_production.log  # Structured audit log
  pyrit_owasp_redteam_production_checkpoint.json  # Resumable checkpoint
```

## Key features

| Feature | Benefit |
|---------|---------|
| **Multi-turn attacks** | Deep adversarial exploration |
| **Converter pipelines** | Prompt obfuscation and variation |
| **Multiple scorers** | Rich signal from different judge perspectives |
| **Retry & resume** | Resilience for long or flaky runs |
| **OWASP alignment** | Industry-standard harm categories |
| **SQLite persistence** | Easy querying and GUI analysis |
| **Detailed logging** | Audit trail for security review |

## Platform support

- ✅ Linux/macOS/Windows
- ✅ Local Ollama endpoint
- ✅ Docker (PyRIT in container, Ollama on host)
- ✅ All open-source Ollama models

## Recommended execution order

1. Setup environment: `scripts/installers/`
2. Run attacks: `scripts/app/main.py`
3. Analyze outputs: `scripts/analysis/`
4. Validate custom datasets: `scripts/helper/dataset/custom_dataset_validator.py`

## Next steps

- [Quickstart](quickstart.md) to run your first scenario
- [PyRIT Installation](../setup/README.md) for setup details
- [Usage Guide](usage_guide.md) for configuration tuning

