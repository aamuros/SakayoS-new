"""Scheduling workflows shared by UI screens and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sakayos.core.models import SchedulerProcess, TimelineEntry
from sakayos.core.scheduling import (
    calculate_metrics,
    schedule_fcfs,
    schedule_priority,
    schedule_round_robin,
    schedule_sjf,
)
from sakayos.ui.parsing import parse_process_block, parse_quantum


SchedulingMetrics = dict[str, dict[str, float]]
SchedulerFn = Callable[[list[SchedulerProcess]], list[TimelineEntry]]


@dataclass(frozen=True)
class SchedulingSimulationResult:
    """Complete output from one scheduling simulation run."""

    algorithm: str
    processes: list[SchedulerProcess]
    timeline: list[TimelineEntry]
    metrics: SchedulingMetrics
    quantum: int | None = None


_SCHEDULERS: dict[str, SchedulerFn] = {
    "fcfs": schedule_fcfs,
    "sjf": schedule_sjf,
    "priority": schedule_priority,
}


def run_scheduling_simulation(
    algo: str,
    raw_process_text: str,
    quantum_text: str | None = None,
) -> SchedulingSimulationResult:
    """Parse input, run the selected scheduler, and calculate metrics."""
    _validate_algorithm(algo)

    require_priority = algo == "priority"
    processes = parse_process_block(
        raw_process_text,
        require_priority=require_priority,
    )
    quantum = _parse_quantum_for_algorithm(algo, quantum_text)

    try:
        timeline = _run_scheduler(algo, processes, quantum)
    except ValueError as exc:
        raise ValueError(f"Scheduling error: {exc}") from exc

    metrics = calculate_metrics(processes, timeline)
    return SchedulingSimulationResult(
        algorithm=algo,
        processes=processes,
        timeline=timeline,
        metrics=metrics,
        quantum=quantum,
    )


def _validate_algorithm(algo: str) -> None:
    valid_algorithms = (*_SCHEDULERS.keys(), "rr")
    if algo not in valid_algorithms:
        raise ValueError(f"Unknown algorithm: {algo!r}")


def _parse_quantum_for_algorithm(
    algo: str,
    quantum_text: str | None,
) -> int | None:
    if algo != "rr":
        return None
    return parse_quantum(quantum_text or "")


def _run_scheduler(
    algo: str,
    processes: list[SchedulerProcess],
    quantum: int | None,
) -> list[TimelineEntry]:
    if algo == "rr":
        assert quantum is not None
        return schedule_round_robin(processes, quantum=quantum)
    return _SCHEDULERS[algo](processes)
