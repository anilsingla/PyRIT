# PyRIT Security Evaluator Quickstart

## 1. Onboarding Wizard
Run the setup wizard to check your environment:
```bash
python samples/security-evaluator/scripts/helper/onboarding_wizard.py
```

## 2. Example .env.local
```ini
OLLAMA_ENDPOINT=http://localhost:11434/v1
OLLAMA_TARGET_MODEL=llama3.2
OLLAMA_ATTACKER_MODEL=mistral
OLLAMA_CONVERTER_MODEL=phi3
OLLAMA_TF_SCORER_MODEL=phi3
OLLAMA_SCALE_SCORER_MODEL=llama2
OLLAMA_REFUSAL_SCORER_MODEL=mistral
OLLAMA_SCORER_MODEL=phi3
PYRIT_SQLITE_DB_PATH=reports/pyrit_ollama_demo.db
```

## 3. Example .pyrit_config
```yaml
memory_db_type: sqlite
operator: local_redteam
operation: owasp_ollama_example
initializers: []
env_files:
  - ./.env.local
silent: false
```

## 4. Run a Baseline Attack
```bash
python samples/security-evaluator/scripts/app/main.py --attack-mode baseline --dry-run
```

## 5. Jupyter Notebook Quickstart
Open `notebooks/Redteam_Quickstart_Template.ipynb` in JupyterLab.

## 6. Generate Markdown Report
```bash
python samples/security-evaluator/scripts/helper/generate_markdown_report.py
```
