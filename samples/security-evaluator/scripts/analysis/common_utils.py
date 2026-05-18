#!/usr/bin/env python3
"""Shared utility helpers for red-team analysis scripts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def print_cli_header(*, title: str) -> None:
    """Print a consistent CLI section header.

    Args:
        title (str): Header title text.
    """
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def load_json_dict(*, input_path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON file and validate that it is a dictionary.

    Args:
        input_path (Path): Path to JSON file.

    Returns:
        dict[str, Any]: Parsed JSON object.

    Raises:
        ValueError: If JSON root payload is not an object.
    """
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at root in: {input_path}")
    return payload


def extract_dict_rows(*, payload: dict[str, Any], key: str = "rows") -> list[dict[str, Any]]:
    """Extract dictionary row items from a payload key.

    Args:
        payload (dict[str, Any]): JSON payload object.
        key (str): Key containing row list. Defaults to "rows".

    Returns:
        list[dict[str, Any]]: Validated row dictionaries.

    Raises:
        ValueError: If key does not contain a list.
    """
    rows = payload.get(key, [])
    if not isinstance(rows, list):
        raise ValueError(f"Invalid JSON format: '{key}' must be a list.")
    return [row for row in rows if isinstance(row, dict)]


def write_dict_rows_csv(
    *,
    output_path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
) -> int:
    """Write dictionary rows to CSV with explicit fieldnames.

    Args:
        output_path (Path): CSV file path.
        fieldnames (list[str]): CSV column names.
        rows (list[dict[str, Any]]): Row dictionaries.

    Returns:
        int: Number of written rows.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    return len(rows)


def write_tabular_csv(*, output_path: Path, columns: list[str], rows: list[tuple[Any, ...]]) -> int:
    """Write tabular rows with explicit columns to CSV.

    Args:
        output_path (Path): CSV file path.
        columns (list[str]): Column names.
        rows (list[tuple[Any, ...]]): Tuple rows matching columns.

    Returns:
        int: Number of written rows.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)
