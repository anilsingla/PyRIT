#!/usr/bin/env python3
"""
Analyze PyRIT red-team JSON reports without GUI or SQLite import.

This script reads per-case JSON reports from the hierarchical report structure
and generates analysis summaries without requiring GUI or database setup.

Usage:
    python analyze_json_reports.py [--input-dir REPORTS_ROOT] [--format {summary,detailed,csv}]

Examples:
    # Analyze all reports with summary
    python analyze_json_reports.py --input-dir reports/cases

    # Save detailed breakdown as CSV
    python analyze_json_reports.py --format csv --output analysis.csv

    # Analyze specific scenario
    python analyze_json_reports.py --scenario LLM01
"""

import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
import csv

from common_utils import load_json_dict, print_cli_header


def load_json_reports(root_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON reports from hierarchical directory structure.
    
    Args:
        root_dir: Root directory containing scenario/scorer/dataset/case_*.json files
        
    Returns:
        List of report dictionaries
    """
    root = Path(root_dir)
    reports = []
    
    for case_file in sorted(root.rglob("case_*.json")):
        try:
            report = load_json_dict(input_path=case_file)
            report['file_path'] = str(case_file)
            reports.append(report)
        except Exception as e:
            print(f"[WARN] Failed to load {case_file}: {e}")
    
    return reports


def generate_summary(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate high-level summary statistics.
    
    Args:
        reports: List of report dictionaries
        
    Returns:
        Summary dictionary with aggregated metrics
    """
    summary = {
        "total_cases": len(reports),
        "by_scenario": defaultdict(lambda: {"total": 0, "success": 0, "failed": 0}),
        "by_dataset": defaultdict(lambda: {"total": 0, "success": 0, "failed": 0}),
        "by_scorer": defaultdict(lambda: {"total": 0, "success": 0, "failed": 0}),
        "errors": [],
    }
    
    for report in reports:
        scenario_id = report.get("owasp_id", "unknown")
        dataset = report.get("dataset", "unknown")
        scorer = report.get("scorer_name", "unknown")
        
        # Extract score value
        is_success = False
        score_value = report.get("scorer_payload", {}).get("score_value")
        if score_value in ["true", "True", True]:
            is_success = True
        
        # Update scenario stats
        summary["by_scenario"][scenario_id]["total"] += 1
        if is_success:
            summary["by_scenario"][scenario_id]["success"] += 1
        else:
            summary["by_scenario"][scenario_id]["failed"] += 1
        
        # Update dataset stats
        summary["by_dataset"][dataset]["total"] += 1
        if is_success:
            summary["by_dataset"][dataset]["success"] += 1
        else:
            summary["by_dataset"][dataset]["failed"] += 1
        
        # Update scorer stats
        summary["by_scorer"][scorer]["total"] += 1
        if is_success:
            summary["by_scorer"][scorer]["success"] += 1
        else:
            summary["by_scorer"][scorer]["failed"] += 1
        
        # Track errors
        if report.get("error"):
            summary["errors"].append({
                "scenario": scenario_id,
                "dataset": dataset,
                "error": report.get("error"),
            })
    
    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    """Print summary in human-readable format.
    
    Args:
        summary: Summary dictionary from generate_summary()
    """
    print_cli_header(title="Red-Team JSON Reports Analysis")
    
    print(f"Total cases analyzed: {summary['total_cases']}\n")
    
    print(f"{'='*70}")
    print("  Success Rate by OWASP Scenario")
    print(f"{'='*70}")
    print(f"{'Scenario':<12} {'Total':<8} {'Success':<8} {'Failed':<8} {'Rate':<8}")
    print(f"{'-'*52}")
    
    for scenario_id in sorted(summary["by_scenario"].keys()):
        stats = summary["by_scenario"][scenario_id]
        total = stats["total"]
        success = stats["success"]
        rate = 100 * success / total if total > 0 else 0
        print(f"{scenario_id:<12} {total:<8} {success:<8} {stats['failed']:<8} {rate:>6.1f}%")
    
    print(f"\n{'='*70}")
    print("  Results by Dataset")
    print(f"{'='*70}")
    print(f"{'Dataset':<20} {'Total':<8} {'Success':<8} {'Failed':<8} {'Rate':<8}")
    print(f"{'-'*54}")
    
    for dataset in sorted(summary["by_dataset"].keys()):
        stats = summary["by_dataset"][dataset]
        total = stats["total"]
        success = stats["success"]
        rate = 100 * success / total if total > 0 else 0
        print(f"{dataset:<20} {total:<8} {success:<8} {stats['failed']:<8} {rate:>6.1f}%")
    
    print(f"\n{'='*70}")
    print("  Results by Scorer")
    print(f"{'='*70}")
    print(f"{'Scorer':<30} {'Total':<8} {'Success':<8} {'Rate':<8}")
    print(f"{'-'*54}")
    
    for scorer in sorted(summary["by_scorer"].keys()):
        stats = summary["by_scorer"][scorer]
        total = stats["total"]
        success = stats["success"]
        rate = 100 * success / total if total > 0 else 0
        print(f"{scorer:<30} {total:<8} {success:<8} {rate:>6.1f}%")
    
    if summary["errors"]:
        print(f"\n{'='*70}")
        print(f"  Errors ({len(summary['errors'])})")
        print(f"{'='*70}")
        for err in summary["errors"][:10]:  # Show first 10
            print(f"  {err['scenario']} / {err['dataset']}: {err['error'][:60]}")
        if len(summary["errors"]) > 10:
            print(f"  ... and {len(summary['errors']) - 10} more")
    
    print(f"\n{'='*70}\n")


def export_csv(reports: List[Dict[str, Any]], output_path: str) -> None:
    """Export reports to CSV for spreadsheet analysis.
    
    Args:
        reports: List of report dictionaries
        output_path: CSV file to write
    """
    if not reports:
        print("[WARN] No reports to export")
        return
    
    fieldnames = [
        "owasp_id",
        "owasp_name",
        "dataset",
        "scorer_name",
        "score_value",
        "score_rationale",
        "error",
        "generated_at_utc",
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for report in reports:
            payload = report.get("scorer_payload", {})
            row = {
                "owasp_id": report.get("owasp_id", ""),
                "owasp_name": report.get("owasp_name", ""),
                "dataset": report.get("dataset", ""),
                "scorer_name": report.get("scorer_name", ""),
                "score_value": payload.get("score_value", ""),
                "score_rationale": payload.get("score_rationale", "")[:100],  # Truncate
                "error": report.get("error", ""),
                "generated_at_utc": report.get("generated_at_utc", ""),
            }
            writer.writerow(row)
    
    print(f"[OK] Exported {len(reports)} reports to {output_path}")


def filter_reports(reports: List[Dict[str, Any]], scenario: str = None, dataset: str = None, 
                  scorer: str = None) -> List[Dict[str, Any]]:
    """Filter reports by criteria.
    
    Args:
        reports: List of report dictionaries
        scenario: Filter by OWASP scenario ID
        dataset: Filter by dataset name
        scorer: Filter by scorer name
        
    Returns:
        Filtered list of reports
    """
    filtered = reports
    
    if scenario:
        filtered = [r for r in filtered if r.get("owasp_id") == scenario]
    if dataset:
        filtered = [r for r in filtered if r.get("dataset") == dataset]
    if scorer:
        filtered = [r for r in filtered if r.get("scorer_name") == scorer]
    
    return filtered


def main():
    parser = argparse.ArgumentParser(
        description="Analyze PyRIT red-team JSON reports without GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all reports
  python analyze_json_reports.py --input-dir reports/cases
  
  # Analyze specific scenario
  python analyze_json_reports.py --scenario LLM01
  
  # Export to CSV
  python analyze_json_reports.py --format csv --output analysis.csv
        """
    )
    
    parser.add_argument(
        "--input-dir",
        default="reports/cases",
        help="Root directory of case reports (default: reports/cases)"
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Filter by OWASP scenario ID (e.g., LLM01)"
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Filter by dataset name (e.g., harmbench)"
    )
    parser.add_argument(
        "--scorer",
        default=None,
        help="Filter by scorer name"
    )
    parser.add_argument(
        "--format",
        choices=["summary", "detailed", "csv"],
        default="summary",
        help="Output format (default: summary)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file for CSV export"
    )
    
    args = parser.parse_args()
    
    # Load reports
    print(f"[*] Loading reports from {args.input_dir}...")
    reports = load_json_reports(args.input_dir)
    
    if not reports:
        print(f"[!] No reports found in {args.input_dir}")
        return
    
    print(f"[v] Loaded {len(reports)} reports")
    
    # Filter if needed
    if args.scenario or args.dataset or args.scorer:
        reports = filter_reports(
            reports,
            scenario=args.scenario,
            dataset=args.dataset,
            scorer=args.scorer
        )
        print(f"[v] Filtered to {len(reports)} reports")
    
    # Generate and display analysis
    if args.format == "summary":
        summary = generate_summary(reports)
        print_summary(summary)
    
    elif args.format == "csv":
        output_file = args.output or "json_reports_analysis.csv"
        export_csv(reports, output_file)
    
    elif args.format == "detailed":
        print_cli_header(title="Detailed Report Listing")
        for i, report in enumerate(reports[:20], 1):  # Show first 20
            payload = report.get("scorer_payload", {})
            print(f"{i}. {report.get('owasp_id')} / {report.get('scorer_name')}")
            print(f"   Dataset: {report.get('dataset')}")
            print(f"   Score:   {payload.get('score_value')}")
            print(f"   Path:    {report.get('file_path')}")
            if payload.get('score_rationale'):
                print(f"   Note:    {payload.get('score_rationale')[:80]}...")
            print()
        if len(reports) > 20:
            print(f"... and {len(reports) - 20} more reports")


if __name__ == "__main__":
    main()
