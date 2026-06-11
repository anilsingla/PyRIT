# Glossary

This glossary is written for people who are new to PyRIT and AI red teaming.
It covers platform terms, attack workflow terms, and security-evaluator sample terms.

## Core PyRIT concepts

- **PyRIT**: Python Risk Identification Tool for generative AI. It provides reusable components to run adversarial tests, score model behavior, and store analysis artifacts.
- **Prompt**: Input text sent to a model. A prompt can be a question, instruction, policy test, or adversarial payload.
- **Context prompt**: Prompt text supplied as background where no direct answer is expected.
- **Response**: Model output generated from a prompt.
- **Conversation**: Ordered turns of prompts and responses, often multi-turn in adversarial tests.
- **Session**: A logical run context containing one or more conversations and associated metadata.
- **Fork (session)**: Creating a new path from an existing conversation state to test alternative follow-up prompts.
- **Target model**: The model/system under test.
- **Attacker model**: A model used to generate or refine adversarial prompts against the target model.
- **Converter**: A transformation that changes prompt representation (for example obfuscation or paraphrase) to test robustness.
- **Scorer**: A component that evaluates model output (for example success/failure, refusal, or numeric risk score).
- **Memory backend**: Persistent storage used by PyRIT for conversations, scores, and labels (for example SQLite).

## Security-evaluator sample terms

- **security-evaluator**: The sample package under samples/security-evaluator that combines runner scripts, docs, API, and installer tooling for local red-team evaluation.
- **Attack mode**: Runner strategy selected through --attack-mode in scripts/app/main.py.
- **Dataset**: Collection of seed prompts used to exercise scenarios.
- **Seed prompt**: Initial prompt entry from a dataset used to start a test case.
- **Scenario**: OWASP-aligned category (for example LLM01) that groups attack objectives and evaluation criteria.
- **Case report**: Per-case JSON artifact with scenario, dataset, scorer payload, and status/error fields.
- **Run report**: Aggregated run-level summary artifact.
- **Checkpoint resume**: Ability to continue interrupted runs based on persisted state metadata.

## Attack and utility modes

- **baseline**: Non-adversarial control run using prompt sending only.
- **redteam**: Primary adversarial workflow that supports single-turn and multi-turn operation.
- **tap**: Tree-of-Attacks with Pruning; explores branching adversarial paths.
- **crescendo**: Escalating multi-turn attack with backtracking controls.
- **xpia**: Cross-Prompt Injection Attack simulation.
- **rescore**: Recompute scorer outputs from stored records without rerunning attacks.
- **report**: Generate HTML/Markdown/JSON summaries from existing artifacts.

## Scoring terms

- **true_false score**: Binary score (for example objective achieved or not achieved).
- **float_scale score**: Numeric/graded score used for severity or confidence ranges.
- **refusal score**: Score indicating whether the model refused unsafe content.
- **score rationale**: Human-readable reason emitted by scorer logic.
- **score metadata**: Structured tags (scenario, dataset, model identifiers, etc.) attached to a score entry.

## Artifact and analysis terms

- **scorer_outputs.json**: Detailed scorer payload artifact, commonly used for GUI import.
- **scorer_comparison.csv**: Flattened tabular scorer output for spreadsheet analysis.
- **reports/cases/**: Hierarchical per-case JSON outputs.
- **logs/**: Runtime and operational logs; may contain sensitive prompt/response text.
- **GUI import**: Loading scorer_outputs.json into SQLite so the PyRIT GUI can query and visualize results.

## Security and operations terms

- **Local-only bind**: Service host binding to localhost or 127.0.0.1 so endpoints are not reachable externally.
- **Remote bind**: Service host binding to non-local interfaces (for example 0.0.0.0) so external clients can connect.
- **Bearer token auth**: HTTP Authorization: Bearer token validation used to protect API endpoints.
- **Least exposure default**: Secure default where network/service exposure is minimized unless explicitly enabled.
- **Sensitive artifacts**: Reports/logs that may contain prompts, model responses, policy bypass attempts, and risk evidence.

## Recommended newcomer reading order

1. about_pyrit.md (platform purpose and architecture)
2. this glossary (terms and definitions)
3. samples/security-evaluator/START_HERE.md (guided workflow)
4. samples/security-evaluator/docs/SECURITY_EVALUATOR_USER_GUIDE.md (full operational walkthrough)
