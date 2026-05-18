#!/usr/bin/env python3
"""Create production-ready custom datasets in JSON and/or PyRIT prompt format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from pyrit.models import SeedDataset
except Exception:
    SeedDataset = None  # type: ignore[assignment]


class DatasetValidationError(ValueError):
    """Raised when dataset input or generated output is invalid."""


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI parser.

    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(
        description="Generate production-ready dataset scaffolds for red-team workflows.",
    )
    parser.add_argument("--dataset-name", required=True, help="Dataset name (for example: my_dataset_v1).")
    parser.add_argument("--description", required=True, help="Human-readable dataset description.")
    parser.add_argument(
        "--dataset-type",
        choices=["single-turn", "multi-turn"],
        default="single-turn",
        help="Dataset conversation structure.",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        default=[],
        help="Prompt text. Repeat this flag for multiple prompts.",
    )
    parser.add_argument(
        "--objective",
        default="",
        help="Objective text for multi-turn datasets (required for multi-turn).",
    )
    parser.add_argument(
        "--seed-group-id",
        default="group_1",
        help="Seed group id for multi-turn prompts.",
    )
    parser.add_argument(
        "--source",
        default="custom_generated",
        help="Dataset source metadata.",
    )
    parser.add_argument(
        "--harm-category",
        action="append",
        default=[],
        help="Harm category. Repeat this flag to add multiple values.",
    )
    parser.add_argument(
        "--group",
        action="append",
        default=[],
        help="Authoring group metadata. Repeat this flag for multiple values.",
    )
    parser.add_argument(
        "--author",
        action="append",
        default=[],
        help="Author metadata. Repeat this flag for multiple values.",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "pyrit-prompt", "both"],
        default="both",
        help="Output format(s) to generate.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Single output path (valid only when output-format is not 'both').",
    )
    parser.add_argument(
        "--json-output-path",
        type=Path,
        default=Path("custom_dataset.production.json"),
        help="JSON output file path.",
    )
    parser.add_argument(
        "--prompt-output-path",
        type=Path,
        default=Path("custom_dataset.production.prompt"),
        help="PyRIT prompt output file path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination files if they already exist.",
    )
    parser.add_argument(
        "--skip-pyrit-validation",
        action="store_true",
        help="Skip validation with PyRIT SeedDataset parser.",
    )
    return parser


def _normalize_values(*, values: list[str]) -> list[str]:
    """Normalize and drop blank string values.

    Args:
        values (list[str]): Raw values.

    Returns:
        list[str]: Normalized values.
    """
    return [item.strip() for item in values if item.strip()]


def _validate_inputs(
    *,
    dataset_name: str,
    description: str,
    dataset_type: str,
    prompts: list[str],
    objective: str,
    seed_group_id: str,
) -> None:
    """Validate user-provided inputs.

    Args:
        dataset_name (str): Dataset name.
        description (str): Dataset description.
        dataset_type (str): Dataset type.
        prompts (list[str]): Prompt values.
        objective (str): Objective text.
        seed_group_id (str): Seed group id.

    Raises:
        DatasetValidationError: If validation fails.
    """
    if not dataset_name:
        raise DatasetValidationError("--dataset-name cannot be empty.")
    if not description:
        raise DatasetValidationError("--description cannot be empty.")
    if any(char.isspace() for char in dataset_name):
        raise DatasetValidationError("--dataset-name should not contain spaces; use '-' or '_' instead.")

    if dataset_type == "single-turn" and len(prompts) < 1:
        raise DatasetValidationError("single-turn datasets require at least one --prompt.")

    if dataset_type == "multi-turn":
        if len(prompts) < 2:
            raise DatasetValidationError("multi-turn datasets require at least two --prompt values.")
        if not objective:
            raise DatasetValidationError("multi-turn datasets require --objective.")
        if not seed_group_id:
            raise DatasetValidationError("multi-turn datasets require a non-empty --seed-group-id.")


def _build_json_payload(
    *,
    dataset_name: str,
    description: str,
    dataset_type: str,
    prompts: list[str],
    objective: str,
    seed_group_id: str,
    source: str,
    harm_categories: list[str],
    groups: list[str],
    authors: list[str],
) -> dict[str, Any]:
    """Build PyRIT-compatible JSON payload from validated inputs.

    Args:
        dataset_name (str): Dataset name.
        description (str): Dataset description.
        dataset_type (str): Dataset type.
        prompts (list[str]): Prompt values.
        objective (str): Objective text.
        seed_group_id (str): Seed group id.
        source (str): Source label.
        harm_categories (list[str]): Harm metadata.
        groups (list[str]): Group metadata.
        authors (list[str]): Author metadata.

    Returns:
        dict[str, Any]: JSON payload.
    """
    base_payload: dict[str, Any] = {
        "dataset_name": dataset_name,
        "description": description,
        "source": source,
    }
    if harm_categories:
        base_payload["harm_categories"] = harm_categories
    if groups:
        base_payload["groups"] = groups
    if authors:
        base_payload["authors"] = authors

    if dataset_type == "single-turn":
        base_payload["seeds"] = [
            {
                "value": prompt,
                "data_type": "text",
                "role": "user",
            }
            for prompt in prompts
        ]
    else:
        base_payload["seeds"] = [
            {
                "value": objective,
                "seed_type": "objective",
                "prompt_group_alias": seed_group_id,
                "sequence": 0,
                "role": "user",
            },
            *[
                {
                    "value": value,
                    "data_type": "text",
                    "prompt_group_alias": seed_group_id,
                    "sequence": index,
                    "role": "user",
                }
                for index, value in enumerate(prompts, start=1)
            ],
        ]

    return base_payload


def _yaml_scalar(*, value: str) -> str:
    """Create YAML-safe scalar using JSON escaping.

    Args:
        value (str): Raw value.

    Returns:
        str: YAML-safe scalar text.
    """
    return json.dumps(value)


def _yaml_key_values(*, key: str, values: list[str]) -> list[str]:
    """Render YAML list for key when values exist.

    Args:
        key (str): YAML key.
        values (list[str]): List values.

    Returns:
        list[str]: Rendered lines.
    """
    if not values:
        return []
    lines = [f"{key}:"]
    for item in values:
        lines.append(f"  - {_yaml_scalar(value=item)}")
    return lines


def _build_pyrit_prompt_text(
    *,
    dataset_name: str,
    description: str,
    dataset_type: str,
    prompts: list[str],
    objective: str,
    seed_group_id: str,
    source: str,
    harm_categories: list[str],
    groups: list[str],
    authors: list[str],
) -> str:
    """Build PyRIT-native prompt text.

    Args:
        dataset_name (str): Dataset name.
        description (str): Dataset description.
        dataset_type (str): Dataset type.
        prompts (list[str]): Prompt values.
        objective (str): Objective text.
        seed_group_id (str): Seed group id.
        source (str): Source label.
        harm_categories (list[str]): Harm metadata.
        groups (list[str]): Group metadata.
        authors (list[str]): Author metadata.

    Returns:
        str: Prompt-format YAML text.
    """
    lines: list[str] = [
        f"dataset_name: {_yaml_scalar(value=dataset_name)}",
        f"description: {_yaml_scalar(value=description)}",
        f"source: {_yaml_scalar(value=source)}",
    ]

    lines.extend(_yaml_key_values(key="harm_categories", values=harm_categories))
    lines.extend(_yaml_key_values(key="groups", values=groups))
    lines.extend(_yaml_key_values(key="authors", values=authors))
    lines.append("seeds:")

    if dataset_type == "single-turn":
        for prompt in prompts:
            lines.extend(
                [
                    f"  - value: {_yaml_scalar(value=prompt)}",
                    "    data_type: text",
                    "    role: user",
                ]
            )
    else:
        lines.extend(
            [
                f"  - value: {_yaml_scalar(value=objective)}",
                "    seed_type: objective",
                f"    prompt_group_alias: {_yaml_scalar(value=seed_group_id)}",
                "    sequence: 0",
                "    role: user",
            ]
        )
        for index, prompt in enumerate(prompts, start=1):
            lines.extend(
                [
                    f"  - value: {_yaml_scalar(value=prompt)}",
                    "    data_type: text",
                    f"    prompt_group_alias: {_yaml_scalar(value=seed_group_id)}",
                    f"    sequence: {index}",
                    "    role: user",
                ]
            )

    return "\n".join(lines) + "\n"


def _resolve_outputs(
    *,
    output_format: str,
    output_path: Path | None,
    json_output_path: Path,
    prompt_output_path: Path,
) -> tuple[Path | None, Path | None]:
    """Resolve concrete output paths by output format.

    Args:
        output_format (str): Output format selector.
        output_path (Path | None): Generic output path.
        json_output_path (Path): JSON path.
        prompt_output_path (Path): Prompt path.

    Returns:
        tuple[Path | None, Path | None]: JSON path and prompt path.

    Raises:
        DatasetValidationError: If path selection is invalid.
    """
    if output_format == "both" and output_path is not None:
        raise DatasetValidationError("--output-path cannot be used when --output-format=both.")

    if output_format == "json":
        return (output_path or json_output_path, None)
    if output_format == "pyrit-prompt":
        return (None, output_path or prompt_output_path)
    return (json_output_path, prompt_output_path)


def _write_atomic(*, output_path: Path, content: str, force: bool) -> None:
    """Write file atomically with overwrite protection.

    Args:
        output_path (Path): Destination path.
        content (str): File content.
        force (bool): Overwrite guard.

    Raises:
        FileExistsError: If destination exists without force.
    """
    if output_path.exists() and not force:
        raise FileExistsError(f"Output file already exists: {output_path}. Use --force to overwrite.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(output_path)


def _validate_with_pyrit(*, json_payload: dict[str, Any] | None, prompt_path: Path | None) -> None:
    """Validate generated outputs using PyRIT parsers when available.

    Args:
        json_payload (dict[str, Any] | None): JSON payload, if generated.
        prompt_path (Path | None): Prompt path, if generated.

    Raises:
        DatasetValidationError: If validation fails.
    """
    if SeedDataset is None:
        print("[WARN] PyRIT not available; skipping parser validation.")
        return

    try:
        if json_payload is not None:
            SeedDataset.from_dict(json_payload)
        if prompt_path is not None:
            SeedDataset.from_yaml_file(str(prompt_path))
    except Exception as exc:
        raise DatasetValidationError(f"PyRIT validation failed: {exc}") from exc


def main() -> int:
    """Run CLI entrypoint.

    Returns:
        int: Process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args()

    dataset_name = str(args.dataset_name).strip()
    description = str(args.description).strip()
    dataset_type = str(args.dataset_type).strip()
    objective = str(args.objective).strip()
    seed_group_id = str(args.seed_group_id).strip()
    source = str(args.source).strip() or "custom_generated"

    prompts = _normalize_values(values=[str(value) for value in args.prompt])
    harm_categories = _normalize_values(values=[str(value) for value in args.harm_category])
    groups = _normalize_values(values=[str(value) for value in args.group])
    authors = _normalize_values(values=[str(value) for value in args.author])

    try:
        _validate_inputs(
            dataset_name=dataset_name,
            description=description,
            dataset_type=dataset_type,
            prompts=prompts,
            objective=objective,
            seed_group_id=seed_group_id,
        )

        output_json_path, output_prompt_path = _resolve_outputs(
            output_format=str(args.output_format),
            output_path=Path(args.output_path) if args.output_path is not None else None,
            json_output_path=Path(args.json_output_path),
            prompt_output_path=Path(args.prompt_output_path),
        )

        json_payload: dict[str, Any] | None = None
        if output_json_path is not None:
            json_payload = _build_json_payload(
                dataset_name=dataset_name,
                description=description,
                dataset_type=dataset_type,
                prompts=prompts,
                objective=objective,
                seed_group_id=seed_group_id,
                source=source,
                harm_categories=harm_categories,
                groups=groups,
                authors=authors,
            )
            _write_atomic(
                output_path=output_json_path,
                content=json.dumps(json_payload, indent=2),
                force=bool(args.force),
            )
            print(f"[OK] Wrote JSON dataset: {output_json_path.resolve()}")

        if output_prompt_path is not None:
            prompt_text = _build_pyrit_prompt_text(
                dataset_name=dataset_name,
                description=description,
                dataset_type=dataset_type,
                prompts=prompts,
                objective=objective,
                seed_group_id=seed_group_id,
                source=source,
                harm_categories=harm_categories,
                groups=groups,
                authors=authors,
            )
            _write_atomic(output_path=output_prompt_path, content=prompt_text, force=bool(args.force))
            print(f"[OK] Wrote PyRIT prompt dataset: {output_prompt_path.resolve()}")

        if not bool(args.skip_pyrit_validation):
            _validate_with_pyrit(json_payload=json_payload, prompt_path=output_prompt_path)
            print("[OK] PyRIT validation passed.")

        return 0
    except (DatasetValidationError, FileExistsError) as exc:
        print(f"[ERROR] {exc}")
        return 2
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
