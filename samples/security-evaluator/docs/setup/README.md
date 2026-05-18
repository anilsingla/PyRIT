# PyRIT Installation & Setup

Select your preferred setup method:

- **[Local Installation](local_setup.md)**  - Install PyRIT directly on your machine.
- **[Docker Setup](docker_setup.md)**  - Run PyRIT in containers with host Ollama integration.
- **[GUI Tutorial](gui_setup.md)** *(optional)* — Graphical interface for interactive result analysis.
- **[GUI report transfer](gui_data_transfer.md)** *(optional)* — Move JSON reports between run host and GUI host (only needed when using GUI on a different machine).
- **[Security Evaluator User Guide](../SECURITY_EVALUATOR_USER_GUIDE.md)** - full sample walkthrough from install through Jupyter-based analysis and reports.

## Quick start (new users)

1. Use [Local Installation](local_setup.md) first.
2. Run one baseline execution: `python scripts/app/main.py`.
3. Review results in `reports/` (CSV/JSON) or open the JupyterLab notebook.
4. If you want a guided install, run `python scripts/installers/install_security-evaluator.py` from `samples/security-evaluator/`.
5. *(Optional)* Open [GUI Tutorial](gui_setup.md) if you want interactive GUI analysis.

The guided installer now also supports generating API service wrapper files for Linux/macOS/Windows,
and can install/start services on the current host OS.

If you prefer containerized execution, use [Docker Setup](docker_setup.md) instead of local setup.

