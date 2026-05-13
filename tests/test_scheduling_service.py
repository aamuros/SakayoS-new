"""Tests for scheduling service workflows independent of Textual."""

from __future__ import annotations

import pytest

from sakayos.services.scheduling_service import (
    SchedulingSimulationResult,
    run_scheduling_simulation,
)


class TestRunSchedulingSimulation:
    def test_fcfs_returns_structured_result(self) -> None:
        result = run_scheduling_simulation(
            "fcfs",
            "P1, 0, 4\nP2, 2, 3",
        )

        assert isinstance(result, SchedulingSimulationResult)
        assert result.algorithm == "fcfs"
        assert result.quantum is None
        assert [proc.pid for proc in result.processes] == ["P1", "P2"]
        assert [(entry.pid, entry.start, entry.end) for entry in result.timeline] == [
            ("P1", 0, 4),
            ("P2", 4, 7),
        ]
        assert result.metrics["P2"]["waiting_time"] == 2

    def test_round_robin_parses_quantum_and_metrics(self) -> None:
        result = run_scheduling_simulation(
            "rr",
            "P1, 0, 5\nP2, 1, 3\nP3, 2, 1",
            quantum_text="2",
        )

        assert result.quantum == 2
        assert [(entry.pid, entry.start, entry.end) for entry in result.timeline] == [
            ("P1", 0, 2),
            ("P2", 2, 4),
            ("P3", 4, 5),
            ("P1", 5, 7),
            ("P2", 7, 8),
            ("P1", 8, 9),
        ]
        assert result.metrics["P1"]["completion_time"] == 9

    def test_priority_requires_priority_values(self) -> None:
        with pytest.raises(ValueError, match="4 fields"):
            run_scheduling_simulation("priority", "P1, 0, 4")

    def test_unknown_algorithm_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown algorithm"):
            run_scheduling_simulation("bogus", "P1, 0, 4")

    def test_round_robin_requires_quantum(self) -> None:
        with pytest.raises(ValueError, match="Quantum cannot be empty"):
            run_scheduling_simulation("rr", "P1, 0, 4")

    def test_scheduler_errors_keep_screen_compatible_prefix(self) -> None:
        with pytest.raises(ValueError, match="Scheduling error: Duplicate pid"):
            run_scheduling_simulation("fcfs", "P1, 0, 4\nP1, 1, 3")
