"""Standalone XPIA attack launcher with dual console/file logging."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _resolve_repo_root() -> Path:
    explicit = os.getenv("PYRIT_REPO_ROOT", "").strip()
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if (candidate / "samples" / "security-evaluator").exists():
            return candidate
    for candidate in (Path("c:/githubrepos/Anil_github_repos/PyRIT"), Path.cwd()):
        if (candidate / "samples" / "security-evaluator").exists():
            return candidate.resolve()
    raise RuntimeError("Set PYRIT_REPO_ROOT to the PyRIT repo root.")


def _resolve_banking_dataset(repo_root: Path) -> Path:
    dataset_path = repo_root / "samples" / "security-evaluator" / "custom_datasets" / "banking_app_security_dataset.json"
    if not dataset_path.exists():
        raise RuntimeError(f"Banking dataset not found: {dataset_path}")
    return dataset_path


class _DualWriter:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.console = sys.__stdout__
        self.file_handle = file_path.open("w", encoding="utf-8", buffering=1)

    def write(self, message: str) -> None:
        self.console.write(message)
        self.console.flush()
        self.file_handle.write(message)
        self.file_handle.flush()

    def flush(self) -> None:
        self.console.flush()
        self.file_handle.flush()

    def close(self) -> None:
        self.file_handle.flush()
        self.file_handle.close()


def _setup_logging(prefix: str) -> tuple[_DualWriter, object, object]:
    log_dir = Path("pyrit_reports")
    log_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{prefix}_{stamp}.log"
    writer = _DualWriter(log_file)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = writer
    sys.stderr = writer
    print(f"[INFO] Logging to: {log_file.resolve()}")
    return writer, original_stdout, original_stderr


def main() -> int:
    writer, original_stdout, original_stderr = _setup_logging(prefix="banking_xpia_attack")
    try:
        repo_root = _resolve_repo_root()
        banking_dataset = _resolve_banking_dataset(repo_root)
        runner = repo_root / "samples" / "security-evaluator" / "scripts" / "app" / "attacks" / "xpia_attack_runner.py"
        if not runner.exists():
            print(f"[ERROR] Runner not found: {runner}")
            return 2

        cmd = [sys.executable, str(runner), *sys.argv[1:]]
        print("[INFO] Launching XPIA runner")
        print(f"[INFO] Banking dataset reference: {banking_dataset}")
        print(f"[INFO] Command: {' '.join(cmd)}")
        print(f"[INFO] Working directory: {repo_root}")
        env = dict(os.environ)
        env["BANKING_DATASET_PATH"] = str(banking_dataset)
        completed = subprocess.run(cmd, cwd=str(repo_root), env=env, check=False)
        print(f"[INFO] Exit code: {completed.returncode}")
        return completed.returncode
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_path = writer.file_path
        writer.close()
        print(f"[INFO] Log written: {log_path.resolve()}")


if __name__ == "__main__":
    raise SystemExit(main())
