#!/usr/bin/env python3
"""
Helper script to import PyRIT scorer JSON reports into SQLite database manually.

This script provides an alternative import method if import_scorer_json_to_memory.py
is not available or not working properly.

Usage:
    python import_json_helper.py --input SCORER_JSON_FILE [--db-path DB_PATH]

Examples:
    # Import with defaults
    python import_json_helper.py --input reports/scorer_outputs.json

    # Specify custom database path
    python import_json_helper.py \\
      --input reports/scorer_outputs.json \\
      --db-path custom_db.db
"""

import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List

from common_utils import extract_dict_rows, load_json_dict, print_cli_header


async def import_scorer_reports(json_path: str, db_path: str) -> None:
    """Import scorer JSON reports into SQLite for GUI analysis.
    
    Args:
        json_path: Path to scorer_outputs.json from red-team script
        db_path: Path to SQLite database (created if not exists)
    """
    try:
        from pyrit.setup import SQLITE, initialize_pyrit_async
        from pyrit.memory import CentralMemory
    except ImportError:
        print("[ERROR] PyRIT not installed. Run: pip install pyrit")
        return
    
    json_file = Path(json_path)
    if not json_file.exists():
        print(f"[ERROR] JSON file not found: {json_path}")
        return
    
    print(f"[*] Loading JSON report from {json_path}...")
    try:
        data = load_json_dict(input_path=json_file)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return
    
    print(f"[*] Initializing PyRIT with SQLite at {db_path}...")
    try:
        await initialize_pyrit_async(
            memory_db_type=SQLITE,
            db_path=db_path
        )
        memory = CentralMemory.get_memory_instance()
    except Exception as e:
        print(f"[ERROR] Failed to initialize PyRIT: {e}")
        return
    
    # Extract and import scorer rows
    rows = extract_dict_rows(payload=data, key="rows")
    if not rows:
        print("[WARN] No rows found in JSON data")
        return
    
    print(f"[*] Processing {len(rows)} report rows...")
    imported_count = 0
    
    for row_idx, row in enumerate(rows, 1):
        try:
            # Extract metadata
            owasp_id = row.get("owasp_id", "")
            owasp_name = row.get("owasp_name", "")
            dataset = row.get("dataset", "")
            scores = row.get("scores", {})
            error = row.get("error")
            
            # Create label set for this scenario
            labels = {
                "owasp_id": owasp_id,
                "owasp_name": owasp_name,
                "dataset": dataset,
                "import_source": "json_import_helper",
            }
            
            # Process each scorer's result
            for scorer_name, score_obj in scores.items():
                if not isinstance(score_obj, dict):
                    continue
                
                try:
                    # Create a memory entry with metadata
                    # This allows GUI to query by owasp_id, dataset, etc.
                    if hasattr(memory, 'add_score_to_memory'):
                        # Newer PyRIT API
                        from pyrit.models import Score
                        
                        score = Score(
                            score_value=score_obj.get("score_value", ""),
                            score_value_description=score_obj.get("score_value_description", ""),
                            score_type=score_obj.get("score_type", ""),
                            score_category=[score_obj.get("score_category", "analysis")],
                            score_metadata=labels,
                            scorer_class_identifier=None,
                        )
                        memory.add_score_to_memory(score=score)
                    else:
                        # Fallback: store as labeled entry
                        memory.add_raw_entry(
                            entry_text=json.dumps(score_obj),
                            entry_type="score",
                            labels=labels
                        )
                    
                    imported_count += 1
                
                except Exception as scorer_err:
                    print(f"    [WARN] Row {row_idx}, Scorer {scorer_name}: {scorer_err}")
                    continue
            
            if row_idx % 10 == 0:
                print(f"  [{row_idx}/{len(rows)}] Processing...")
        
        except Exception as row_err:
            print(f"  [WARN] Skipping row {row_idx}: {row_err}")
            continue
    
    print(f"\n[OK] Successfully imported {imported_count} score entries")
    print(f"     Database: {db_path}")
    print(f"\nNext steps:")
    print(f"  1. Launch GUI: cd doc/code && python pyrit_gui.py")
    print(f"  2. Set env var: export PYRIT_SQLITE_DB_PATH={db_path}")
    print(f"  3. GUI will query the imported scores automatically")


def main():
    parser = argparse.ArgumentParser(
        description="Helper script to import scorer JSON into SQLite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import with default database path
  python import_json_helper.py --input reports/scorer_outputs.json
  
  # Import with custom database path
  python import_json_helper.py \\
    --input my_reports.json \\
    --db-path /tmp/custom.db
        """
    )
    
    parser.add_argument(
        "--input",
        required=True,
        help="Path to scorer_outputs.json file"
    )
    parser.add_argument(
        "--db-path",
        default="pyrit_ollama_demo.db",
        help="Path to SQLite database (default: pyrit_ollama_demo.db)"
    )
    
    args = parser.parse_args()
    
    print_cli_header(title="JSON Report Importer Helper")
    
    # Run async function
    try:
        asyncio.run(import_scorer_reports(args.input, args.db_path))
    except KeyboardInterrupt:
        print("\n[!] Import cancelled by user")
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")


if __name__ == "__main__":
    main()
