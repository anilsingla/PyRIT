"""Pydantic models for security-evaluator API requests and responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class RunOptions(BaseModel):
    """Execution options for a red-team run command.

    Attributes:
        attack_mode (Literal): Attack mode used by scripts/app/main.py.
        turn_mode (Literal): Conversation mode, single or multi.
        converters (list[str]): Converter keys.
        all_converters (bool): Whether to use all converters.
        datasets (list[str]): Dataset names or file paths.
        all_datasets (bool): Whether to use all datasets.
        scorers (list[str]): Scorer keys.
        all_scorers (bool): Whether to use all scorers.
        scenarios (list[str]): OWASP scenario IDs, e.g. LLM01.
        dry_run (bool): Print plan only when true.
        local_datasets_only (bool): Skip remote dataset provider fetch.
        tap_width (int | None): TAP width override.
        tap_depth (int | None): TAP depth override.
        tap_branching_factor (int | None): TAP branching factor override.
        max_backtracks (int | None): Crescendo max backtracks.
        max_turns (int | None): Maximum conversation turns.
        max_seeds (int | None): Baseline max seeds.
        filter_owasp (list[str]): Rescore OWASP filter IDs.
        output_json (str | None): Rescore JSON output path.
        output_html (str | None): Report HTML output path.
        output_md (str | None): Report markdown output path.
        open_report (bool): Open report in browser.
    """

    attack_mode: Literal["redteam", "tap", "crescendo", "xpia", "baseline", "rescore", "report"] = "baseline"
    turn_mode: Literal["single", "multi"] = "single"

    converters: list[str] = Field(default_factory=list)
    all_converters: bool = False

    datasets: list[str] = Field(default_factory=list)
    all_datasets: bool = False

    scorers: list[str] = Field(default_factory=list)
    all_scorers: bool = False

    scenarios: list[str] = Field(default_factory=list)

    dry_run: bool = False
    local_datasets_only: bool = False

    tap_width: int | None = None
    tap_depth: int | None = None
    tap_branching_factor: int | None = None

    max_backtracks: int | None = None
    max_turns: int | None = None
    max_seeds: int | None = None

    filter_owasp: list[str] = Field(default_factory=list)

    output_json: str | None = None
    output_html: str | None = None
    output_md: str | None = None
    open_report: bool = False


class RunStartRequest(BaseModel):
    """Request model to start a run.

    Attributes:
        options (RunOptions): Full run option payload.
    """

    options: RunOptions


class RunStartResponse(BaseModel):
    """Response model returned when a run is accepted.

    Attributes:
        job_id (str): Unique run identifier.
        status (str): Current job state.
        output_file (str): File path where command output is captured.
    """

    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    output_file: str


class RunStatusResponse(BaseModel):
    """Response model describing job status.

    Attributes:
        job_id (str): Job ID.
        status (str): Job status.
        command (list[str]): Executed command.
        created_at (str): UTC timestamp for creation.
        started_at (str | None): UTC timestamp for start.
        finished_at (str | None): UTC timestamp for finish.
        return_code (int | None): Process return code.
        output_file (str): Captured output path.
    """

    job_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    command: list[str]
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    return_code: int | None = None
    output_file: str


class RunOutputResponse(BaseModel):
    """Response model with tail output lines.

    Attributes:
        job_id (str): Job ID.
        tail_lines (int): Requested tail line count.
        output (str): Tail output content.
    """

    job_id: str
    tail_lines: int
    output: str


class CancelResponse(BaseModel):
    """Response model after cancel request.

    Attributes:
        job_id (str): Job ID.
        status (str): Updated status.
    """

    job_id: str
    status: Literal["cancelled", "completed", "failed", "running", "queued"]


class HealthResponse(BaseModel):
    """Simple health response for probes.

    Attributes:
        status (str): Service health.
        timestamp (str): UTC timestamp.
        service (str): Service name.
    """

    status: Literal["healthy"] = "healthy"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    service: str = "redteam-ollama-api"


class OptionCatalogResponse(BaseModel):
    """Response model listing supported command options.

    Attributes:
        attack_modes (list[str]): Supported attack modes.
        turn_modes (list[str]): Supported turn modes.
        converters (list[str]): Supported converter keys.
        scorers (list[str]): Supported scorer keys.
    """

    attack_modes: list[str]
    turn_modes: list[str]
    converters: list[str]
    scorers: list[str]
