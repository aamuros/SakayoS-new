"""Process reader — reads real OS process data via psutil.

Provides:
- list_processes()  Read-only snapshot of running processes as ProcessInfo
                    objects, with configurable sorting and result limiting.
"""

from __future__ import annotations

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

    Raises
    ------
    ValueError
        If *sort_by* is not one of the recognised keys **or** *limit* is ≤ 0.
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

    # ── collect process snapshots ───────────────────────────────────────
    attrs = ["pid", "name", "status", "cpu_percent", "memory_percent", "username"]
    processes: list[ProcessInfo] = []

    for proc in psutil.process_iter(attrs=attrs):
        try:
            info = proc.info
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

        processes.append(
            ProcessInfo(
                pid=info["pid"],
                name=info["name"],
                status=info["status"],
                cpu_percent=info["cpu_percent"],
                memory_percent=info["memory_percent"],
                username=info.get("username"),
            )
        )

    # ── sort ────────────────────────────────────────────────────────────
    key_fn, reverse = _SORT_OPTIONS[sort_by]
    processes.sort(key=key_fn, reverse=reverse)

    # ── limit ───────────────────────────────────────────────────────────
    if limit is not None:
        processes = processes[:limit]

    return processes
