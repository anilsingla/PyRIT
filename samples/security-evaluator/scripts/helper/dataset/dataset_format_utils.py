#!/usr/bin/env python3
"""Dataset format helpers for starter and PyRIT-compatible payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_optional_list(*, value: object) -> list[str]:
    """Normalize optional list-like metadata values.

    Args:
        value (object): Raw metadata value.

    Returns:
        list[str]: Normalized string list.
    """
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def is_starter_dataset_payload(*, payload: dict[str, Any]) -> bool:
    """Check whether payload matches starter custom dataset schema.

    Args:
        payload (dict[str, Any]): Parsed JSON payload.

    Returns:
        bool: True if payload appears to be starter schema.
    """
    dataset_type = payload.get("dataset_type")
    if dataset_type not in {"single-turn", "multi-turn"}:
        return False

    return "seeds" in payload or "dynamic_seed_groups" in payload


def convert_starter_json_to_pyrit_dict(*, payload: dict[str, Any]) -> dict[str, Any]:
    """Convert starter dataset JSON payload into PyRIT-compatible dictionary.

    Args:
        payload (dict[str, Any]): Starter payload.

    Returns:
        dict[str, Any]: PyRIT-compatible payload.

    Raises:
        ValueError: If required starter fields are missing or invalid.
    """
    dataset_name = str(payload.get("dataset_name", "")).strip()
    description = str(payload.get("description", "")).strip()
    dataset_type = str(payload.get("dataset_type", "")).strip()

    if not dataset_name:
        raise ValueError("Starter payload missing non-empty 'dataset_name'.")
    if not description:
        raise ValueError("Starter payload missing non-empty 'description'.")
    if dataset_type not in {"single-turn", "multi-turn"}:
        raise ValueError("Starter payload 'dataset_type' must be 'single-turn' or 'multi-turn'.")

    pyrit_payload: dict[str, Any] = {
        "dataset_name": dataset_name,
        "description": description,
        "source": str(payload.get("source", "custom_generated")).strip() or "custom_generated",
    }

    harm_categories = _normalize_optional_list(value=payload.get("harm_categories"))
    groups = _normalize_optional_list(value=payload.get("groups"))
    authors = _normalize_optional_list(value=payload.get("authors"))

    if harm_categories:
        pyrit_payload["harm_categories"] = harm_categories
    if groups:
        pyrit_payload["groups"] = groups
    if authors:
        pyrit_payload["authors"] = authors

    if dataset_type == "single-turn":
        seeds_raw = payload.get("seeds", [])
        if not isinstance(seeds_raw, list) or not seeds_raw:
            raise ValueError("Starter single-turn payload requires non-empty 'seeds'.")

        seeds: list[dict[str, Any]] = []
        for item in seeds_raw:
            if not isinstance(item, dict):
                continue
            value = str(item.get("value", "")).strip()
            if not value:
                continue
            seeds.append(
                {
                    "value": value,
                    "data_type": "text",
                    "role": "user",
                }
            )

        if not seeds:
            raise ValueError("Starter single-turn payload contains no valid prompt 'value'.")
        pyrit_payload["seeds"] = seeds
        return pyrit_payload

    groups_raw = payload.get("dynamic_seed_groups", [])
    if not isinstance(groups_raw, list) or not groups_raw:
        raise ValueError("Starter multi-turn payload requires non-empty 'dynamic_seed_groups'.")

    first_group = groups_raw[0]
    if not isinstance(first_group, dict):
        raise ValueError("Starter multi-turn payload contains invalid first group.")

    objective = str(first_group.get("objective", "")).strip()
    seed_group_id = str(first_group.get("seed_group_id", "group_1")).strip() or "group_1"
    prompts_raw = first_group.get("prompts", [])

    if not objective:
        raise ValueError("Starter multi-turn payload requires non-empty group 'objective'.")
    if not isinstance(prompts_raw, list) or len(prompts_raw) < 1:
        raise ValueError("Starter multi-turn payload requires at least one prompt entry.")

    prompt_values: list[str] = []
    for prompt in prompts_raw:
        if not isinstance(prompt, dict):
            continue
        value = str(prompt.get("value", "")).strip()
        if value:
            prompt_values.append(value)

    if not prompt_values:
        raise ValueError("Starter multi-turn payload contains no valid prompt values.")

    seeds = [
        {
            "value": objective,
            "seed_type": "objective",
            "prompt_group_alias": seed_group_id,
            "sequence": 0,
            "role": "user",
        }
    ]
    seeds.extend(
        {
            "value": value,
            "data_type": "text",
            "prompt_group_alias": seed_group_id,
            "sequence": index,
            "role": "user",
        }
        for index, value in enumerate(prompt_values, start=1)
    )

    pyrit_payload["seeds"] = seeds
    return pyrit_payload


def load_json_payload(*, input_path: Path) -> dict[str, Any]:
    """Load JSON file as dictionary payload.

    Args:
        input_path (Path): JSON file path.

    Returns:
        dict[str, Any]: Parsed payload.

    Raises:
        ValueError: If payload is not a dictionary.
    """
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object.")
    return payload
