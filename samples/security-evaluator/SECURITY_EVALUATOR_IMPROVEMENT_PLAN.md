# Security Evaluator Improvement Plan

## 1. Usability & Developer Experience
- Add a unified web dashboard (Streamlit/FastAPI+React) for visualizing attack results and exporting reports.
- Enhance CLI with subcommands (e.g., `pyrit scan`, `pyrit report`).
- Support YAML/JSON “attack profiles” for quick scenario switching.
- Provide ready-to-run Jupyter notebook templates for red-teaming tasks.

## 2. Automation & CI/CD
- Integrate with GitHub Actions to run security-evaluator on PRs or nightly.
- Expose a REST API for launching evaluations and retrieving results programmatically.

## 3. Reporting & Analytics
- Generate HTML/PDF reports with charts, summaries, and model comparison tables.
- Add trend analysis to track model performance over time.
- Support CSV, JSON, and Markdown exports for all result types.

## 4. Attack & Scoring Features
- Allow custom attack strategies via a plugin interface.
- Support ensemble scoring (multiple models vote on pass/fail).
- Add LLM-based explanations for scoring decisions.

## 5. Security & Compliance
- Implement audit logging for all evaluation runs.
- Add basic authentication and role-based access for dashboard/API.

## 6. Extensibility
- Add plug-and-play support for Azure OpenAI, Google Vertex, AWS Bedrock, etc.
- Integrate with public red-teaming datasets or allow users to share datasets.

## 7. Documentation & Onboarding
- Add an interactive setup wizard (CLI or web-based) for config generation and validation.
- Provide video tutorials for setup and usage.
- Expand troubleshooting guide with common errors and solutions.

---

## Implementation Progress (May 2026)

- [x] Interactive onboarding wizard script added: `scripts/helper/onboarding_wizard.py`
- [x] Jupyter notebook quickstart template: `notebooks/Redteam_Quickstart_Template.ipynb`
- [x] Basic Markdown report generator: `scripts/helper/generate_markdown_report.py`

See the respective files for usage instructions.
