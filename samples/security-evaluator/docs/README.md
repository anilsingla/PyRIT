# Documentation Hub

Choose your learning path:

- **New here?** Start with [START_HERE.md](../START_HERE.md) for a simple-to-advanced step-by-step flow.

## Quick Start (5 minutes)

New to this package? Start here:
- [Start Here](../START_HERE.md) — Step-by-step path from first run to advanced modes
- [Security Evaluator User Guide](./SECURITY_EVALUATOR_USER_GUIDE.md) — full sample walkthrough from install through GUI and report analysis
- [Script Quickstart](script/quickstart.md) — run your first red-team scenario
- [PyRIT Local Setup](./setup/local_setup.md) — install PyRIT and dependencies

## PyRIT Platform Documentation

Learn how to install, configure, and use PyRIT:

- **[Security Evaluator User Guide](./SECURITY_EVALUATOR_USER_GUIDE.md)** - central walkthrough for setup, configuration, reports, and attack modes
- **[Local Installation](./setup/local_setup.md)** - Install PyRIT locally on Linux, macOS, or Windows
- **[Docker Setup](./setup/docker_setup.md)** - Run PyRIT in containers with host Ollama
- **[GUI Tutorial](./setup/gui_setup.md)** - Set up and use the PyRIT graphical interface for analysis
- **[GUI report transfer](./setup/gui_data_transfer.md)** - export/import JSON reports between run hosts and GUI hosts
- **[Configuration field reference](./script/configuration_fields.md)** - explicit `.env` and `.pyrit_config` field definitions
- **[Report analysis](./script/report_analysis.md)** - how to interpret generated output files and logs

### New to PyRIT?
Start with [PyRIT Installation Guide](./setup/README.md)

## Red-Team Script Documentation

Everything about `scripts/app/main.py`:

- **[Script Overview](script/README.md)** - Architecture, features, and output structure
- **[Quickstart](script/quickstart.md)** - Get running in 5 minutes
- **[Usage Guide](script/usage_guide.md)** - All configuration options and environment variables
- **[Technical Reference](script/technical_reference.md)** - Script internals, components, and extension points
- **[Custom Datasets](script/custom_dataset_guide.md)** - Author and validate custom attack datasets
- **[Artifacts and Outputs](script/artifacts.md)** - What files are generated and how to use them

### First time?
Start with [Script Quickstart](script/quickstart.md)

## Common Workflows

**I want to run a red-team attack:**
1. [PyRIT Local Setup](./setup/local_setup.md)
2. [Script Quickstart](script/quickstart.md)
3. Review results in `reports/`

**I want to analyze results interactively:**
1. Run red-team script
2. [Import scores](script/quickstart.md#analyzing-results)
3. [Open PyRIT GUI](./setup/gui_setup.md)
4. Review generated files in [Artifacts and Outputs](script/artifacts.md)

**I want to use custom attack prompts:**
1. Author dataset — see [Custom Datasets](script/custom_dataset_guide.md)
2. Validate with `custom_dataset_validator.py`
3. Configure script to use it
4. Run and review results

**I want to run everything in Docker:**
1. [Docker Setup](./setup/docker_setup.md)
2. [Script Quickstart](script/quickstart.md) (from within container)

## Runbook Essentials

Use this minimal operational flow for repeatable runs:

1. Start Ollama and verify models are available.
2. Run setup from [Local Installation](./setup/local_setup.md) or [Docker Setup](./setup/docker_setup.md).
3. Execute the runner script from [Script Quickstart](script/quickstart.md).
4. Review outputs under `reports/<attack_mode>/<datasets>/<scorers>/<timestamp>/`, `reports/<attack_mode>/<datasets>/<scorers>/<timestamp>/cases/`, and `logs/`.
5. Optionally import JSON for GUI browsing from [GUI Tutorial](./setup/gui_setup.md).

Security baseline:
- Keep `ALLOW_REMOTE_OLLAMA_ENDPOINT=false` unless explicitly required.
- Avoid exposing Ollama publicly without access controls.
- Treat logs and report artifacts as sensitive data.

## File Organization

```
docs/
  README.md (this file)
  setup/
    README.md
    local_setup.md
    docker_setup.md
    gui_setup.md
  script/
    README.md              ? Script overview and features
    quickstart.md          ? 5-minute quick start
    usage_guide.md         ? Complete configuration reference
    technical_reference.md ? Architecture and internals
    custom_dataset_guide.md ? Dataset creation and validation
```

## Troubleshooting

**Can't reach Ollama?**
- See [Docker Setup / Troubleshooting](./setup/docker_setup.md#troubleshooting) (applies to local too)

**Script hangs or crashes?**
- See [Script Quickstart / Troubleshooting](script/quickstart.md#troubleshooting)

**GUI won't load data?**
- See [GUI Tutorial / Troubleshooting](./setup/gui_setup.md#troubleshooting)

**Dataset validation failed?**
- See [Custom Datasets / Common Gotchas](script/custom_dataset_guide.md#common-gotchas)

## Next Steps

- Begin with [PyRIT Installation](./setup/README.md) or jump straight to [Script Quickstart](script/quickstart.md)
- Check out [samples/README.md](../../README.md) for other sample packs
