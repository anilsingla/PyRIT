# PyRIT GUI Tutorial

> Advanced / Optional
>
> This page covers the optional graphical interface workflow. The unified container quick start does not require the GUI.

Set up and use the PyRIT graphical interface for interactive red-team analysis.

## What is the PyRIT GUI?

The PyRIT GUI is a web-based interface (Streamlit) that allows you to:

- Browse and query red-team conversations from SQLite
- Visualize scorer results and metrics
- Analyze multi-turn attack flows
- Filter by OWASP categories, datasets, and models
- Search prompt/response content

## Starting the GUI locally

### Prerequisites

- PyRIT installed locally (see [Local Setup](local_setup.md))
- SQLite database with red-team data (`pyrit_ollama_demo.db`)
- Port 8501 available

### Launch GUI

From the PyRIT repository root:

```bash
# If using default installation
cd doc/code
python pyrit_gui.py

# Or if using venv
source .venv/bin/activate  # or .venv\Scripts\Activate on Windows
cd doc/code
python pyrit_gui.py
```

The GUI will open at: `http://localhost:8501`

## Starting the GUI in Docker

From the repository root:

```bash
cd docker/
docker-compose up pyrit-gui
```

GUI available at: `http://localhost:8501`

**Share host Ollama with container:**

Edit `docker-compose.yaml`:

```yaml
services:
  pyrit-gui:
    environment:
      OLLAMA_ENDPOINT: http://host.docker.internal:11434/v1
```

## Analyzing Reports in the GUI

The PyRIT GUI reads red-team data from SQLite database. To analyze your reports in GUI, you must import them into SQLite first.

### Multiple ways to view reports

| Method | Format | Pros | Cons |
|--------|--------|------|------|
| **GUI (native)** | SQLite | Interactive, filterable, linked data | Requires import |
| **CSV spreadsheet** | CSV | Familiar, quick charts | Limited interactivity |
| **JSON browser** | JSON | Raw data, complete info | Less user-friendly |
| **Python script** | JSON/Python | Customizable analysis | Requires coding |

### Data sources after running red-team script

```
reports/
  +-- redteam/datasets__airt_illegal__harmbench/scorers__self_ask_true_false__refusal/20260515T120000Z/
      +-- scorer_comparison.csv         # Flattened scorer results (easy to open in Excel)
      +-- scorer_outputs.json           # Detailed scorer data (import to GUI)
      +-- batch_scorer_check.json       # BatchScorer metadata
      +-- run_report.json               # Overall run summary
      +-- cases/                        # Per-case hierarchical reports
          +-- <scenario>/<dataset>/<seed_group>/<scorer>/case_*.json

logs/
  +-- pyrit_owasp_redteam_production.log  # Audit trail (JSON lines)
```

## Method 1: Import JSON Reports to GUI (Recommended)

### Option A: Using the import script

After running the red-team script, import scorer results into SQLite:

```bash
cd samples/security-evaluator

# Import scorer_outputs.json into SQLite
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json ../../reports/scorer_outputs.json \
  --db-path ../../reports/pyrit_ollama_demo.db
```

Parameters:
- `--input-json`: Path to `scorer_outputs.json` (required)
- `--db-path`: Path to SQLite database (optional, defaults to `pyrit_ollama_demo.db`)

### Option B: Manual import using Python

If the import script is not available or you need custom import logic:

```python
import json
import asyncio
from pathlib import Path
from pyrit.setup import SQLITE, initialize_pyrit_async
from pyrit.memory import CentralMemory
from pyrit.models import Score

async def import_scorer_reports(json_path: str, db_path: str):
    """Import scorer JSON reports into SQLite for GUI analysis."""
    
    # Initialize PyRIT with SQLite backend
    await initialize_pyrit_async(
        memory_db_type=SQLITE,
        db_path=db_path
    )
    memory = CentralMemory.get_memory_instance()
    
    # Load JSON report
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract and import scorer rows
    if 'rows' in data:
        for row in data['rows']:
            # Each row contains scenario metadata and scores
            # Store as memory labels for GUI filtering
            labels = {
                "owasp_id": row.get("owasp_id", ""),
                "owasp_name": row.get("owasp_name", ""),
                "dataset": row.get("dataset", ""),
                "scorer": row.get("scorer", ""),
            }
            
            # Import score details
            scores = row.get("scores", {})
            for scorer_name, score_obj in scores.items():
                # Creates queryable Score entries in SQLite
                score_entry = Score(
                    score_value=score_obj.get("score_value"),
                    score_value_description=score_obj.get("score_value_description"),
                    score_type=score_obj.get("score_type"),
                    score_category=[score_obj.get("score_category", "analysis")],
                    score_metadata=labels,
                    scorer_class_identifier=None,
                )
                memory.add_score_to_memory(score=score_entry)
    
    print(f"[OK] Imported scorer reports from {json_path}")
    print(f"     Database: {db_path}")

# Run the import
asyncio.run(import_scorer_reports(
    json_path="reports/scorer_outputs.json",
    db_path="reports/pyrit_ollama_demo.db"
))
```

### Step-by-step: Import and view in GUI

1. Run red-team script to generate reports:
   ```bash
  python scripts/app/main.py
   ```

2. Import scorer results into SQLite:
   ```bash
  python scripts/analysis/import_scorer_json_to_memory.py \
      --input-json reports/scorer_outputs.json
   ```

3. Launch GUI:
   ```bash
   cd doc/code
   python pyrit_gui.py
   ```

4. GUI automatically connects to `pyrit_ollama_demo.db` and displays imported data

## Using the GUI for Scorer Analysis

### 1. Browse imported data

Once data is imported into SQLite, the GUI automatically displays:

### 2. Query imported data

Sidebar filters in GUI:

- **Dataset**: Filter by seed dataset name
- **Model**: Filter by target/attacker model  
- **Scorer**: View results from specific scorer (TF, Scale, Refusal, etc.)
- **Category**: Filter by OWASP id or harm type
- **Search**: Full-text search on prompts/responses
- **Date range**: Filter by execution date (if using multi-run database)

### 3. Analyze scorer agreement

After import, view:

- **Scorer Comparison tab**: See how different scorers (TF, Scale, Refusal) rated the same response
- **Weighted metrics**: Consensus signal across all scorers
- **Disagreement cases**: Scenarios where scorers had conflicting opinions

### 4. Drill into specific cases

1. Select a scenario from results
2. Click to expand conversation turns
3. View:
   - Prompt at each turn (often with converter applied)
   - Assistant response
   - All 6 scorer results with rationale
   - Metadata (model, dataset, labels)

### 5. Export and share

From GUI, download:
- Conversation as JSON
- Filtered subset as CSV
- Analysis report with charts

## Method 2: View Reports via CSV (Quick alternative)

If you need quick analysis without GUI, open CSV in spreadsheet:

```bash
# Open scorer comparison CSV in Excel/LibreOffice
open reports/scorer_comparison.csv
```

Columns include:
- OWASP ID and category
- Each scorer's result (true/false/score)
- Weighted majority, confidence, disagreement
- Scenario info and dataset

**Pros**: Immediate access, familiar tools, sort/filter
**Cons**: Limited interactivity, no multi-turn navigation

## Method 3: View Raw JSON Reports

### Per-case hierarchical JSON

Each case is saved as individual JSON file:

```bash
# View a specific case
cat reports/redteam/datasets__airt_illegal__harmbench/scorers__self_ask_true_false__refusal/20260515T120000Z/cases/llm01_prompt_injection/airt_illegal/group_1/self_ask_true_false/case_00001_scenario_00000.json
```

Each file contains:
```json
{
  "owasp_id": "LLM01",
  "owasp_name": "Prompt Injection",
  "dataset": "airt_illegal",
  "objective": "Ignore all previous instructions...",
  "scorer_name": "self_ask_true_false",
  "scorer_payload": {
    "score_value": "true",
    "score_rationale": "The model provided step-by-step instructions for obtaining controlled substances...",
    "score_category": ["objective_achieved"]
  },
  "error": null,
  "generated_at_utc": "2026-05-15T12:34:56.789Z"
}
```

### Script for batch JSON analysis

```python
import json
from pathlib import Path

def analyze_json_reports(reports_root: str = "reports/cases"):
    """Analyze JSON reports without importing to SQLite."""
    
    root = Path(reports_root)
    scenarios = {}
    
    for case_file in root.rglob("case_*.json"):
        with open(case_file) as f:
            report = json.load(f)
        
        scenario_id = report["owasp_id"]
        if scenario_id not in scenarios:
            scenarios[scenario_id] = {"total": 0, "passed": 0, "failed": 0}
        
        scenarios[scenario_id]["total"] += 1
        
        # Analyze scorer result
        score_value = report.get("scorer_payload", {}).get("score_value")
        if score_value == "true":
            scenarios[scenario_id]["passed"] += 1
        else:
            scenarios[scenario_id]["failed"] += 1
    
    # Print summary
    for scenario_id, stats in sorted(scenarios.items()):
        success_rate = 100 * stats["passed"] / stats["total"]
        print(f"{scenario_id}: {success_rate:.1f}% success ({stats['passed']}/{stats['total']})")

# Run analysis
analyze_json_reports()
```

**Pros**: No database needed, direct data access
**Cons**: Manual parsing, no GUI interactivity

## Method 4: Use GUI with existing SQLite without re-import

If you already have a populated SQLite database from a previous run:

```bash
# Point GUI to existing database
export PYRIT_SQLITE_DB_PATH=./reports/pyrit_ollama_demo.db
cd doc/code
python pyrit_gui.py
```

GUI will connect and display all previously imported conversations and scores.

## How PyRIT GUI Reads SQLite

The GUI queries these SQLite tables:

- **`conversations`** � Attack conversation ID and metadata
- **`messages`** � Prompt/response pairs within conversations  
- **`scores`** � Scorer results (imported via import tool)
- **`memory_labels`** � Metadata tags (OWASP id, dataset, model, etc.)

When you import `scorer_outputs.json`, the import script populates the `scores` and `memory_labels` tables so GUI can query and display them.

## Sharing reports across systems

If your run environment is separate from the GUI host, transfer the report JSON file and import it locally.

Recommended workflow:

1. Export `reports/scorer_outputs.json` from the run host.
2. Copy the file to the GUI machine.
3. Run the import tool on the GUI host:

```bash
cd samples/security-evaluator
python scripts/analysis/import_scorer_json_to_memory.py \
  --input-json /path/to/scorer_outputs.json \
  --db-path /path/to/pyrit_ollama_gui.db
```

If you need a helper to export run artifacts into a portable directory, use:

```bash
python scripts/analysis/export_scorer_outputs_for_gui.py \
  --input-json reports/scorer_outputs.json \
  --output-dir exported_gui_reports \
  --include-run-report \
  --include-comparison-csv
```

If the same SQLite database is already available on the GUI host, you can skip import and point the GUI at that DB file by setting `PYRIT_SQLITE_DB_PATH`.

See also: [GUI data transfer guide](./gui_data_transfer.md)

## When to use each method

| Need | Method | Time | Complexity |
|------|--------|------|-----------|
| Quick overview | CSV spreadsheet | 1 min | Low |
| Interactive drill-down | GUI (after import) | 5 min | Medium |
| Custom analysis | JSON + Python | 10+ min | High |
| Data persistence | SQLite + GUI | 5 min | Medium |
| Automated reporting | JSON batch script | Varies | High |

## Troubleshooting reports & imports

### "No data in GUI after import"

1. Verify import script finished without errors:
   ```bash
  python scripts/analysis/import_scorer_json_to_memory.py \
      --input-json reports/scorer_outputs.json 2>&1 | tail -20
   ```

2. Check database was created/updated:
   ```bash
   ls -lh reports/pyrit_ollama_demo.db
   ```

3. Restart GUI (Ctrl+C, then re-run):
   ```bash
   cd doc/code
   python pyrit_gui.py
   ```

4. Check that red-team script actually created `scorer_outputs.json`:
   ```bash
   ls -l reports/scorer_outputs.json
   cat reports/run_report.json | grep scorer_outputs
   ```

### "Import script not working or not found"

If `import_scorer_json_to_memory.py` doesn't exist or isn't working:

**Option A: Use alternative import (manual Python above)**

Create a Python script with the code from "Option B" section above.

**Option B: Use sqlite3 CLI to query existing database**

```bash
# Check what's in the database
sqlite3 reports/pyrit_ollama_demo.db \
  "SELECT COUNT(*) as conversation_count FROM conversations;"

sqlite3 reports/pyrit_ollama_demo.db \
  "SELECT COUNT(*) as score_count FROM scores;"
```

**Option C: Open database directly in GUI**

If database already has conversations (from old runs), GUI will display them:

```bash
export PYRIT_SQLITE_DB_PATH=reports/pyrit_ollama_demo.db
cd doc/code
python pyrit_gui.py
```

### "JSON file not found"

Verify red-team script completed:

```bash
# Check run report summary
cat reports/run_report.json | grep -A 5 outputs

# Should show:
# "scorer_outputs_json": "reports/scorer_outputs.json"
```

If missing, re-run red-team script with:
```bash
export EXPORT_DETAILED_SCORES_JSON=true
python scripts/app/main.py
```

### "Can't open CSV in spreadsheet"

Use Python to convert:

```python
import pandas as pd

df = pd.read_csv("reports/scorer_comparison.csv")
df.to_excel("scorer_comparison.xlsx", index=False)
print("[OK] Saved as scorer_comparison.xlsx")
```

Then open `.xlsx` in Excel/LibreOffice.

## Common analysis workflows

### Workflow 1: Find high-confidence agreement cases

1. Launch GUI (data already imported)
2. Filter: **WeightedConfidence** > 0.8
3. View cases where all scorers agree
4. These are highest-confidence objective achievements

### Workflow 2: Investigate scorer disagreement

1. Filter: **WeightedDisagreement** = "YES"
2. Select OWASP category
3. Review responses where scorers conflicted
4. Identify edge cases and model ambiguity

### Workflow 3: Compare performance across datasets

1. Filter by **Dataset** = "harmbench"
2. Note success rate for this dataset
3. Switch to **Dataset** = another one
4. Compare success rates
5. Determine which dataset types are harder

### Workflow 4: Deep-dive single scenario

1. Select OWASP id = "LLM01"
2. View all turns in one attack
3. Watch model responses evolve
4. See how converter was applied at each step
5. Review all 6 scorer opinions on final turn
6. Export conversation for report or sharing

## Troubleshooting

### GUI launching issues

**"Port 8501 already in use"**

Kill existing process:

```bash
lsof -i :8501 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

Or run on different port:

```bash
cd doc/code
streamlit run pyrit_gui.py --server.port 8502
```

**"Cannot connect to Ollama from GUI"**

- Local: Verify Ollama running on localhost:11434
- Docker: Use `host.docker.internal` (macOS/Windows) or host gateway IP (Linux)
- See [Docker Setup](docker_setup.md) for config details

### Data display issues

**"No data appears in GUI"**

Quick checklist:

1. ? Red-team script ran: `ls -la reports/scorer_outputs.json`
2. ? Import script completed: `python scripts/analysis/import_scorer_json_to_memory.py --input-json reports/scorer_outputs.json`
3. ? Database exists: `ls -la reports/pyrit_ollama_demo.db` (file should grow after import)
4. ? GUI restarted after import (old connections may cache empty data)

If database still empty:

```bash
# Check database schema
sqlite3 reports/pyrit_ollama_demo.db ".tables"

# Should show: conversations, messages, scores, memory_labels, etc.

# Count rows
sqlite3 reports/pyrit_ollama_demo.db \
  "SELECT 'conversations' as table_name, COUNT(*) as count FROM conversations \
   UNION ALL \
   SELECT 'scores', COUNT(*) FROM scores;"
```

**"Only some scenarios appear"**

- Check `reports/run_report.json` for actual execution count
- If many scenarios failed, check `logs/pyrit_owasp_redteam_production.log`
- Re-import to ensure all data is synced

**"Scorer results not showing"**

1. Verify `scorer_outputs.json` has data:
   ```bash
   head -c 500 reports/scorer_outputs.json
   ```

2. Check import output:
   ```bash
  python scripts/analysis/import_scorer_json_to_memory.py \
      --input-json reports/scorer_outputs.json 2>&1 | head -20
   ```

### Import script issues

**"ImportError or module not found"**

If `import_scorer_json_to_memory.py` script is missing or broken, use manual Python import (see "Option B: Manual import using Python" section above).

**"JSON parsing error during import"**

Verify JSON file isn't corrupted:

```bash
python -c "import json; json.load(open('reports/scorer_outputs.json'))"
```

If it fails, JSON is malformed. Check red-team script logs for where it failed.

**"Database locked during import"**

Another GUI or script instance is accessing database. Close all GUI windows and retry.

### View data without GUI

If GUI keeps having issues, use alternatives:

**Quick CSV view:**
```bash
open reports/scorer_comparison.csv
```

**Raw JSON summary:**
```bash
cat reports/run_report.json | python -m json.tool | head -50
```

**Per-case breakdown:**
```bash
ls reports/cases/*/                    # List all scenarios
cat reports/cases/llm01_prompt_injection/*/airt_illegal/case_00001_scenario_00000.json
```

**Python script to query database directly:**
```python
import sqlite3
conn = sqlite3.connect("reports/pyrit_ollama_demo.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM scores;")
print(f"Total scores: {cursor.fetchone()[0]}")
```

## Next steps

### Quick path: GUI analysis

1. [Run red-team script](../../docs/script/quickstart.md)
2. [Import JSON to SQLite](#method-1-import-json-reports-to-gui-recommended) (5 minutes)
3. Launch GUI and analyze

### Alternative paths

- **No time for GUI?** ? Open `reports/scorer_comparison.csv` in spreadsheet (1 minute)
- **Need custom filtering?** ? Use JSON + Python script (see Method 3)
- **Prefer command-line?** ? Query SQLite directly with sqlite3 CLI

### Learn more

- [Script configuration options](../../docs/script/usage_guide.md) � Tune red-team behavior
- [Custom datasets](../../docs/script/custom_dataset_guide.md) � Create your own attack prompts
- [Technical details](../../docs/script/technical_reference.md) � Understand reporting architecture
