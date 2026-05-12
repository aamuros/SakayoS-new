"""Data models for SakayOS.

Defines the core data structures used across the system:
- SchedulerProcess  — a process to be scheduled (a "passenger")
- TimelineEntry     — one slot in a scheduling Gantt chart
- MemoryBlock       — a contiguous region of simulated memory
- ProcessInfo       — a snapshot of a real OS process (via psutil)
"""

from __future__ import annotations

from dataclasses import dataclass


# ── SchedulerProcess ────────────────────────────────────────────────────────


@dataclass
class SchedulerProcess:
    """A process waiting to be dispatched by the CPU scheduler.

    Attributes:
        pid:          Unique process identifier (e.g. "P1").
        arrival_time: Time unit at which the process arrives (>= 0).
        burst_time:   CPU time the process requires (> 0).
        priority:     Optional priority level (lower = higher priority).
    """

    pid: str
    arrival_time: int
    burst_time: int
    priority: int | None = None

    def __post_init__(self) -> None:
        if self.arrival_time < 0:
            raise ValueError(
                f"arrival_time must be >= 0, got {self.arrival_time}"
            )
        if self.burst_time <= 0:
            raise ValueError(
                f"burst_time must be > 0, got {self.burst_time}"
            )


# ── TimelineEntry ───────────────────────────────────────────────────────────


@dataclass
class TimelineEntry:
    """One continuous execution slice in a scheduling timeline.

    Attributes:
        pid:   Process identifier that ran during this slice.
        start: Time unit when execution began.
        end:   Time unit when execution stopped (exclusive, must be > start).
    """

    pid: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                f"end must be greater than start, got start={self.start}, end={self.end}"
            )

    @property
    def duration(self) -> int:
        """Number of time units this entry spans."""
        return self.end - self.start


# ── MemoryBlock ─────────────────────────────────────────────────────────────


@dataclass
class MemoryBlock:
    """A contiguous block of simulated memory.

    Attributes:
        start:      Starting address of the block (>= 0).
        size:       Size of the block in units (> 0).
        process_id: ID of the process occupying this block, or None if free.
    """

    start: int
    size: int
    process_id: str | None

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(
                f"start must be >= 0, got {self.start}"
            )
        if self.size <= 0:
            raise ValueError(
                f"size must be > 0, got {self.size}"
            )

    @property
    def is_free(self) -> bool:
        """Return True if this block is unoccupied."""
        return self.process_id is None


# ── ProcessInfo ─────────────────────────────────────────────────────────────


@dataclass
class ProcessInfo:
    """Snapshot of a real OS process (typically from psutil).

    Attributes:
        pid:            OS-level process ID.
        name:           Process name.
        status:         Current status string (e.g. "running", "sleeping").
        cpu_percent:    CPU usage percentage.
        memory_percent: Memory usage percentage.
        username:       Owner of the process, or None if unavailable.
    """

    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    username: str | None
