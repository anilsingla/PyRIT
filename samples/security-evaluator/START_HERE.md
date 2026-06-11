# RedTeam Ollama  - Start Here

This is the main entry guide for this sample.

For a complete, sequential walkthrough from install through GUI and report analysis, also see [Security Evaluator User Guide](docs/SECURITY_EVALUATOR_USER_GUIDE.md).

Use this file when you want to go from **first run** to **advanced red-team workflows** in a safe order.

## What this sample does

It helps you red-team local LLMs (via Ollama) using:
- OWASP-aligned attack scenarios
- multiple attack modes (baseline, redteam, TAP, Crescendo, XPIA)
- scorer-based analysis and reports
- optional API and service hosting
- generated artifacts, logs, and result review flows

---

## Learning path (simple → advanced)

## Step 1  - Setup your environment (first time only)

Pick one setup path:
- Local: [docs/setup/local_setup.md](docs/setup/local_setup.md)
- Docker: [docs/setup/docker_setup.md](docs/setup/docker_setup.md)

Recommended Python version for local installs: 3.11 or 3.12.

If you want one guided installer, use:
```bash
python scripts/installers/install_security_evaluator.py
```

The installer can also generate API service wrapper files for Windows, Linux, and macOS,
and install/start the service on the current host OS when run with admin/sudo privileges.

If you prefer to set things up manually, copy the config templates in `samples/security-evaluator/`:

Linux/macOS:
```bash
cp config/.env.local.example .env.local
cp config/.pyrit_config.example .pyrit_config
```

Windows PowerShell:
```powershell
Copy-Item config/.env.local.example .env.local
Copy-Item config/.pyrit_config.example .pyrit_config
```

Optional config validation:
```bash
python scripts/helper/verification/validate_redteam_config.py
```

You can also use the interactive installer above to create both config files and validate them in one flow.

---

## Step 2  - Run your first safe check (dry run)

Preview execution without sending prompts:
```bash
python scripts/app/main.py --dry-run
```

Why this matters:
- verifies your setup and paths
- shows planned scenarios/datasets/modes before actual execution

---

## Step 3  - Run baseline mode (recommended first real run)

Baseline is simplest and safest to interpret.

```bash
python scripts/app/main.py --attack-mode baseline
```

Learn baseline details: [docs/script/baseline_scan.md](docs/script/baseline_scan.md)

---

## Step 4  - Run core red-team mode

Run the standard adversarial workflow:
```bash
python scripts/app/main.py --attack-mode redteam
```

Fast single-scenario test:
```bash
python scripts/app/main.py --attack-mode redteam --scenarios LLM01 --dry-run
```

Main script docs:
- [docs/script/quickstart.md](docs/script/quickstart.md)
- [docs/script/usage_guide.md](docs/script/usage_guide.md)

---

## Step 5  - Review results

Generated outputs are under:
- `reports/` (JSON/CSV/run summary)
- `reports/cases/` (per-case hierarchical reports)
- `logs/` (runtime logs)

Optionally, use the GUI for interactive analysis (see the Optional section in [docker_setup.md](docs/setup/docker_setup.md) for how it accesses the same SQLite database):
- [docs/setup/gui_setup.md](docs/setup/gui_setup.md) *(optional)*

Understand the output files first:
- [docs/script/artifacts.md](docs/script/artifacts.md)

Generate HTML report:
```bash
python scripts/app/main.py --attack-mode report --open
```

---

## Step 6  - Move to advanced attack modes

Use these after baseline + redteam:

- TAP (tree search): [docs/script/tap_attack.md](docs/script/tap_attack.md)
- Crescendo (gradual escalation): [docs/script/crescendo_attack.md](docs/script/crescendo_attack.md)
- XPIA (indirect injection): [docs/script/xpia_attack.md](docs/script/xpia_attack.md)

Mode overview: [docs/script/attack_modes_overview.md](docs/script/attack_modes_overview.md)

---

## Step 7  - Custom data, rescoring, and repeatable operations

- Custom datasets: [docs/script/custom_dataset_guide.md](docs/script/custom_dataset_guide.md)
- Batch rescoring: [docs/script/batch_scoring.md](docs/script/batch_scoring.md)
- Full technical internals: [docs/script/technical_reference.md](docs/script/technical_reference.md)

## Step 8  - Sanity checks and repeatability

Run these when you change docs or runner wiring:

```bash
python scripts/helper/verification/check_docs_links.py
python scripts/helper/verification/smoke_test_runner.py
```

---

## Optional: API and background services

If you want to run this as an API/service:

- API setup: [api/API_SETUP_GUIDE.md](api/API_SETUP_GUIDE.md)
- Services (Windows/Linux/macOS): [scripts/installers/app_service/SERVICES_GUIDE.md](scripts/installers/app_service/SERVICES_GUIDE.md)

---

## Quick command cheat sheet

```bash
# 1) Dry run
python scripts/app/main.py --dry-run

# 2) Baseline
python scripts/app/main.py --attack-mode baseline

# 3) Core redteam
python scripts/app/main.py --attack-mode redteam

# 4) Report
python scripts/app/main.py --attack-mode report --open
```

---

## If you are completely new

Start in this order:
1. [docs/setup/local_setup.md](docs/setup/local_setup.md)
2. [docs/script/quickstart.md](docs/script/quickstart.md)
3. Run baseline
4. Run redteam
5. Open GUI/report

That gives a clean progression from basic validation to full adversarial testing.
