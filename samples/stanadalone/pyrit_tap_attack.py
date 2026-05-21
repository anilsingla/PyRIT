#!/usr/bin/env python3
"""Standalone TAP attack runner with unified professional reporting."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from standalone_banking_attack_common import build_common_parser, run_standalone_suite


def main() -> int:
    parser = build_common_parser("Standalone TAP attack runner.", supports_width=True)
    args = parser.parse_args()
    try:
        return asyncio.run(
            run_standalone_suite(
                script_name="tap",
                mode="tap",
                script_path=Path(__file__).resolve(),
                max_tests=args.max_tests,
                tap_width=max(1, args.width),
                temperature=args.temperature,
            )
        )
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())


