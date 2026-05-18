#!/usr/bin/env python3
"""Export scorer report artifacts for GUI import on another machine."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Iterable


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export generated scorer artifacts from a PyRIT run so they can be imported into a GUI host."
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        default=Path("reports/scorer_outputs.json"),
        help="Path to scored JSON output produced by a PyRIT run.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("exported_gui_reports"),
        help="Target directory for exported artifacts.",
    )
    parser.add_argument(
        "--include-run-report",
        action="store_true",
        help="Also export run_report.json if present.",
    )
    parser.add_argument(
        "--include-comparison-csv",
        action="store_true",
        help="Also export scorer_comparison.csv if present.",
    )
    return parser


def _safe_copy(src: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    print(f"Copied {src} -> {dest}")


def _find_optional_artifact(root: Path, name: str) -> Path | None:
    candidate = root / name
    return candidate if candidate.exists() else None


def export_artifacts(*, input_json: Path, output_dir: Path, include_run_report: bool, include_comparison_csv: bool) -> int:
    if not input_json.exists():
        print(f"ERROR: input scorer JSON not found: {input_json}")
        return 2

    _safe_copy(input_json, output_dir)

    report_root = input_json.parent
    optional_files: list[Path] = []

    if include_run_report:
        run_report = _find_optional_artifact(report_root, "run_report.json")
        if run_report is not None:
            optional_files.append(run_report)
        else:
            print("Warning: run_report.json not found at the same location as scorer_outputs.json")

    if include_comparison_csv:
        comparison_csv = _find_optional_artifact(report_root, "scorer_comparison.csv")
        if comparison_csv is not None:
            optional_files.append(comparison_csv)
        else:
            print("Warning: scorer_comparison.csv not found at the same location as scorer_outputs.json")

    for artifact in optional_files:
        _safe_copy(artifact, output_dir)

    print(f"Export completed. Use the exported scorer JSON from: {output_dir / input_json.name}")
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    return export_artifacts(
        input_json=args.input_json,
        output_dir=args.output_dir,
        include_run_report=args.include_run_report,
        include_comparison_csv=args.include_comparison_csv,
    )


if __name__ == "__main__":
    raise SystemExit(main())
