"""FastAPI service to run security-evaluator utility commands over HTTP/HTTPS."""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .models import (
    CancelResponse,
    HealthResponse,
    OptionCatalogResponse,
    RunOptions,
    RunOutputResponse,
    RunStartRequest,
    RunStartResponse,
    RunStatusResponse,
)


RunJobStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


def _as_bool(*, value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _require_api_auth(*, authorization: str | None = Header(default=None)) -> None:
    """Optionally enforce bearer authentication for API endpoints.

    Controlled by env vars:
    - API_AUTH_ENABLED: false by default.
    - API_BEARER_TOKEN: required only when API_AUTH_ENABLED is true.
    """

    auth_enabled = _as_bool(value=os.getenv("API_AUTH_ENABLED"), default=False)
    if not auth_enabled:
        return

    configured_token = os.getenv("API_BEARER_TOKEN", "")
    if not configured_token:
        raise HTTPException(status_code=500, detail="API auth enabled but API_BEARER_TOKEN is not configured")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    scheme, _, supplied_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not supplied_token:
        raise HTTPException(status_code=401, detail="Authorization header must use Bearer token")

    if not secrets.compare_digest(supplied_token, configured_token):
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@dataclass
class RunJob:
    """In-memory representation of one CLI execution job.

    Attributes:
        job_id (str): Job identifier.
        command (list[str]): Subprocess command list.
        output_file (Path): Captured stdout/stderr path.
        status (RunJobStatus): Current status.
        created_at (str): UTC timestamp created.
        started_at (str | None): UTC timestamp started.
        finished_at (str | None): UTC timestamp finished.
        return_code (int | None): Process return code.
        process (subprocess.Popen[str] | None): Child process handle.
    """

    job_id: str
    command: list[str]
    output_file: Path
    status: RunJobStatus = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    finished_at: str | None = None
    return_code: int | None = None
    process: subprocess.Popen[str] | None = None


class JobStore:
    """Thread-safe in-memory store for subprocess jobs."""

    ATTACK_MODES: tuple[str, ...] = ("redteam", "tap", "crescendo", "xpia", "baseline", "rescore", "report")
    TURN_MODES: tuple[str, ...] = ("single", "multi")
    CONVERTERS: tuple[str, ...] = (
        "base64",
        "rot13",
        "caesar",
        "atbash",
        "flip",
        "leetspeak",
        "unicode_confusable",
        "string_join",
        "char_swap",
        "emoji",
        "random_caps",
        "tone_persuasive",
        "variation",
        "translation_french",
    )
    SCORERS: tuple[str, ...] = (
        "substring",
        "self_ask_true_false",
        "self_ask_scale",
        "scale_threshold_0_7",
        "refusal",
        "compliance_inverted_refusal",
    )

    def __init__(self, *, workspace_root: Path) -> None:
        """Initialize the store.

        Args:
            workspace_root (Path): Sample workspace root.
        """

        self._workspace_root = workspace_root
        self._runner = workspace_root / "scripts" / "runners" / "main.py"
        self._output_root = workspace_root / "reports" / "api_runs"
        self._output_root.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, RunJob] = {}
        self._lock = threading.Lock()

    def create_job(self, *, options: RunOptions) -> RunJob:
        """Create and start a subprocess-backed run job.

        Args:
            options (RunOptions): Parsed run options.

        Returns:
            RunJob: Created job with running subprocess.
        """

        job_id = uuid.uuid4().hex
        output_file = self._output_root / f"{job_id}.log"
        command = self._build_command(options=options)
        job = RunJob(job_id=job_id, command=command, output_file=output_file)

        with output_file.open(mode="w", encoding="utf-8") as handle:
            process = subprocess.Popen(
                command,
                cwd=str(self._workspace_root),
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        job.process = process
        job.status = "running"
        job.started_at = now_utc

        with self._lock:
            self._jobs[job_id] = job

        watcher = threading.Thread(target=self._watch_job, kwargs={"job_id": job_id}, daemon=True)
        watcher.start()
        return job

    def get_job(self, *, job_id: str) -> RunJob:
        """Return a job by ID.

        Args:
            job_id (str): Job identifier.

        Returns:
            RunJob: Existing job.

        Raises:
            KeyError: If job does not exist.
        """

        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            return self._jobs[job_id]

    def list_jobs(self) -> list[RunJob]:
        """List all jobs ordered by creation.

        Returns:
            list[RunJob]: Current jobs.
        """

        with self._lock:
            return list(self._jobs.values())

    def cancel_job(self, *, job_id: str) -> RunJob:
        """Cancel a running job.

        Args:
            job_id (str): Job identifier.

        Returns:
            RunJob: Updated job.

        Raises:
            KeyError: If job does not exist.
        """

        job = self.get_job(job_id=job_id)
        if job.process and job.process.poll() is None:
            job.process.terminate()
            job.status = "cancelled"
            job.finished_at = datetime.now(timezone.utc).isoformat()
        return job

    def read_tail(self, *, job_id: str, tail_lines: int) -> str:
        """Read tail output from the job log file.

        Args:
            job_id (str): Job identifier.
            tail_lines (int): Number of lines from file end.

        Returns:
            str: Tail output text.
        """

        job = self.get_job(job_id=job_id)
        if not job.output_file.exists():
            return ""

        with job.output_file.open(mode="r", encoding="utf-8") as handle:
            lines = handle.readlines()
        return "".join(lines[-tail_lines:])

    def _watch_job(self, *, job_id: str) -> None:
        """Wait for process completion and update status.

        Args:
            job_id (str): Job identifier.
        """

        try:
            job = self.get_job(job_id=job_id)
        except KeyError:
            return

        if not job.process:
            return

        return_code = job.process.wait()
        job.return_code = return_code
        if job.status != "cancelled":
            job.status = "completed" if return_code == 0 else "failed"
        job.finished_at = datetime.now(timezone.utc).isoformat()

    def _build_command(self, *, options: RunOptions) -> list[str]:
        """Build python command from RunOptions.

        Args:
            options (RunOptions): Parsed run options.

        Returns:
            list[str]: Command tokens.
        """

        command: list[str] = [sys.executable, str(self._runner), "--attack-mode", options.attack_mode]

        command.extend(["--turn-mode", options.turn_mode])
        command.extend(self._serialize_list_flag(flag="--converters", values=options.converters))
        command.extend(self._serialize_list_flag(flag="--datasets", values=options.datasets))
        command.extend(self._serialize_list_flag(flag="--scorers", values=options.scorers))
        command.extend(self._serialize_list_flag(flag="--scenarios", values=options.scenarios))
        command.extend(self._serialize_list_flag(flag="--filter-owasp", values=options.filter_owasp))

        command.extend(self._serialize_optional_int(flag="--tap-width", value=options.tap_width))
        command.extend(self._serialize_optional_int(flag="--tap-depth", value=options.tap_depth))
        command.extend(self._serialize_optional_int(flag="--tap-branching-factor", value=options.tap_branching_factor))
        command.extend(self._serialize_optional_int(flag="--max-backtracks", value=options.max_backtracks))
        command.extend(self._serialize_optional_int(flag="--max-turns", value=options.max_turns))
        command.extend(self._serialize_optional_int(flag="--max-seeds", value=options.max_seeds))

        command.extend(self._serialize_optional_path(flag="--output-json", value=options.output_json))
        command.extend(self._serialize_optional_path(flag="--output-html", value=options.output_html))
        command.extend(self._serialize_optional_path(flag="--output-md", value=options.output_md))

        if options.all_converters:
            command.append("--all-converters")
        if options.all_datasets:
            command.append("--all-datasets")
        if options.all_scorers:
            command.append("--all-scorers")
        if options.dry_run:
            command.append("--dry-run")
        if options.local_datasets_only:
            command.append("--local-datasets-only")
        if options.open_report:
            command.append("--open")

        return command

    @staticmethod
    def _serialize_list_flag(*, flag: str, values: list[str]) -> list[str]:
        """Serialize list-valued flags.

        Args:
            flag (str): CLI flag.
            values (list[str]): Value list.

        Returns:
            list[str]: Flattened tokens.
        """

        if not values:
            return []
        return [flag, *values]

    @staticmethod
    def _serialize_optional_int(*, flag: str, value: int | None) -> list[str]:
        """Serialize optional integer flags.

        Args:
            flag (str): CLI flag.
            value (int | None): Integer value.

        Returns:
            list[str]: Flattened tokens.
        """

        if value is None:
            return []
        return [flag, str(value)]

    @staticmethod
    def _serialize_optional_path(*, flag: str, value: str | None) -> list[str]:
        """Serialize optional path flags.

        Args:
            flag (str): CLI flag.
            value (str | None): Path value.

        Returns:
            list[str]: Flattened tokens.
        """

        if not value:
            return []
        return [flag, value]


BASE_DIR = Path(__file__).resolve().parents[1]
STORE = JobStore(workspace_root=BASE_DIR)
app = FastAPI(title="RedTeam Ollama Utility API", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check_async() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Health payload.
    """

    return HealthResponse()


@app.get("/api/v1/options", response_model=OptionCatalogResponse, dependencies=[Depends(_require_api_auth)])
async def list_options_async() -> OptionCatalogResponse:
    """Return supported utility options.

    Returns:
        OptionCatalogResponse: Option catalog for clients.
    """

    return OptionCatalogResponse(
        attack_modes=list(JobStore.ATTACK_MODES),
        turn_modes=list(JobStore.TURN_MODES),
        converters=list(JobStore.CONVERTERS),
        scorers=list(JobStore.SCORERS),
    )


@app.post("/api/v1/runs", response_model=RunStartResponse, dependencies=[Depends(_require_api_auth)])
async def start_run_async(payload: RunStartRequest) -> RunStartResponse:
    """Start a background run.

    Args:
        payload (RunStartRequest): Run start payload.

    Returns:
        RunStartResponse: Accepted job metadata.
    """

    job = STORE.create_job(options=payload.options)
    return RunStartResponse(job_id=job.job_id, status=job.status, output_file=str(job.output_file))


@app.post("/api/v1/runs/dry-run", response_model=RunStartResponse, dependencies=[Depends(_require_api_auth)])
async def start_dry_run_async(payload: RunStartRequest) -> RunStartResponse:
    """Start a dry-run command in background.

    Args:
        payload (RunStartRequest): Run start payload.

    Returns:
        RunStartResponse: Accepted job metadata.
    """

    dry_options = payload.options.model_copy(update={"dry_run": True})
    job = STORE.create_job(options=dry_options)
    return RunStartResponse(job_id=job.job_id, status=job.status, output_file=str(job.output_file))


@app.get("/api/v1/runs", response_model=list[RunStatusResponse], dependencies=[Depends(_require_api_auth)])
async def list_runs_async() -> list[RunStatusResponse]:
    """List known run jobs.

    Returns:
        list[RunStatusResponse]: Current job statuses.
    """

    jobs = STORE.list_jobs()
    return [
        RunStatusResponse(
            job_id=job.job_id,
            status=job.status,
            command=job.command,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            return_code=job.return_code,
            output_file=str(job.output_file),
        )
        for job in jobs
    ]


@app.get("/api/v1/runs/{job_id}", response_model=RunStatusResponse, dependencies=[Depends(_require_api_auth)])
async def get_run_status_async(job_id: str) -> RunStatusResponse:
    """Get one run status by job ID.

    Args:
        job_id (str): Job identifier.

    Returns:
        RunStatusResponse: Run status.

    Raises:
        HTTPException: If job is not found.
    """

    try:
        job = STORE.get_job(job_id=job_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error

    return RunStatusResponse(
        job_id=job.job_id,
        status=job.status,
        command=job.command,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        return_code=job.return_code,
        output_file=str(job.output_file),
    )


@app.get("/api/v1/runs/{job_id}/output", response_model=RunOutputResponse, dependencies=[Depends(_require_api_auth)])
async def get_run_output_async(
    job_id: str,
    *,
    tail_lines: int = Query(default=200, ge=1, le=5000),
) -> RunOutputResponse:
    """Get run output tail.

    Args:
        job_id (str): Job identifier.
        tail_lines (int): Tail line count.

    Returns:
        RunOutputResponse: Tail output payload.

    Raises:
        HTTPException: If job is not found.
    """

    try:
        output = STORE.read_tail(job_id=job_id, tail_lines=tail_lines)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error

    return RunOutputResponse(job_id=job_id, tail_lines=tail_lines, output=output)


@app.post("/api/v1/runs/{job_id}/cancel", response_model=CancelResponse, dependencies=[Depends(_require_api_auth)])
async def cancel_run_async(job_id: str) -> CancelResponse:
    """Cancel a running job.

    Args:
        job_id (str): Job identifier.

    Returns:
        CancelResponse: Updated status.

    Raises:
        HTTPException: If job is not found.
    """

    try:
        job = STORE.cancel_job(job_id=job_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error

    return CancelResponse(job_id=job.job_id, status=job.status)
