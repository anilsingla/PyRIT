#!/usr/bin/env python3
"""
SQLite database query utility for PyRIT red-team reports.

Provides simple command-line access to query scorer results, scores, and conversation history
without requiring the GUI.

Usage:
    python query_sqlite_database.py --query [scorers|scores|conversations|count]
    python query_sqlite_database.py --query scores --scenario LLM01
    python query_sqlite_database.py --sql "SELECT * FROM Score LIMIT 5"

Examples:
    # List all scorers in database
    python query_sqlite_database.py --query scorers
    
    # Get scores by scenario
    python query_sqlite_database.py --query scores --filter-scenario LLM01
    
    # Run custom SQL query
    python query_sqlite_database.py --sql "SELECT score_value, COUNT(*) FROM Score GROUP BY score_value"
    
    # Export scores to CSV
    python query_sqlite_database.py --query scores --export scores.csv
"""

import argparse
import sqlite3
import csv
from pathlib import Path
from typing import List, Tuple, Optional

from common_utils import print_cli_header, write_tabular_csv


class PyRITDatabase:
    """Helper class to query PyRIT SQLite databases."""
    
    def __init__(self, db_path: str = "pyrit_ollama_demo.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to PyRIT SQLite database
        """
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def list_tables(self) -> List[str]:
        """Get list of all tables in database.
        
        Returns:
            List of table names
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def list_scorers(self) -> List[Tuple]:
        """List all scorer classes used in database.
        
        Returns:
            List of (scorer_class_identifier, count) tuples
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT scorer_class_identifier, COUNT(*) as count
                FROM Score
                GROUP BY scorer_class_identifier
                ORDER BY count DESC
            """)
            return cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"[ERROR] Table 'Score' not found. Available tables: {self.list_tables()}")
            return []
    
    def get_scores(self, scenario: Optional[str] = None, 
                  scorer: Optional[str] = None,
                  limit: int = 100) -> List[dict]:
        """Query scores with optional filters.
        
        Args:
            scenario: Filter by OWASP scenario ID (from score_metadata)
            scorer: Filter by scorer class identifier
            limit: Maximum results to return
            
        Returns:
            List of score dictionaries
        """
        cursor = self.conn.cursor()
        
        # Build base query
        query = "SELECT * FROM Score WHERE 1=1"
        params = []
        
        # Filter by scenario (stored in score_metadata as JSON)
        if scenario:
            query += " AND score_metadata LIKE ?"
            params.append(f'%"owasp_id": "{scenario}"%')
        
        # Filter by scorer
        if scorer:
            query += " AND scorer_class_identifier = ?"
            params.append(scorer)
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_score_statistics(self) -> dict:
        """Get overall statistics about scores in database.
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total scores
        cursor.execute("SELECT COUNT(*) FROM Score")
        stats['total_scores'] = cursor.fetchone()[0]
        
        # Scores by value (true/false breakdown)
        cursor.execute("""
            SELECT score_value, COUNT(*) as count
            FROM Score
            GROUP BY score_value
            ORDER BY count DESC
        """)
        stats['by_score_value'] = dict(cursor.fetchall())
        
        # Scores by scorer
        cursor.execute("""
            SELECT scorer_class_identifier, COUNT(*) as count
            FROM Score
            GROUP BY scorer_class_identifier
            ORDER BY count DESC
        """)
        stats['by_scorer'] = dict(cursor.fetchall())
        
        return stats
    
    def get_conversations(self, limit: int = 10) -> List[dict]:
        """Query conversation history.
        
        Returns:
            List of conversation dictionaries
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM Conversation ORDER BY timestamp DESC LIMIT ?", (limit,))
        except sqlite3.OperationalError:
            print("[INFO] No 'Conversation' table found (normal if not using multi-turn)")
            return []
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_raw_sql(self, sql: str) -> Tuple[List[str], List[tuple]]:
        """Execute arbitrary SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            Tuple of (columns, rows)
        """
        cursor = self.conn.cursor()
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    
    def export_scores_to_csv(self, output_path: str, limit: int = None):
        """Export all scores to CSV file.
        
        Args:
            output_path: Path to CSV output file
            limit: Maximum number of rows (None = all)
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM Score"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(zip(columns, row)))
        
        print(f"[OK] Exported {len(rows)} rows to {output_path}")


def print_table(columns: List[str], rows: List[tuple], limit: int = 20):
    """Pretty-print query results as ASCII table.
    
    Args:
        columns: Column names
        rows: Query result rows
        limit: Maximum rows to display
    """
    if not rows:
        print("[INFO] No results")
        return
    
    # Truncate long values and limit rows
    total_rows = len(rows)
    displayed_rows = rows[:limit]
    col_widths = [max(len(str(col)), max(len(str(row[i])) for row in displayed_rows)) 
                  for i, col in enumerate(columns)]
    col_widths = [min(w, 50) for w in col_widths]  # Cap width at 50
    
    # Print header
    header = " | ".join(f"{col[:w]:<{w}}" for col, w in zip(columns, col_widths))
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in displayed_rows:
        row_str = " | ".join(
            f"{str(val)[:w]:<{w}}" if val is not None else f"{'NULL':<{w}}"
            for val, w in zip(row, col_widths)
        )
        print(row_str)
    
    if total_rows > limit:
        print(f"\n[INFO] Showing first {limit} rows (more available)")


def main():
    parser = argparse.ArgumentParser(
        description="Query PyRIT SQLite database from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all scorers
  python query_sqlite_database.py --query scorers
  
  # Show statistics
  python query_sqlite_database.py --query count
  
  # Get scores for specific scenario
  python query_sqlite_database.py --query scores --filter-scenario LLM01
  
  # Run custom SQL
  python query_sqlite_database.py --sql "SELECT COUNT(*) FROM Score"
  
  # Export to CSV
  python query_sqlite_database.py --query scores --export results.csv
        """
    )
    
    parser.add_argument(
        "--db-path",
        default="pyrit_ollama_demo.db",
        help="Path to PyRIT SQLite database (default: pyrit_ollama_demo.db)"
    )
    
    parser.add_argument(
        "--query",
        choices=["scorers", "scores", "conversations", "count"],
        help="Predefined queries (or use --sql for custom)"
    )
    
    parser.add_argument(
        "--filter-scenario",
        help="Filter scores by OWASP scenario ID"
    )
    
    parser.add_argument(
        "--filter-scorer",
        help="Filter scores by scorer identifier"
    )
    
    parser.add_argument(
        "--sql",
        help="Run custom SQL query"
    )
    
    parser.add_argument(
        "--export",
        help="Export results to CSV file"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum rows to display (default: 20)"
    )
    
    args = parser.parse_args()
    
    print_cli_header(title="PyRIT SQLite Database Query Tool")
    
    # Connect to database
    try:
        db = PyRITDatabase(args.db_path)
        print(f"[OK] Connected to {args.db_path}")
        print(f"     Tables: {', '.join(db.list_tables())}\n")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return
    
    try:
        # Execute query
        if args.sql:
            print(f"[*] Executing: {args.sql}\n")
            columns, rows = db.execute_raw_sql(args.sql)
            
            if args.export:
                # For CSV export of custom query
                written = write_tabular_csv(output_path=Path(args.export), columns=columns, rows=rows)
                print(f"[OK] Exported {written} rows to {args.export}")
            else:
                print_table(columns, rows, limit=args.limit)
        
        elif args.query == "scorers":
            print("[*] Scorers in database:\n")
            scorers = db.list_scorers()
            for scorer, count in scorers:
                print(f"  {scorer or '(None)':<50} {count:>5} scores")
        
        elif args.query == "count":
            print("[*] Database statistics:\n")
            stats = db.get_score_statistics()
            
            print(f"Total scores: {stats['total_scores']}")
            
            print(f"\nBy Score Value:")
            for value, count in stats['by_score_value'].items():
                pct = 100 * count / stats['total_scores'] if stats['total_scores'] > 0 else 0
                print(f"  {value or 'NULL':<20} {count:>5} ({pct:>5.1f}%)")
            
            print(f"\nBy Scorer:")
            for scorer, count in stats['by_scorer'].items():
                print(f"  {scorer or '(None)':<50} {count:>5}")
        
        elif args.query == "scores":
            print(f"[*] Retrieving scores")
            if args.filter_scenario:
                print(f"    Filter: scenario={args.filter_scenario}")
            if args.filter_scorer:
                print(f"    Filter: scorer={args.filter_scorer}")
            print()
            
            scores = db.get_scores(
                scenario=args.filter_scenario,
                scorer=args.filter_scorer,
                limit=args.limit
            )
            
            if not scores:
                print("[INFO] No scores found")
            else:
                print(f"[OK] Found {len(scores)} scores:\n")
                # Print as formatted table
                columns = list(scores[0].keys())
                rows = [[score[col] for col in columns] for score in scores]
                print_table(columns, rows, limit=args.limit)
                
                if args.export:
                    with open(args.export, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(scores)
                    print(f"\n[OK] Exported to {args.export}")
        
        elif args.query == "conversations":
            conversations = db.get_conversations(limit=args.limit)
            if conversations:
                print(f"[OK] Found {len(conversations)} conversations:\n")
                columns = list(conversations[0].keys())
                rows = [[c[col] for col in columns] for c in conversations]
                print_table(columns, rows, limit=args.limit)
            else:
                print("[INFO] No conversations found")
        
        else:
            print("[!] Please specify --query or --sql")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n[!] Query cancelled")
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
    finally:
        db.close()
    
    print()


if __name__ == "__main__":
    main()
