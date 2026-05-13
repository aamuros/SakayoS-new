"""Tests for sakayos.core.scheduling — written BEFORE implementation (TDD).

Covers:
- First Come First Serve (FCFS)
- Shortest Job First (SJF)
- Round Robin (RR)
- Priority Scheduling
- calculate_metrics
- Input validation and edge cases
"""

import pytest

from sakayos.core.models import SchedulerProcess, TimelineEntry
from sakayos.core.scheduling import (
    calculate_metrics,
    schedule_fcfs,
    schedule_priority,
    schedule_round_robin,
    schedule_sjf,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _pids(timeline: list[TimelineEntry]) -> list[str]:
    """Extract the sequence of pids from a timeline."""
    return [entry.pid for entry in timeline]


def _spans(timeline: list[TimelineEntry]) -> list[tuple[str, int, int]]:
    """Extract (pid, start, end) tuples from a timeline."""
    return [(e.pid, e.start, e.end) for e in timeline]


# ── Empty & validation ──────────────────────────────────────────────────────


class TestValidation:
    """Input validation common to all schedulers."""

    def test_empty_process_list_returns_empty_timeline_fcfs(self):
        assert schedule_fcfs([]) == []

    def test_empty_process_list_returns_empty_timeline_sjf(self):
        assert schedule_sjf([]) == []

    def test_empty_process_list_returns_empty_timeline_rr(self):
        assert schedule_round_robin([], quantum=2) == []

    def test_empty_process_list_returns_empty_timeline_priority(self):
        assert schedule_priority([]) == []

    def test_duplicate_pid_raises_fcfs(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3),
            SchedulerProcess(pid="P1", arrival_time=1, burst_time=2),
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            schedule_fcfs(procs)

    def test_duplicate_pid_raises_sjf(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3),
            SchedulerProcess(pid="P1", arrival_time=1, burst_time=2),
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            schedule_sjf(procs)

    def test_duplicate_pid_raises_rr(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3),
            SchedulerProcess(pid="P1", arrival_time=1, burst_time=2),
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            schedule_round_robin(procs, quantum=2)

    def test_duplicate_pid_raises_priority(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3, priority=1),
            SchedulerProcess(pid="P1", arrival_time=1, burst_time=2, priority=2),
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            schedule_priority(procs)


# ── FCFS ────────────────────────────────────────────────────────────────────


class TestFCFS:
    """First Come First Serve scheduling tests."""

    def test_staggered_arrivals(self):
        """Processes arriving at different times are served in arrival order."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=4),
            SchedulerProcess(pid="P2", arrival_time=2, burst_time=3),
            SchedulerProcess(pid="P3", arrival_time=5, burst_time=2),
        ]
        timeline = schedule_fcfs(procs)
        assert _spans(timeline) == [
            ("P1", 0, 4),
            ("P2", 4, 7),
            ("P3", 7, 9),
        ]

    def test_idle_time_before_first_process(self):
        """CPU is idle until the first process arrives (arrival_time > 0)."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=3, burst_time=2),
            SchedulerProcess(pid="P2", arrival_time=5, burst_time=1),
        ]
        timeline = schedule_fcfs(procs)
        # First entry should start at 3, not 0 — CPU jumps to first arrival.
        assert _spans(timeline) == [
            ("P1", 3, 5),
            ("P2", 5, 6),
        ]

    def test_idle_gap_between_processes(self):
        """CPU idles between processes when there is a gap in arrivals."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=2),
            SchedulerProcess(pid="P2", arrival_time=5, burst_time=3),
        ]
        timeline = schedule_fcfs(procs)
        assert _spans(timeline) == [
            ("P1", 0, 2),
            ("P2", 5, 8),
        ]

    def test_single_process(self):
        procs = [SchedulerProcess(pid="P1", arrival_time=0, burst_time=5)]
        timeline = schedule_fcfs(procs)
        assert _spans(timeline) == [("P1", 0, 5)]


# ── SJF ─────────────────────────────────────────────────────────────────────


class TestSJF:
    """Shortest Job First (non-preemptive) scheduling tests."""

    def test_chooses_shortest_available_job(self):
        """SJF picks the shortest burst among *arrived* processes only."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=6),
            SchedulerProcess(pid="P2", arrival_time=1, burst_time=2),
            SchedulerProcess(pid="P3", arrival_time=2, burst_time=4),
        ]
        timeline = schedule_sjf(procs)
        # P1 runs first (only one at t=0). At t=6, P2 and P3 are available.
        # P2 has shorter burst → P2 next, then P3.
        assert _spans(timeline) == [
            ("P1", 0, 6),
            ("P2", 6, 8),
            ("P3", 8, 12),
        ]

    def test_tie_breaking_is_deterministic(self):
        """When burst times are equal, earlier arrival wins; then input order."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3),
            SchedulerProcess(pid="P2", arrival_time=0, burst_time=3),
            SchedulerProcess(pid="P3", arrival_time=0, burst_time=3),
        ]
        timeline = schedule_sjf(procs)
        # All arrive at 0 with equal burst → input order wins.
        assert _pids(timeline) == ["P1", "P2", "P3"]

    def test_future_short_job_not_chosen_over_arrived(self):
        """A short job arriving in the future doesn't preempt a longer arrived job."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=5),
            SchedulerProcess(pid="P2", arrival_time=10, burst_time=1),
        ]
        timeline = schedule_sjf(procs)
        assert _spans(timeline) == [
            ("P1", 0, 5),
            ("P2", 10, 11),
        ]


# ── Round Robin ─────────────────────────────────────────────────────────────


class TestRoundRobin:
    """Round Robin (preemptive, time-quantum) scheduling tests."""

    def test_quantum_zero_raises(self):
        with pytest.raises(ValueError, match="[Qq]uantum"):
            schedule_round_robin([], quantum=0)

    def test_negative_quantum_raises(self):
        with pytest.raises(ValueError, match="[Qq]uantum"):
            schedule_round_robin([], quantum=-3)

    def test_staggered_arrivals_quantum_2(self):
        """Classic RR example with quantum=2 and staggered arrivals."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=5),
            SchedulerProcess(pid="P2", arrival_time=1, burst_time=3),
            SchedulerProcess(pid="P3", arrival_time=2, burst_time=1),
        ]
        timeline = schedule_round_robin(procs, quantum=2)
        # t=0-2: P1 runs (remaining 3). Queue: [P2, P3, P1]
        # t=2-4: P2 runs (remaining 1). Queue: [P3, P1, P2]
        # t=4-5: P3 runs (done).         Queue: [P1, P2]
        # t=5-7: P1 runs (remaining 1). Queue: [P2, P1]
        # t=7-8: P2 runs (done).         Queue: [P1]
        # t=8-9: P1 runs (done).
        assert _spans(timeline) == [
            ("P1", 0, 2),
            ("P2", 2, 4),
            ("P3", 4, 5),
            ("P1", 5, 7),
            ("P2", 7, 8),
            ("P1", 8, 9),
        ]

    def test_single_process_quantum_larger_than_burst(self):
        """When quantum exceeds burst, process finishes in one slice."""
        procs = [SchedulerProcess(pid="P1", arrival_time=0, burst_time=3)]
        timeline = schedule_round_robin(procs, quantum=10)
        assert _spans(timeline) == [("P1", 0, 3)]

    def test_idle_jump_in_round_robin(self):
        """CPU jumps to next arrival when queue is empty."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=1),
            SchedulerProcess(pid="P2", arrival_time=5, burst_time=2),
        ]
        timeline = schedule_round_robin(procs, quantum=3)
        assert _spans(timeline) == [
            ("P1", 0, 1),
            ("P2", 5, 7),
        ]


# ── Priority Scheduling ────────────────────────────────────────────────────


class TestPriorityScheduling:
    """Priority Scheduling (non-preemptive) tests."""

    def test_missing_priority_raises(self):
        """All processes must have a priority value."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=3),  # priority=None
        ]
        with pytest.raises(ValueError, match="[Pp]riority"):
            schedule_priority(procs)

    def test_chooses_lowest_priority_number(self):
        """Lower priority number = higher priority."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=4, priority=3),
            SchedulerProcess(pid="P2", arrival_time=0, burst_time=2, priority=1),
            SchedulerProcess(pid="P3", arrival_time=0, burst_time=3, priority=2),
        ]
        timeline = schedule_priority(procs)
        assert _pids(timeline) == ["P2", "P3", "P1"]

    def test_priority_with_staggered_arrivals(self):
        """Priority selection only considers arrived processes."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=5, priority=3),
            SchedulerProcess(pid="P2", arrival_time=1, burst_time=2, priority=1),
            SchedulerProcess(pid="P3", arrival_time=2, burst_time=3, priority=2),
        ]
        timeline = schedule_priority(procs)
        # P1 starts at 0 (only one available). Finishes at 5.
        # At t=5, P2(pri=1) and P3(pri=2) are available → P2 first, then P3.
        assert _spans(timeline) == [
            ("P1", 0, 5),
            ("P2", 5, 7),
            ("P3", 7, 10),
        ]

    def test_priority_tie_breaking(self):
        """Equal priorities use arrival_time, then input order."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=2, priority=1),
            SchedulerProcess(pid="P2", arrival_time=0, burst_time=3, priority=1),
            SchedulerProcess(pid="P3", arrival_time=0, burst_time=1, priority=1),
        ]
        timeline = schedule_priority(procs)
        # All same arrival and priority → input order.
        assert _pids(timeline) == ["P1", "P2", "P3"]


# ── calculate_metrics ──────────────────────────────────────────────────────


class TestCalculateMetrics:
    """Tests for the calculate_metrics helper."""

    def test_basic_metrics(self):
        """Verify completion, turnaround, and waiting times."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=4),
            SchedulerProcess(pid="P2", arrival_time=1, burst_time=3),
        ]
        timeline = [
            TimelineEntry(pid="P1", start=0, end=4),
            TimelineEntry(pid="P2", start=4, end=7),
        ]
        metrics = calculate_metrics(procs, timeline)

        assert metrics["P1"]["completion_time"] == 4
        assert metrics["P1"]["turnaround_time"] == 4   # 4 - 0
        assert metrics["P1"]["waiting_time"] == 0       # 4 - 4

        assert metrics["P2"]["completion_time"] == 7
        assert metrics["P2"]["turnaround_time"] == 6    # 7 - 1
        assert metrics["P2"]["waiting_time"] == 3       # 6 - 3

    def test_metrics_with_preempted_process(self):
        """Metrics work correctly when a process has multiple timeline entries."""
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=4),
            SchedulerProcess(pid="P2", arrival_time=1, burst_time=2),
        ]
        # Simulating a scenario where P1 is split across two entries.
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=2, end=4),
            TimelineEntry(pid="P1", start=4, end=6),
        ]
        metrics = calculate_metrics(procs, timeline)

        assert metrics["P1"]["completion_time"] == 6
        assert metrics["P1"]["turnaround_time"] == 6    # 6 - 0
        assert metrics["P1"]["waiting_time"] == 2        # 6 - 4

        assert metrics["P2"]["completion_time"] == 4
        assert metrics["P2"]["turnaround_time"] == 3     # 4 - 1
        assert metrics["P2"]["waiting_time"] == 1        # 3 - 2

    def test_empty_inputs(self):
        assert calculate_metrics([], []) == {}

    def test_duplicate_process_pid_raises(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=2),
            SchedulerProcess(pid="P1", arrival_time=1, burst_time=3),
        ]
        timeline = [TimelineEntry(pid="P1", start=0, end=2)]

        with pytest.raises(ValueError, match="[Dd]uplicate"):
            calculate_metrics(procs, timeline)

    def test_timeline_with_unknown_pid_raises(self):
        procs = [SchedulerProcess(pid="P1", arrival_time=0, burst_time=2)]
        timeline = [
            TimelineEntry(pid="P1", start=0, end=2),
            TimelineEntry(pid="P2", start=2, end=4),
        ]

        with pytest.raises(ValueError, match="unknown pid"):
            calculate_metrics(procs, timeline)

    def test_missing_timeline_entry_raises(self):
        procs = [
            SchedulerProcess(pid="P1", arrival_time=0, burst_time=2),
            SchedulerProcess(pid="P2", arrival_time=0, burst_time=3),
        ]
        timeline = [TimelineEntry(pid="P1", start=0, end=2)]

        with pytest.raises(ValueError, match="missing"):
            calculate_metrics(procs, timeline)

    def test_execution_duration_must_match_burst_time(self):
        procs = [SchedulerProcess(pid="P1", arrival_time=0, burst_time=3)]
        timeline = [TimelineEntry(pid="P1", start=0, end=2)]

        with pytest.raises(ValueError, match="burst_time"):
            calculate_metrics(procs, timeline)
