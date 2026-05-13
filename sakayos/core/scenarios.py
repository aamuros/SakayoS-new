"""Pure import/export helpers for CPU scheduling scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sakayos.core.models import SchedulerProcess


SCHEDULING_SCENARIO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["algorithm", "processes"],
    "properties": {
        "title": {"type": "string", "required": False},
        "description": {"type": "string", "required": False},
        "algorithm": {"type": "string", "enum": ["fcfs", "sjf", "priority", "rr"]},
        "quantum": {"type": "integer", "minimum": 1, "required_for": ["rr"]},
        "processes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["pid", "arrival_time", "burst_time"],
                "properties": {
                    "pid": {"type": "string", "minLength": 1},
                    "arrival_time": {"type": "integer", "minimum": 0},
                    "burst_time": {"type": "integer", "minimum": 1},
                    "priority": {"type": "integer", "required_for": ["priority"]},
                },
            },
        },
    },
}

VALID_SCENARIO_ALGORITHMS = frozenset(("fcfs", "sjf", "priority", "rr"))


@dataclass(frozen=True)
class SchedulingScenario:
    """A portable CPU scheduling scenario independent of the Textual screens."""

    algorithm: str
    processes: list[SchedulerProcess]
    quantum: int | None = None
    title: str | None = None
    description: str | None = None


def serialize_scheduling_scenario(scenario: SchedulingScenario) -> str:
    """Serialize a validated scheduling scenario to a deterministic JSON string."""
    validate_scheduling_scenario(scenario)
    payload: dict[str, Any] = {
        "algorithm": scenario.algorithm,
        "processes": [_process_to_payload(process) for process in scenario.processes],
    }
    if scenario.quantum is not None:
        payload["quantum"] = scenario.quantum
    if scenario.title is not None:
        payload["title"] = scenario.title
    if scenario.description is not None:
        payload["description"] = scenario.description

    return json.dumps(payload, indent=2, sort_keys=True)


def parse_scheduling_scenario(raw_json: str) -> SchedulingScenario:
    """Parse and validate a scheduling scenario JSON string."""
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid scenario JSON: {exc.msg}") from exc

    return _scenario_from_payload(payload)


def validate_scheduling_scenario(scenario: SchedulingScenario) -> None:
    """Validate a scheduling scenario's algorithm, quantum, and processes."""
    if not isinstance(scenario, SchedulingScenario):
        raise ValueError("Scenario must be a SchedulingScenario")
    _validate_algorithm(scenario.algorithm)
    _validate_optional_text("title", scenario.title)
    _validate_optional_text("description", scenario.description)
    _validate_quantum(scenario.algorithm, scenario.quantum)
    _validate_processes(scenario.algorithm, scenario.processes)


def _scenario_from_payload(payload: Any) -> SchedulingScenario:
    if not isinstance(payload, dict):
        raise ValueError("Scenario must be a JSON object")

    algorithm = _required(payload, "algorithm")
    _validate_algorithm(algorithm)

    title = payload.get("title")
    description = payload.get("description")
    _validate_optional_text("title", title)
    _validate_optional_text("description", description)

    quantum = payload.get("quantum")
    _validate_quantum(algorithm, quantum)

    raw_processes = _required(payload, "processes")
    if not isinstance(raw_processes, list):
        raise ValueError("processes must be a list")

    processes = [
        _process_from_payload(index, raw_process, require_priority=algorithm == "priority")
        for index, raw_process in enumerate(raw_processes)
    ]
    _validate_processes(algorithm, processes)

    return SchedulingScenario(
        algorithm=algorithm,
        processes=processes,
        quantum=quantum,
        title=title,
        description=description,
    )


def _process_from_payload(
    index: int,
    payload: Any,
    *,
    require_priority: bool,
) -> SchedulerProcess:
    label = f"processes[{index}]"
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")

    pid = _required(payload, "pid", label)
    arrival_time = _required(payload, "arrival_time", label)
    burst_time = _required(payload, "burst_time", label)
    priority = payload.get("priority")

    _validate_pid(pid, label)
    _validate_int(f"{label}.arrival_time", arrival_time)
    _validate_int(f"{label}.burst_time", burst_time)
    if arrival_time < 0:
        raise ValueError(f"{label}.arrival_time must be >= 0")
    if burst_time <= 0:
        raise ValueError(f"{label}.burst_time must be > 0")

    if priority is not None:
        _validate_int(f"{label}.priority", priority)
    if require_priority and priority is None:
        raise ValueError(f"{label}.priority is required for priority scheduling")

    return SchedulerProcess(
        pid=pid,
        arrival_time=arrival_time,
        burst_time=burst_time,
        priority=priority,
    )


def _validate_processes(algorithm: str, processes: list[SchedulerProcess]) -> None:
    if not isinstance(processes, list):
        raise ValueError("processes must be a list")
    if not processes:
        raise ValueError("processes must contain at least one process")

    seen: set[str] = set()
    for index, process in enumerate(processes):
        label = f"processes[{index}]"
        if not isinstance(process, SchedulerProcess):
            raise ValueError(f"{label} must be a SchedulerProcess")
        _validate_pid(process.pid, label)
        _validate_int(f"{label}.arrival_time", process.arrival_time)
        _validate_int(f"{label}.burst_time", process.burst_time)
        if process.arrival_time < 0:
            raise ValueError(f"{label}.arrival_time must be >= 0")
        if process.burst_time <= 0:
            raise ValueError(f"{label}.burst_time must be > 0")
        if process.priority is not None:
            _validate_int(f"{label}.priority", process.priority)
        if algorithm == "priority" and process.priority is None:
            raise ValueError(f"{label}.priority is required for priority scheduling")
        if process.pid in seen:
            raise ValueError(f"Duplicate pid found: {process.pid!r}")
        seen.add(process.pid)


def _process_to_payload(process: SchedulerProcess) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "pid": process.pid,
        "arrival_time": process.arrival_time,
        "burst_time": process.burst_time,
    }
    if process.priority is not None:
        payload["priority"] = process.priority
    return payload


def _required(payload: dict[str, Any], field: str, parent: str = "scenario") -> Any:
    if field not in payload:
        raise ValueError(f"{parent}.{field} is required")
    return payload[field]


def _validate_algorithm(algorithm: Any) -> None:
    if not isinstance(algorithm, str):
        raise ValueError("algorithm must be a string")
    if algorithm not in VALID_SCENARIO_ALGORITHMS:
        valid = ", ".join(sorted(VALID_SCENARIO_ALGORITHMS))
        raise ValueError(f"Invalid algorithm {algorithm!r}; expected one of: {valid}")


def _validate_quantum(algorithm: str, quantum: Any) -> None:
    if algorithm == "rr":
        if quantum is None:
            raise ValueError("quantum is required for Round Robin scheduling")
        _validate_int("quantum", quantum)
        if quantum <= 0:
            raise ValueError("quantum must be > 0")
        return

    if quantum is not None:
        _validate_int("quantum", quantum)
        if quantum <= 0:
            raise ValueError("quantum must be > 0")


def _validate_optional_text(field: str, value: Any) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{field} must be a string")


def _validate_pid(pid: Any, label: str) -> None:
    if not isinstance(pid, str):
        raise ValueError(f"{label}.pid must be a string")
    if not pid.strip():
        raise ValueError(f"{label}.pid cannot be empty")


def _validate_int(field: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
