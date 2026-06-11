# pyright: reportMissingImports=false
#!/usr/bin/env python3
"""Import custom dataset files into PyRIT SQLite memory in one command."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

HELPER_DIR = Path(__file__).resolve().parent
if str(HELPER_DIR) not in sys.path:
    sys.path.insert(0, str(HELPER_DIR))

from dataset_format_utils import (
    convert_starter_json_to_pyrit_dict,
    is_starter_dataset_payload,
    load_json_payload,
)
from pyrit.models import SeedDataset
from pyrit.setup import SQLITE, initialize_pyrit_async
from pyrit.memory import CentralMemory


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI parser.

    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(description="Import a custom dataset into SQLite-backed PyRIT memory.")
    parser.add_argument("--input", required=True, type=Path, help="Input dataset file (.json/.yaml/.yml/.prompt).")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("reports/pyrit_ollama_demo.db"),
        help="SQLite DB path used by PyRIT.",
    )
    parser.add_argument(
        "--added-by",
        default="custom_dataset_importer",
        help="Label for dataset insertion source.",
    )
    return parser


def _load_dataset(*, input_path: Path) -> SeedDataset:
    """Load dataset from supported file formats.

    Args:
        input_path (Path): Input dataset path.

    Returns:
        SeedDataset: Parsed dataset object.

    Raises:
        ValueError: If file extension is unsupported.
    """
    suffix = input_path.suffix.lower()

    if suffix in {".yaml", ".yml", ".prompt"}:
        return SeedDataset.from_yaml_file(str(input_path))

    if suffix == ".json":
        payload = load_json_payload(input_path=input_path)
        if is_starter_dataset_payload(payload=payload):
            payload = convert_starter_json_to_pyrit_dict(payload=payload)
        return SeedDataset.from_dict(payload)

    raise ValueError("Unsupported file extension. Use .json, .yaml, .yml, or .prompt.")


async def _import_dataset_async(*, dataset: SeedDataset, db_path: Path, added_by: str) -> None:
    """Import dataset into SQLite memory.

    Args:
        dataset (SeedDataset): Dataset object.
        db_path (Path): SQLite path.
        added_by (str): Label for insertion source.
    """
    await initialize_pyrit_async(memory_db_type=SQLITE, db_path=str(db_path.resolve()))
    memory = CentralMemory.get_memory_instance()
    await memory.add_seed_datasets_to_memory_async(datasets=[dataset], added_by=added_by)


def main() -> int:
    """Run CLI entrypoint.

    Returns:
        int: Exit code.
    """
    parser = _build_parser()
    args = parser.parse_args()

    input_path: Path = args.input
    db_path: Path = args.db_path
    added_by = str(args.added_by).strip() or "custom_dataset_importer"

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 2

    try:
        dataset = _load_dataset(input_path=input_path)
        asyncio.run(_import_dataset_async(dataset=dataset, db_path=db_path, added_by=added_by))
        dataset_name = dataset.dataset_name or dataset.name or "unknown_dataset"
        print(f"[OK] Imported dataset '{dataset_name}' into {db_path.resolve()}")
        print(f"[OK] Total seeds imported in this dataset: {len(dataset.seeds)}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Import failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
