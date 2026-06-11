# Utility for dual output and color formatting
import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output with Windows compatibility."""
    CYAN = '\033[96m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    AMBER = '\033[38;5;208m'  # Orange/Amber color
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    DIM = '\033[2m'
    # Composite styles
    SUCCESS = f'{GREEN}{BOLD}'
    ERROR = f'{RED}{BOLD}'
    WARNING = f'{YELLOW}{BOLD}'
    INFO = f'{CYAN}{BOLD}'
    HEADER = f'{CYAN}{BOLD}{UNDERLINE}'


def _env_flag(name: str, default: bool) -> bool:
    """Parse common true/false environment flag values."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ENABLE_WAIT_SPINNER = _env_flag("ENABLE_WAIT_SPINNER", True)
ENABLE_LIVE_SCORER_FEED = _env_flag("ENABLE_LIVE_SCORER_FEED", True)


def print_banner(*, title: str, width: int = 66) -> None:
    """Print a consistent section banner with color styling."""
    print(f"\n{Colors.HEADER}{'#' * width}{Colors.RESET}")
    print(f"  {Colors.HEADER}{title}{Colors.RESET}")
    print(f"{Colors.HEADER}{'#' * width}{Colors.RESET}")


def print_divider(*, width: int = 66) -> None:
    """Print a subtle cyan divider line."""
    print(f"{Colors.CYAN}{'─' * width}{Colors.RESET}")


async def await_with_spinner(*, label: str, awaitable):
    """Await long-running operation while showing a lightweight spinner."""
    if not ENABLE_WAIT_SPINNER:
        return await awaitable

    frames = "|/-\\"
    idx = 0
    started = time.monotonic()
    task = asyncio.create_task(awaitable)

    while not task.done():
        elapsed = time.monotonic() - started
        print(
            f"\r{Colors.DIM}  ⏳ {label} {frames[idx % len(frames)]}  {elapsed:5.1f}s{Colors.RESET}",
            end="",
            flush=True,
        )
        idx += 1
        await asyncio.sleep(0.2)

    print("\r" + " " * 100 + "\r", end="", flush=True)
    return await task


def _to_bool_or_none(*, value: object) -> bool | None:
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None


def _to_float_or_none(*, value: object) -> float | None:
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _format_scorer_verdict(*, key: str, value: object) -> str:
    bool_value = _to_bool_or_none(value=value)
    if bool_value is True:
        if key == "self_ask_true_false":
            return f"{Colors.RED}ATTACK SUCCEEDED{Colors.RESET}"
        if key == "refusal":
            return f"{Colors.GREEN}REFUSAL DETECTED{Colors.RESET}"
        return f"{Colors.RED}TRUE{Colors.RESET}"
    if bool_value is False:
        if key == "self_ask_true_false":
            return f"{Colors.GREEN}ATTACK BLOCKED{Colors.RESET}"
        if key == "refusal":
            return f"{Colors.RED}NO REFUSAL{Colors.RESET}"
        return f"{Colors.GREEN}FALSE{Colors.RESET}"

    if key in {"self_ask_scale", "scale_raw"}:
        score = _to_float_or_none(value=value)
        if score is not None:
            normalized = score * 100.0
            if normalized <= 20:
                return f"{Colors.GREEN}LOW RISK ({normalized:.1f}/100){Colors.RESET}"
            if normalized <= 40:
                return f"{Colors.YELLOW}MEDIUM RISK ({normalized:.1f}/100){Colors.RESET}"
            if normalized <= 60:
                return f"{Colors.AMBER}MODERATE RISK ({normalized:.1f}/100){Colors.RESET}"
            return f"{Colors.RED}HIGH RISK ({normalized:.1f}/100){Colors.RESET}"

    return f"{Colors.WHITE}{value}{Colors.RESET}"


def print_scorer_comparison(*, comparison: dict[str, object], title: str = "SCORER COMPARISON") -> None:
    """Print a professional, color-coded scorer comparison block."""
    ordered_keys = [
        "self_ask_true_false",
        "self_ask_scale",
        "scale_threshold_0_7",
        "refusal",
        "compliance_inverted_refusal",
        "substring",
        "weighted_majority",
        "weighted_confidence",
        "weighted_disagreement",
        "scale_vote",
        "scale_raw",
    ]

    print(f"{Colors.CYAN}    ┌─ {title} {Colors.DIM}{'─' * 42}{Colors.RESET}")
    any_rows = False
    for key in ordered_keys:
        if key not in comparison:
            continue
        any_rows = True
        value = comparison.get(key)
        verdict = _format_scorer_verdict(key=key, value=value)
        print(f"{Colors.CYAN}    │  ├─ {key}:{Colors.RESET} {verdict}")

    if not any_rows:
        print(f"{Colors.CYAN}    │  └─ No scorer data returned.{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}    │  └─ End of scorer details{Colors.RESET}")

    print(f"{Colors.CYAN}    └{'─' * 63}{Colors.RESET}")

def enable_colors_windows():
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

enable_colors_windows()


def _console_safe(text: str) -> str:
    """Best-effort conversion for consoles that cannot encode some Unicode symbols."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    except Exception:
        return text

class DualWriter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_handle = open(file_path, 'w', encoding='utf-8', buffering=1)
        self.console = sys.stdout
        self.is_closed = False
        self.line_count = 0
    def write(self, message):
        try:
            self.console.write(_console_safe(message))
            self.console.flush()
            self.file_handle.write(message)
            self.file_handle.flush()
            try:
                import os
                os.fsync(self.file_handle.fileno())
            except Exception:
                pass
            if '\n' in message:
                self.line_count += message.count('\n')
        except Exception as e:
            self.console.write(f"[LOGGING ERROR: {str(e)}]\n")
            self.console.flush()
    def flush(self):
        try:
            self.console.flush()
        except Exception:
            pass
        if not self.is_closed:
            try:
                self.file_handle.flush()
                try:
                    import os
                    os.fsync(self.file_handle.fileno())
                except Exception:
                    pass
            except Exception:
                pass
    def close(self):
        if not self.is_closed:
            try:
                self.file_handle.flush()
                try:
                    import os
                    os.fsync(self.file_handle.fileno())
                except Exception:
                    pass
                self.file_handle.close()
            except Exception as e:
                self.console.write(f"[ERROR closing log file: {str(e)}]\n")
            self.is_closed = True
    def get_log_path(self):
        return str(self.file_path)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

def setup_logging(log_dir_name="pyrit_sec_eval_logs", prefix="security_eval_run"):
    log_dir = Path(log_dir_name)
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{prefix}_{timestamp}.log"
    sys.stdout.write(_console_safe(f"\n{Colors.INFO}{'='*80}{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.INFO}LOG FILE INITIALIZATION{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.INFO}{'='*80}{Colors.RESET}\n\n"))
    sys.stdout.write(_console_safe(f"{Colors.GREEN}Log File Path:{Colors.RESET} {Colors.CYAN}{log_file.absolute()}{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.GREEN}Capture Mode:{Colors.RESET} {Colors.CYAN}DUAL OUTPUT (Screen + File){Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.GREEN}File Format:{Colors.RESET} {Colors.CYAN}UTF-8 with ANSI Colors{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.GREEN}Sync Method:{Colors.RESET} {Colors.CYAN}Real-time with Disk Sync{Colors.RESET}\n\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}Capturing Information:{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}  - All console output (both stdout and stderr){Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}  - All colors and formatting{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}  - All test results and scores{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}  - All system messages and errors{Colors.RESET}\n"))
    sys.stdout.write(_console_safe(f"{Colors.DIM}  - Real-time synchronization to disk{Colors.RESET}\n\n"))
    sys.stdout.flush()
    return DualWriter(log_file)
