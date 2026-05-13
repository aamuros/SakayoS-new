"""Tests for pure scheduling scenario import/export helpers."""

from __future__ import annotations

import json

import pytest

from sakayos.core.models import SchedulerProcess
from sakayos.core.scenarios import (
    SCHEDULING_SCENARIO_SCHEMA,
    SchedulingScenario,
    parse_scheduling_scenario,
    serialize_scheduling_scenario,
    validate_scheduling_scenario,
)


class TestSchedulingScenarioSchema:
    def test_schema_documents_expected_top_level_fields(self) -> None:
        assert SCHEDULING_SCENARIO_SCHEMA["required"] == ["algorithm", "processes"]
        assert SCHEDULING_SCENARIO_SCHEMA["properties"]["algorithm"]["enum"] == [
            "fcfs",
            "sjf",
            "priority",
            "rr",
        ]
        assert SCHEDULING_SCENARIO_SCHEMA["properties"]["quantum"]["required_for"] == ["rr"]


class TestSchedulingScenarioSerialization:
    @pytest.mark.parametrize("algorithm", ["fcfs", "sjf"])
    def test_serializes_and_parses_non_priority_scenarios(self, algorithm: str) -> None:
        scenario = SchedulingScenario(
            algorithm=algorithm,
            title=f"{algorithm.upper()} demo",
            description="Two-process classroom example.",
            processes=[
                SchedulerProcess(pid="P1", arrival_time=0, burst_time=4),
                SchedulerProcess(pid="P2", arrival_time=2, burst_time=3),
            ],
        )

        raw_json = serialize_scheduling_scenario(scenario)
        parsed = parse_scheduling_scenario(raw_json)

        assert parsed == scenario
        assert json.loads(raw_json)["algorithm"] == algorithm

    def test_serializes_and_parses_priority_scenario(self) -> None:
        scenario = SchedulingScenario(
            algorithm="priority",
            processes=[
                SchedulerProcess(pid="P1", arrival_time=0, burst_time=5, priority=2),
                SchedulerProcess(pid="P2", arrival_time=1, burst_time=2, priority=1),
            ],
        )

        parsed = parse_scheduling_scenario(serialize_scheduling_scenario(scenario))

        assert parsed == scenario
        assert [process.priority for process in parsed.processes] == [2, 1]

    def test_serializes_and_parses_round_robin_scenario_with_quantum(self) -> None:
        scenario = SchedulingScenario(
            algorithm="rr",
            quantum=2,
            processes=[
                SchedulerProcess(pid="P1", arrival_time=0, burst_time=5),
                SchedulerProcess(pid="P2", arrival_time=1, burst_time=3),
            ],
        )

        parsed = parse_scheduling_scenario(serialize_scheduling_scenario(scenario))

        assert parsed.algorithm == "rr"
        assert parsed.quantum == 2
        assert parsed.processes == scenario.processes


class TestSchedulingScenarioValidation:
    def test_missing_algorithm_raises(self) -> None:
        with pytest.raises(ValueError, match="scenario.algorithm is required"):
            parse_scheduling_scenario(
                json.dumps(
                    {
                        "processes": [
                            {"pid": "P1", "arrival_time": 0, "burst_time": 4},
                        ],
                    }
                )
            )

    def test_missing_processes_raises(self) -> None:
        with pytest.raises(ValueError, match="scenario.processes is required"):
            parse_scheduling_scenario(json.dumps({"algorithm": "fcfs"}))

    def test_round_robin_missing_quantum_raises(self) -> None:
        with pytest.raises(ValueError, match="quantum is required"):
            parse_scheduling_scenario(
                json.dumps(
                    {
                        "algorithm": "rr",
                        "processes": [
                            {"pid": "P1", "arrival_time": 0, "burst_time": 4},
                        ],
                    }
                )
            )

    def test_invalid_algorithm_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid algorithm"):
            parse_scheduling_scenario(
                json.dumps(
                    {
                        "algorithm": "lottery",
                        "processes": [
                            {"pid": "P1", "arrival_time": 0, "burst_time": 4},
                        ],
                    }
                )
            )

    @pytest.mark.parametrize(
        ("process_payload", "message"),
        [
            ({"pid": "", "arrival_time": 0, "burst_time": 4}, "pid cannot be empty"),
            ({"pid": "P1", "arrival_time": -1, "burst_time": 4}, "arrival_time must be >= 0"),
            ({"pid": "P1", "arrival_time": 0, "burst_time": 0}, "burst_time must be > 0"),
            ({"pid": "P1", "arrival_time": "0", "burst_time": 4}, "arrival_time must be an integer"),
        ],
    )
    def test_invalid_process_values_raise(
        self,
        process_payload: dict[str, object],
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=message):
            parse_scheduling_scenario(
                json.dumps(
                    {
                        "algorithm": "fcfs",
                        "processes": [process_payload],
                    }
                )
            )

    def test_priority_requires_process_priority_values(self) -> None:
        with pytest.raises(ValueError, match="priority is required"):
            parse_scheduling_scenario(
                json.dumps(
                    {
                        "algorithm": "priority",
                        "processes": [
                            {"pid": "P1", "arrival_time": 0, "burst_time": 4},
                        ],
                    }
                )
            )

    def test_validate_scheduling_scenario_checks_duplicate_pids(self) -> None:
        with pytest.raises(ValueError, match="Duplicate pid"):
            validate_scheduling_scenario(
                SchedulingScenario(
                    algorithm="fcfs",
                    processes=[
                        SchedulerProcess(pid="P1", arrival_time=0, burst_time=4),
                        SchedulerProcess(pid="P1", arrival_time=1, burst_time=2),
                    ],
                )
            )
