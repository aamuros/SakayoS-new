"""Process reader — reads real OS process data via psutil.

Provides:
- list_processes()  Read-only snapshot of running processes as ProcessInfo
                    objects, with configurable sorting and result limiting.
"""

from __future__ import annotations

import time

import psutil

from sakayos.core.models import ProcessInfo

# Valid sort keys and their (key-function, reverse?) tuples.
_SORT_OPTIONS: dict[str, tuple] = {
    "pid":    (lambda p: p.pid, False),
    "cpu":    (lambda p: p.cpu_percent, True),
    "memory": (lambda p: p.memory_percent, True),
    "name":   (lambda p: p.name.lower(), False),
}


def list_processes(
    limit: int | None = None,
    sort_by: str = "pid",
    sample_cpu: bool = False,
    sample_interval: float = 0.1,
) -> list[ProcessInfo]:
    """Return a list of :class:`ProcessInfo` snapshots from the live system.

    Parameters
    ----------
    limit:
        Maximum number of results to return.  ``None`` (default) means no
        explicit cap.  A value of 0 or less raises :class:`ValueError`.
    sort_by:
        How to order the results.  Accepted values:

        * ``"pid"``    — ascending by process ID (default)
        * ``"cpu"``    — descending by CPU usage
        * ``"memory"`` — descending by memory usage
        * ``"name"``   — alphabetical (case-insensitive)
    sample_cpu:
        If True, prime per-process CPU counters, wait *sample_interval*
        seconds, then read CPU usage again.  The default False preserves the
        existing fast snapshot behavior.
    sample_interval:
        Number of seconds to wait between CPU samples when *sample_cpu* is
        True.  Negative values raise :class:`ValueError`.

    Raises
    ------
    ValueError
        If *sort_by* is not one of the recognised keys, *limit* is ≤ 0, or
        *sample_interval* is negative.
    """
    # ── validate inputs early ───────────────────────────────────────────
    if sort_by not in _SORT_OPTIONS:
        raise ValueError(
            f"sort_by must be one of {sorted(_SORT_OPTIONS)}, got {sort_by!r}"
        )
    if limit is not None and limit <= 0:
        raise ValueError(
            f"limit must be a positive integer or None, got {limit}"
        )
    if sample_interval < 0:
        raise ValueError(
            f"sample_interval must be zero or greater, got {sample_interval}"
        )

    # ── collect process snapshots ───────────────────────────────────────
    attrs = ["pid", "name", "status", "cpu_percent", "memory_percent", "username"]
    snapshots: list[tuple[psutil.Process, dict]] = []

    for proc in psutil.process_iter(attrs=attrs):
        try:
            info = proc.info
            pid = _normalize_pid(info.get("pid"))
            if pid is None:
                continue

            if sample_cpu:
                proc.cpu_percent(interval=None)

            snapshots.append((proc, info))
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    if sample_cpu and snapshots:
        time.sleep(sample_interval)

    processes: list[ProcessInfo] = []
    for proc, info in snapshots:
        try:
            pid = _normalize_pid(info.get("pid"))
            if pid is None:
                continue

            cpu_percent = (
                _normalize_percent(proc.cpu_percent(interval=None))
                if sample_cpu
                else _normalize_percent(info.get("cpu_percent"))
            )

            processes.append(
                ProcessInfo(
                    pid=pid,
                    name=_normalize_text(info.get("name")),
                    status=_normalize_text(info.get("status")),
                    cpu_percent=cpu_percent,
                    memory_percent=_normalize_percent(info.get("memory_percent")),
                    username=info.get("username"),
                )
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    # ── sort ────────────────────────────────────────────────────────────
    key_fn, reverse = _SORT_OPTIONS[sort_by]
    processes.sort(key=key_fn, reverse=reverse)

    # ── limit ───────────────────────────────────────────────────────────
    if limit is not None:
        processes = processes[:limit]

    return processes


def _normalize_pid(value: object) -> int | None:
    """Return a usable pid, or None when the process identity is unavailable."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_text(value: object) -> str:
    if value is None:
        return "unknown"
    text = str(value)
    return text if text else "unknown"


def _normalize_percent(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
