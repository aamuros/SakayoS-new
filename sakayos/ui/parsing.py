"""Input parsing helpers for the Dispatch Scheduler UI.

These functions validate and convert raw user input into
SchedulerProcess objects. They are intentionally separated from
core scheduling logic so the UI layer handles its own concerns.
"""

from __future__ import annotations

from sakayos.core.models import SchedulerProcess


DEFAULT_MAX_ARRIVAL_TIME = 1_000_000
DEFAULT_MAX_BURST_TIME = 1_000_000
DEFAULT_MAX_PRIORITY = 1_000_000
DEFAULT_MAX_MEMORY_SIZE = 1_000_000


def _validate_process_id(pid: str, *, label: str = "PID") -> str:
    if not pid:
        raise ValueError(f"{label} cannot be empty")
    if "," in pid:
        raise ValueError(f"{label} cannot contain commas: {pid!r}")
    if any(ch.isspace() for ch in pid):
        raise ValueError(f"{label} cannot contain whitespace: {pid!r}")
    return pid


def _validate_max_value(value: int, max_value: int | None, name: str) -> None:
    if max_value is not None and value > max_value:
        raise ValueError(f"{name} must be <= {max_value}, got {value}")


def parse_process_line(
    line: str,
    *,
    require_priority: bool = False,
    max_arrival_time: int | None = DEFAULT_MAX_ARRIVAL_TIME,
    max_burst_time: int | None = DEFAULT_MAX_BURST_TIME,
    max_priority: int | None = DEFAULT_MAX_PRIORITY,
) -> SchedulerProcess:
    """Parse a single line of process input into a SchedulerProcess.

    Expected format (comma or whitespace separated):
        pid, arrival_time, burst_time[, priority]

    Args:
        line:             raw input string.
        require_priority: if True, a priority value is required.
        max_arrival_time: optional upper bound for arrival_time.
        max_burst_time:   optional upper bound for burst_time.
        max_priority:     optional upper bound for priority.

    Returns:
        A validated SchedulerProcess.

    Raises:
        ValueError: if the input is malformed or values are invalid.
    """
    line = line.strip()
    if not line:
        raise ValueError("Empty process line")

    # Support both comma-separated and whitespace-separated.
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
    else:
        parts = line.split()

    expected = 4 if require_priority else 3
    max_parts = 4

    if len(parts) < expected:
        if require_priority:
            raise ValueError(
                f"Expected 4 fields (pid, arrival, burst, priority), "
                f"got {len(parts)}: {line!r}"
            )
        raise ValueError(
            f"Expected at least 3 fields (pid, arrival, burst), "
            f"got {len(parts)}: {line!r}"
        )

    if len(parts) > max_parts:
        raise ValueError(
            f"Too many fields (max 4), got {len(parts)}: {line!r}"
        )

    pid = _validate_process_id(parts[0], label="PID")

    try:
        arrival_time = int(parts[1])
    except ValueError:
        raise ValueError(
            f"arrival_time must be an integer, got {parts[1]!r}"
        )
    _validate_max_value(arrival_time, max_arrival_time, "arrival_time")

    try:
        burst_time = int(parts[2])
    except ValueError:
        raise ValueError(
            f"burst_time must be an integer, got {parts[2]!r}"
        )
    _validate_max_value(burst_time, max_burst_time, "burst_time")

    priority: int | None = None
    if len(parts) == 4:
        try:
            priority = int(parts[3])
        except ValueError:
            raise ValueError(
                f"priority must be an integer, got {parts[3]!r}"
            )
        _validate_max_value(priority, max_priority, "priority")

    # Delegate validation to SchedulerProcess.__post_init__.
    return SchedulerProcess(
        pid=pid,
        arrival_time=arrival_time,
        burst_time=burst_time,
        priority=priority,
    )


def parse_quantum(raw: str) -> int:
    """Parse and validate a quantum value from raw input.

    Args:
        raw: the user-entered string.

    Returns:
        A positive integer quantum.

    Raises:
        ValueError: if the input is not a positive integer.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("Quantum cannot be empty")
    try:
        q = int(raw)
    except ValueError:
        raise ValueError(f"Quantum must be an integer, got {raw!r}")
    if q <= 0:
        raise ValueError(f"Quantum must be positive, got {q}")
    return q


def parse_process_block(
    text: str,
    *,
    require_priority: bool = False,
    max_arrival_time: int | None = DEFAULT_MAX_ARRIVAL_TIME,
    max_burst_time: int | None = DEFAULT_MAX_BURST_TIME,
    max_priority: int | None = DEFAULT_MAX_PRIORITY,
) -> list[SchedulerProcess]:
    """Parse a multi-line block of process input.

    Each non-empty line is parsed as a single process.

    Args:
        text:             the full text block.
        require_priority: passed through to parse_process_line.
        max_arrival_time: passed through to parse_process_line.
        max_burst_time:   passed through to parse_process_line.
        max_priority:     passed through to parse_process_line.

    Returns:
        A list of SchedulerProcess objects.

    Raises:
        ValueError: on the first malformed line, with the line number.
    """
    if not text or not text.strip():
        raise ValueError("No process data provided")

    processes: list[SchedulerProcess] = []
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue  # skip blank lines and comments
        try:
            proc = parse_process_line(
                stripped,
                require_priority=require_priority,
                max_arrival_time=max_arrival_time,
                max_burst_time=max_burst_time,
                max_priority=max_priority,
            )
        except ValueError as e:
            raise ValueError(f"Line {i}: {e}") from e
        processes.append(proc)

    if not processes:
        raise ValueError("No valid process lines found")

    return processes


def parse_memory_size(
    raw: str,
    *,
    max_size: int | None = DEFAULT_MAX_MEMORY_SIZE,
) -> int:
    """Parse and validate memory size from raw input.

    Args:
        raw:      the user-entered string.
        max_size: optional upper bound for memory size.

    Returns:
        A positive integer size.

    Raises:
        ValueError: if the input is not a positive integer.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("Memory size cannot be empty")
    try:
        size = int(raw)
    except ValueError:
        raise ValueError(f"Memory size must be an integer, got {raw!r}")
    if size <= 0:
        raise ValueError(f"Memory size must be positive, got {size}")
    _validate_max_value(size, max_size, "Memory size")
    return size


def parse_process_id(raw: str) -> str:
    """Parse and validate process ID from raw input.

    Args:
        raw: the user-entered string.

    Returns:
        A cleaned string.

    Raises:
        ValueError: if the input is empty or contains invalid characters.
    """
    cleaned = raw.strip()
    return _validate_process_id(cleaned, label="Process ID")
