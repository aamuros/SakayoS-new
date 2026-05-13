"""CPU scheduling algorithm simulations.

Pure, deterministic functions — no UI, no I/O, no side effects.

Algorithms:
- First Come First Serve (FCFS)    — non-preemptive
- Shortest Job First (SJF)         — non-preemptive
- Round Robin (RR)                 — preemptive, fixed time quantum
- Priority Scheduling              — non-preemptive, lower number = higher priority

Each scheduler accepts a list of SchedulerProcess and returns a list of
TimelineEntry representing the Gantt chart of execution.
"""

from __future__ import annotations

from sakayos.core.models import SchedulerProcess, TimelineEntry


# ── Shared helpers ──────────────────────────────────────────────────────────


def _validate_no_duplicate_pids(processes: list[SchedulerProcess]) -> None:
    """Raise ValueError if any two processes share the same pid."""
    seen: set[str] = set()
    for p in processes:
        if p.pid in seen:
            raise ValueError(f"Duplicate pid found: {p.pid!r}")
        seen.add(p.pid)


def _next_arrival(processes: list[SchedulerProcess], current_time: int) -> int:
    """Return the earliest arrival_time that is > current_time.

    Assumes at least one process has arrival_time > current_time.
    """
    return min(
        p.arrival_time for p in processes if p.arrival_time > current_time
    )


# ── FCFS ────────────────────────────────────────────────────────────────────


def schedule_fcfs(processes: list[SchedulerProcess]) -> list[TimelineEntry]:
    """First Come First Serve — non-preemptive.

    Tie-breaking: arrival_time → input order → pid.
    """
    if not processes:
        return []
    _validate_no_duplicate_pids(processes)

    # Stable-sort by arrival_time; input order is preserved for ties.
    ordered = sorted(
        enumerate(processes),
        key=lambda ip: (ip[1].arrival_time, ip[0], ip[1].pid),
    )

    timeline: list[TimelineEntry] = []
    current_time = 0

    for _idx, proc in ordered:
        # If the CPU is idle, jump to the process's arrival time.
        start = max(current_time, proc.arrival_time)
        end = start + proc.burst_time
        timeline.append(TimelineEntry(pid=proc.pid, start=start, end=end))
        current_time = end

    return timeline


# ── SJF ─────────────────────────────────────────────────────────────────────


def schedule_sjf(processes: list[SchedulerProcess]) -> list[TimelineEntry]:
    """Shortest Job First — non-preemptive.

    At each scheduling decision point the algorithm picks the arrived process
    with the smallest burst_time.

    Tie-breaking: burst_time → arrival_time → input order → pid.
    """
    if not processes:
        return []
    _validate_no_duplicate_pids(processes)

    # Pair each process with its original index for deterministic tie-breaking.
    remaining = [(i, p) for i, p in enumerate(processes)]
    timeline: list[TimelineEntry] = []
    current_time = 0

    while remaining:
        # Find processes that have arrived by current_time.
        ready = [(i, p) for i, p in remaining if p.arrival_time <= current_time]

        if not ready:
            # CPU idle — jump to the next arrival.
            current_time = min(p.arrival_time for _, p in remaining)
            ready = [(i, p) for i, p in remaining if p.arrival_time <= current_time]

        # Pick shortest burst; break ties by arrival_time, index, pid.
        ready.sort(key=lambda ip: (ip[1].burst_time, ip[1].arrival_time, ip[0], ip[1].pid))
        chosen_idx, chosen_proc = ready[0]

        start = current_time
        end = start + chosen_proc.burst_time
        timeline.append(TimelineEntry(pid=chosen_proc.pid, start=start, end=end))
        current_time = end
        remaining = [(i, p) for i, p in remaining if i != chosen_idx]

    return timeline


# ── Round Robin ─────────────────────────────────────────────────────────────


def schedule_round_robin(
    processes: list[SchedulerProcess],
    quantum: int,
) -> list[TimelineEntry]:
    """Round Robin — preemptive with a fixed time quantum.

    Newly arriving processes are added to the back of the ready queue
    *before* the preempted process is re-enqueued.

    Args:
        processes: list of SchedulerProcess.
        quantum:   positive integer time quantum.

    Raises:
        ValueError: if quantum is not a positive integer.
    """
    if quantum <= 0:
        raise ValueError(f"Quantum must be a positive integer, got {quantum}")
    if not processes:
        return []
    _validate_no_duplicate_pids(processes)

    # Build work items: (original_index, pid, arrival_time, remaining_burst).
    work = [
        (i, p.pid, p.arrival_time, p.burst_time)
        for i, p in enumerate(processes)
    ]
    # Sort initially by arrival_time, then original index for determinism.
    work.sort(key=lambda w: (w[2], w[0], w[1]))

    timeline: list[TimelineEntry] = []
    # ready_queue stores (original_index, pid, remaining_burst).
    ready_queue: list[tuple[int, str, int]] = []
    # not_arrived keeps items sorted by arrival_time.
    not_arrived = list(work)  # already sorted
    current_time = 0

    def _enqueue_arrivals(up_to: int) -> None:
        """Move all processes with arrival_time <= up_to into the ready queue."""
        while not_arrived and not_arrived[0][2] <= up_to:
            idx, pid, _at, rem = not_arrived.pop(0)
            ready_queue.append((idx, pid, rem))

    # Seed the queue.
    if not_arrived:
        current_time = not_arrived[0][2]
        _enqueue_arrivals(current_time)

    while ready_queue or not_arrived:
        if not ready_queue:
            # CPU idle — jump to the next arrival.
            current_time = not_arrived[0][2]
            _enqueue_arrivals(current_time)

        idx, pid, remaining = ready_queue.pop(0)
        run_time = min(quantum, remaining)
        start = current_time
        end = start + run_time
        timeline.append(TimelineEntry(pid=pid, start=start, end=end))
        current_time = end

        # Enqueue processes that arrived during this slice.
        _enqueue_arrivals(current_time)

        # Re-enqueue current process if it still has remaining burst.
        new_remaining = remaining - run_time
        if new_remaining > 0:
            ready_queue.append((idx, pid, new_remaining))

    return timeline


# ── Priority Scheduling ────────────────────────────────────────────────────


def schedule_priority(processes: list[SchedulerProcess]) -> list[TimelineEntry]:
    """Priority Scheduling — non-preemptive.

    Lower priority number = higher priority.

    Tie-breaking: priority → arrival_time → input order → pid.

    Raises:
        ValueError: if any process has priority=None.
    """
    if not processes:
        return []
    _validate_no_duplicate_pids(processes)

    for p in processes:
        if p.priority is None:
            raise ValueError(
                f"Priority scheduling requires all processes to have a priority, "
                f"but process {p.pid!r} has priority=None"
            )

    remaining = [(i, p) for i, p in enumerate(processes)]
    timeline: list[TimelineEntry] = []
    current_time = 0

    while remaining:
        ready = [(i, p) for i, p in remaining if p.arrival_time <= current_time]

        if not ready:
            current_time = min(p.arrival_time for _, p in remaining)
            ready = [(i, p) for i, p in remaining if p.arrival_time <= current_time]

        # Pick highest priority (lowest number); tie-break by arrival, index, pid.
        ready.sort(key=lambda ip: (ip[1].priority, ip[1].arrival_time, ip[0], ip[1].pid))
        chosen_idx, chosen_proc = ready[0]

        start = current_time
        end = start + chosen_proc.burst_time
        timeline.append(TimelineEntry(pid=chosen_proc.pid, start=start, end=end))
        current_time = end
        remaining = [(i, p) for i, p in remaining if i != chosen_idx]

    return timeline


# ── Metrics ─────────────────────────────────────────────────────────────────


def calculate_metrics(
    processes: list[SchedulerProcess],
    timeline: list[TimelineEntry],
) -> dict[str, dict[str, float]]:
    """Compute per-process scheduling metrics from a timeline.

    For each process, returns:
        - completion_time:  last time unit when the process finished
        - turnaround_time:  completion_time - arrival_time
        - waiting_time:     turnaround_time - burst_time

    Args:
        processes: the original process list.
        timeline:  the timeline produced by a scheduler.

    Returns:
        dict mapping pid → {completion_time, turnaround_time, waiting_time}.
    """
    if not processes:
        return {}

    # Build a lookup of arrival_time and burst_time by pid.
    _validate_no_duplicate_pids(processes)
    proc_map = {p.pid: p for p in processes}

    # Find the completion time for each process (last timeline entry's end).
    completion: dict[str, int] = {}
    executed_time = dict.fromkeys(proc_map, 0)
    for entry in timeline:
        if entry.pid not in proc_map:
            raise ValueError(f"Timeline contains unknown pid: {entry.pid!r}")
        completion[entry.pid] = entry.end  # last one wins
        executed_time[entry.pid] += entry.duration

    metrics: dict[str, dict[str, float]] = {}
    for pid, proc in proc_map.items():
        if pid not in completion:
            raise ValueError(f"Timeline is missing process {pid!r}")
        if executed_time[pid] != proc.burst_time:
            raise ValueError(
                f"Timeline duration for process {pid!r} must match burst_time "
                f"{proc.burst_time}, got {executed_time[pid]}"
            )
        ct = completion[pid]
        tat = ct - proc.arrival_time
        wt = tat - proc.burst_time
        metrics[pid] = {
            "completion_time": ct,
            "turnaround_time": tat,
            "waiting_time": wt,
        }

    return metrics
