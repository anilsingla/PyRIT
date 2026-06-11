#!/usr/bin/env python3
"""Create starter datasets in JSON or PyRIT-native prompt format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _safe_identifier(*, value: str) -> str:
    """Convert free text into a safe Python identifier suffix.

    Args:
        value (str): Input text.

    Returns:
        str: Identifier-safe string.
    """
    cleaned = "".join(char if char.isalnum() else "_" for char in value.strip().lower())
    compact = "_".join(token for token in cleaned.split("_") if token)
    return compact or "custom_dataset"


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI parser for dataset scaffold generation.

    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(
        description="Generate a custom dataset scaffold (JSON or PyRIT .prompt)."
    )
    parser.add_argument("--dataset-name", required=True, help="Dataset name (for example: my_dataset_v1).")
    parser.add_argument("--description", required=True, help="Human-readable dataset description.")
    parser.add_argument(
        "--dataset-type",
        choices=["single-turn", "multi-turn"],
        default="single-turn",
        help="Dataset structure type.",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        default=[],
        help="Prompt text. Repeat this flag to add multiple prompts.",
    )
    parser.add_argument(
        "--objective",
        default="Assess model behavior for this scenario.",
        help="Objective used for multi-turn group generation.",
    )
    parser.add_argument(
        "--seed-group-id",
        default="group_1",
        help="Seed group id for multi-turn dataset generation.",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "pyrit-prompt"],
        default="json",
        help="Primary output format.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Output dataset file path. Defaults by format: custom_dataset.json or custom_dataset.prompt.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--emit-pyrit-code",
        action="store_true",
        help="Also generate a Python scaffold that builds a SeedDataset the PyRIT way.",
    )
    parser.add_argument(
        "--pyrit-code-path",
        type=Path,
        default=None,
        help="Output Python file path for --emit-pyrit-code.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    return parser


def _build_single_turn_payload(*, dataset_name: str, description: str, prompts: list[str]) -> dict[str, object]:
    """Build single-turn dataset payload.

    Args:
        dataset_name (str): Dataset identifier.
        description (str): Dataset description.
        prompts (list[str]): Seed prompt values.

    Returns:
        dict[str, object]: JSON payload.
    """
    seed_values = prompts or ["Replace this with your first custom prompt."]
    seeds = [
        {
            "seed_type": "text",
            "value": value,
            "data_origin": "custom_manual",
            "tags": ["custom"],
        }
        for value in seed_values
    ]

    return {
        "dataset_name": dataset_name,
        "description": description,
        "dataset_type": "single-turn",
        "seeds": seeds,
    }


def _build_multi_turn_payload(
    *,
    dataset_name: str,
    description: str,
    prompts: list[str],
    objective: str,
    seed_group_id: str,
) -> dict[str, object]:
    """Build multi-turn dataset payload.

    Args:
        dataset_name (str): Dataset identifier.
        description (str): Dataset description.
        prompts (list[str]): Turn prompts.
        objective (str): Group objective statement.
        seed_group_id (str): Group id value.

    Returns:
        dict[str, object]: JSON payload.
    """
    turn_values = prompts or [
        "Turn 1 prompt placeholder.",
        "Turn 2 prompt placeholder.",
    ]
    prompt_items = [{"step": index + 1, "value": value} for index, value in enumerate(turn_values)]

    return {
        "dataset_name": dataset_name,
        "description": description,
        "dataset_type": "multi-turn",
        "dynamic_seed_groups": [
            {
                "seed_group_id": seed_group_id,
                "objective": objective,
                "prompts": prompt_items,
            }
        ],
    }


def _write_payload(*, output_path: Path, payload: dict[str, object], force: bool) -> None:
    """Write dataset payload to JSON file.

    Args:
        output_path (Path): Destination path.
        payload (dict[str, object]): JSON payload.
        force (bool): Overwrite guard flag.

    Raises:
        FileExistsError: If output exists and force is not enabled.
    """
    if output_path.exists() and not force:
        raise FileExistsError(f"Output file already exists: {output_path}. Use --force to overwrite.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _yaml_quote(*, value: str) -> str:
    """Encode a string as YAML-safe double-quoted scalar.

    Args:
        value (str): Raw string value.

    Returns:
        str: YAML-safe scalar text.
    """
    return json.dumps(value)


def _build_pyrit_prompt_text(
    *,
    dataset_name: str,
    description: str,
    dataset_type: str,
    prompts: list[str],
    seed_group_id: str,
) -> str:
    """Build a PyRIT-native .prompt dataset scaffold.

    Args:
        dataset_name (str): Dataset identifier.
        description (str): Dataset description.
        dataset_type (str): single-turn or multi-turn.
        prompts (list[str]): Prompt values.
        seed_group_id (str): Group alias for multi-turn prompts.

    Returns:
        str: YAML-compatible .prompt text.
    """
    lines: list[str] = [
        f"dataset_name: {_yaml_quote(value=dataset_name)}",
        f"description: {_yaml_quote(value=description)}",
        "source: \"https://azure.github.io/PyRIT/\"",
        "seeds:",
    ]

    if dataset_type == "single-turn":
        values = prompts or ["Replace this with your first custom prompt."]
        for prompt_value in values:
            lines.extend(
                [
                    f"  - value: {_yaml_quote(value=prompt_value)}",
                    "    data_type: text",
                    "    role: user",
                ]
            )
    else:
        values = prompts or ["Turn 1 prompt placeholder.", "Turn 2 prompt placeholder."]
        for index, prompt_value in enumerate(values):
            lines.extend(
                [
                    f"  - value: {_yaml_quote(value=prompt_value)}",
                    "    data_type: text",
                    f"    prompt_group_alias: {_yaml_quote(value=seed_group_id)}",
                    f"    sequence: {index}",
                    "    role: user",
                ]
            )

    return "\n".join(lines) + "\n"


def _write_text(*, output_path: Path, text: str, force: bool) -> None:
    """Write plain text output with overwrite guard.

    Args:
        output_path (Path): Destination file path.
        text (str): Content text.
        force (bool): Overwrite guard flag.

    Raises:
        FileExistsError: If output exists and force is not enabled.
    """
    if output_path.exists() and not force:
        raise FileExistsError(f"Output file already exists: {output_path}. Use --force to overwrite.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def _default_output_path(*, output_format: str) -> Path:
    """Resolve default dataset output path by format.

    Args:
        output_format (str): Output format type.

    Returns:
        Path: Default output file path.
    """
    if output_format == "pyrit-prompt":
        return Path("custom_dataset.prompt")
    return Path("custom_dataset.json")


def _build_pyrit_code_text(
    *,
    dataset_name: str,
    description: str,
    dataset_type: str,
    prompts: list[str],
    seed_group_id: str,
) -> str:
    """Build Python scaffold that creates SeedDataset using PyRIT models.

    Args:
        dataset_name (str): Dataset identifier.
        description (str): Dataset description.
        dataset_type (str): single-turn or multi-turn.
        prompts (list[str]): Prompt values.
        seed_group_id (str): Group id for multi-turn prompts.

    Returns:
        str: Python source text.
    """
    prompt_values = prompts or [
        "Replace this with your first custom prompt.",
        "Turn 2 prompt placeholder.",
    ]
    escaped_values = ",\n        ".join(json.dumps(value) for value in prompt_values)

    dataset_identifier = _safe_identifier(value=dataset_name)

    if dataset_type == "single-turn":
        builder_block = (
            "seeds = [\n"
            "        SeedPrompt(value=value, data_type=\"text\", role=\"user\")\n"
            "        for value in prompt_values\n"
            "    ]"
        )
    else:
        builder_block = (
            "seeds = [\n"
            "        SeedPrompt(\n"
            "            value=value,\n"
            "            data_type=\"text\",\n"
            f"            prompt_group_id=\"{seed_group_id}\",\n"
            "            sequence=index,\n"
            "            role=\"user\",\n"
            "        )\n"
            "        for index, value in enumerate(prompt_values)\n"
            "    ]"
        )

    return f'''#!/usr/bin/env python3
"""PyRIT-style dataset scaffold generator for {dataset_name}."""

from __future__ import annotations

from pyrit.models import SeedDataset, SeedPrompt


def build_{dataset_identifier}_dataset() -> SeedDataset:
    """Build and return a SeedDataset instance."""
    prompt_values = [
        {escaped_values}
    ]

    {builder_block}

    return SeedDataset(
        dataset_name={json.dumps(dataset_name)},
        description={json.dumps(description)},
        seeds=seeds,
        source="custom_generated",
    )


if __name__ == "__main__":
    dataset = build_{dataset_identifier}_dataset()
    print(f"Built dataset: {{dataset.dataset_name}} with {{len(dataset.seeds)}} seed(s)")
'''


def main() -> int:
    """Run CLI entrypoint.

    Returns:
        int: Exit code.
    """
    parser = _build_parser()
    args = parser.parse_args()

    dataset_name = str(args.dataset_name).strip()
    description = str(args.description).strip()
    prompts = [str(value).strip() for value in args.prompt if str(value).strip()]
    output_format = str(args.output_format).strip()

    if args.output_json is not None:
        output_format = "json"

    output_path = Path(args.output_path) if args.output_path is not None else _default_output_path(output_format=output_format)
    if args.output_json is not None:
        output_path = Path(args.output_json)

    if not dataset_name:
        print("[ERROR] --dataset-name cannot be empty.")
        return 2
    if not description:
        print("[ERROR] --description cannot be empty.")
        return 2

    seed_group_id = str(args.seed_group_id).strip() or "group_1"

    try:
        if output_format == "json":
            if args.dataset_type == "single-turn":
                payload = _build_single_turn_payload(
                    dataset_name=dataset_name,
                    description=description,
                    prompts=prompts,
                )
            else:
                payload = _build_multi_turn_payload(
                    dataset_name=dataset_name,
                    description=description,
                    prompts=prompts,
                    objective=str(args.objective).strip(),
                    seed_group_id=seed_group_id,
                )
            _write_payload(output_path=output_path, payload=payload, force=bool(args.force))
        else:
            prompt_text = _build_pyrit_prompt_text(
                dataset_name=dataset_name,
                description=description,
                dataset_type=str(args.dataset_type),
                prompts=prompts,
                seed_group_id=seed_group_id,
            )
            _write_text(output_path=output_path, text=prompt_text, force=bool(args.force))

        if bool(args.emit_pyrit_code):
            code_path = (
                Path(args.pyrit_code_path)
                if args.pyrit_code_path is not None
                else Path(f"create_{_safe_identifier(value=dataset_name)}_dataset.py")
            )
            code_text = _build_pyrit_code_text(
                dataset_name=dataset_name,
                description=description,
                dataset_type=str(args.dataset_type),
                prompts=prompts,
                seed_group_id=seed_group_id,
            )
            _write_text(output_path=code_path, text=code_text, force=bool(args.force))
            print(f"[OK] Wrote PyRIT code scaffold: {code_path.resolve()}")
    except FileExistsError as exc:
        print(f"[ERROR] {exc}")
        return 2

    print(f"[OK] Wrote dataset scaffold: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
