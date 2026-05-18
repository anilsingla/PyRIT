# PyRIT Installation & Setup

Select your preferred setup method:

- **[Local Installation](local_setup.md)**  - Install PyRIT directly on your machine.
- **[Docker Setup](docker_setup.md)**  - Run PyRIT in containers with host Ollama integration.
- **[GUI Tutorial](gui_setup.md)**  - Set up and run the PyRIT GUI for analysis and scoring.
- **[GUI report transfer](gui_data_transfer.md)** - Move generated JSON reports between run hosts and GUI hosts.
- **[Security Evaluator User Guide](../SECURITY_EVALUATOR_USER_GUIDE.md)** - full sample walkthrough from install through GUI and report analysis.

## Quick start (new users)

1. Use [Local Installation](local_setup.md) first.
2. Run one baseline execution: `python scripts/app/main.py`.
3. Open [GUI Tutorial](gui_setup.md) to inspect results.
4. If you want a guided install, run `python scripts/installers/install_security-evaluator.py` from `samples/security-evaluator/`.

The guided installer now also supports generating API service wrapper files for Linux/macOS/Windows,
and can install/start services on the current host OS.

If you prefer containerized execution, use [Docker Setup](docker_setup.md) instead of local setup.

