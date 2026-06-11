"""Dataset planning, preview, and memory sync helpers."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from typing import Any

from .env_config import (
    DATASET_PREVIEW_ROWS,
    PRINT_DATASET_SEEDS,
    OWASPScenario,
    SeedDataset,
    Sequence,
    debug_log,
)


def pick_dataset(*, preferred: list[str], available: set[str]) -> str | None:
    """Return the first preferred dataset name that is available."""
    for name in preferred:
        if name in available:
            debug_log(message=f"Selected dataset '{name}' from preferred list")
            return name
    debug_log(message=f"No dataset found in preferred list: {preferred}")
    return None


def order_datasets_for_execution(*, preferred: list[str], available: set[str]) -> list[str]:
    """Order datasets for execution with preferred names first."""
    preferred_present = [name for name in preferred if name in available]
    remaining = sorted([name for name in available if name not in set(preferred_present)])
    return preferred_present + remaining


def load_seed_dataset_from_path(*, input_path: Path) -> SeedDataset:
    """Load a PyRIT seed dataset from YAML, prompt, or JSON file."""
    suffix = input_path.suffix.lower()
    if suffix in {".yaml", ".yml", ".prompt"}:
        return SeedDataset.from_yaml_file(str(input_path))

    if suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON dataset must contain an object at the top level.")

        if payload.get("dataset_type") in {"single-turn", "multi-turn"}:
            from scripts.helper.dataset.dataset_format_utils import convert_starter_json_to_pyrit_dict

            payload = convert_starter_json_to_pyrit_dict(payload=payload)

        return SeedDataset.from_dict(payload)

    raise ValueError("Unsupported dataset file extension. Use .json, .yaml, .yml, or .prompt.")


def build_execution_plan(
    *,
    scenarios: list[OWASPScenario],
    available_datasets: set[str],
    selected_datasets: set[str] | None,
    run_all_available_datasets: bool,
    max_datasets_per_scenario: int,
) -> list[dict[str, object]]:
    """Build scenario + dataset execution plan."""
    scenario_execution_plan: list[dict[str, object]] = []
    selected_pool = selected_datasets or set()

    for scenario in scenarios:
        candidate_pool = available_datasets
        if selected_datasets is not None:
            candidate_pool = {name for name in available_datasets if name in selected_pool}
            if not candidate_pool:
                candidate_pool = set(selected_pool)

        if run_all_available_datasets:
            preferred_pool = [name for name in scenario.datasets if name in candidate_pool]
            ordered_datasets = order_datasets_for_execution(preferred=preferred_pool, available=candidate_pool)
            if not ordered_datasets and selected_datasets is not None:
                ordered_datasets = sorted(candidate_pool)
            if max_datasets_per_scenario > 0:
                ordered_datasets = ordered_datasets[:max_datasets_per_scenario]
            if ordered_datasets:
                for dataset_name in ordered_datasets:
                    scenario_execution_plan.append({"scenario": scenario, "dataset": dataset_name})
            else:
                scenario_execution_plan.append({"scenario": scenario, "dataset": None})
        else:
            chosen_dataset = pick_dataset(preferred=[name for name in scenario.datasets if name in candidate_pool], available=candidate_pool)
            if chosen_dataset is None and selected_datasets is not None and candidate_pool:
                chosen_dataset = sorted(candidate_pool)[0]
            scenario_execution_plan.append({"scenario": scenario, "dataset": chosen_dataset})

    return scenario_execution_plan


def print_dataset_preview(*, dataset_name: str, seeds: Sequence) -> None:  # type: ignore[type-arg]
    """Print a short preview of dataset seed contents based on debug/safety settings."""
    bar = "=" * 66
    print(f"\n{bar}")
    print(f"  Dataset : {dataset_name}")
    print(f"  Seeds   : {len(seeds)}")
    print(bar)
    if PRINT_DATASET_SEEDS and DATASET_PREVIEW_ROWS > 0:
        for idx, seed in enumerate(seeds[:DATASET_PREVIEW_ROWS], start=1):
            preview = re.sub(r"\s+", " ", str(seed.value))[:108]
            print(f"  [{idx:02d}] {preview}")
        if len(seeds) > DATASET_PREVIEW_ROWS:
            print(f"  ... and {len(seeds) - DATASET_PREVIEW_ROWS} more seeds (truncated for brevity).")
    else:
        print("  [preview disabled] Set PRINT_DATASET_SEEDS=true to print sample prompt text.")
    print(bar)


def seed_fingerprint(*, seed: Any) -> str:
    """Build a stable fingerprint for a seed for change detection."""
    value_sha256 = getattr(seed, "value_sha256", None)
    if isinstance(value_sha256, str) and value_sha256:
        return value_sha256
    value_text = str(getattr(seed, "value", ""))
    return hashlib.sha256(value_text.encode("utf-8")).hexdigest()


def dataset_seed_fingerprints(*, seeds: Sequence[Any]) -> set[str]:
    """Build fingerprint set for a seed sequence."""
    return {seed_fingerprint(seed=seed) for seed in seeds}


async def sync_dataset_to_memory_async(*, memory: Any, dataset: SeedDataset, added_by: str) -> dict[str, object]:
    """Sync one dataset to memory: skip unchanged, insert only new/changed seeds."""
    dataset_name = dataset.dataset_name or "unknown_dataset"
    incoming_seeds = list(dataset.seeds)
    incoming_fingerprints = dataset_seed_fingerprints(seeds=incoming_seeds)

    existing_seeds = list(memory.get_seeds(dataset_name=dataset_name))
    existing_fingerprints = dataset_seed_fingerprints(seeds=existing_seeds)

    if existing_fingerprints and incoming_fingerprints == existing_fingerprints:
        return {
            "dataset_name": dataset_name,
            "status": "unchanged",
            "added_count": 0,
            "incoming_count": len(incoming_seeds),
            "existing_count": len(existing_seeds),
        }

    if not existing_fingerprints:
        await memory.add_seed_datasets_to_memory_async(datasets=[dataset], added_by=added_by)
        return {
            "dataset_name": dataset_name,
            "status": "inserted",
            "added_count": len(incoming_seeds),
            "incoming_count": len(incoming_seeds),
            "existing_count": len(existing_seeds),
        }

    seeds_to_add = [seed for seed in incoming_seeds if seed_fingerprint(seed=seed) not in existing_fingerprints]
    if not seeds_to_add:
        return {
            "dataset_name": dataset_name,
            "status": "changed_no_new_seed_values",
            "added_count": 0,
            "incoming_count": len(incoming_seeds),
            "existing_count": len(existing_seeds),
        }

    delta_dataset = SeedDataset(
        seeds=seeds_to_add,
        name=dataset.name,
        dataset_name=dataset.dataset_name,
        harm_categories=dataset.harm_categories,
        description=dataset.description,
        authors=dataset.authors,
        groups=dataset.groups,
        source=dataset.source,
        date_added=dataset.date_added,
        added_by=dataset.added_by,
    )
    await memory.add_seed_datasets_to_memory_async(datasets=[delta_dataset], added_by=added_by)
    return {
        "dataset_name": dataset_name,
        "status": "updated_with_new_seeds",
        "added_count": len(seeds_to_add),
        "incoming_count": len(incoming_seeds),
        "existing_count": len(existing_seeds),
    }
