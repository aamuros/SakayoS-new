# Scheduling Scenario JSON

Scheduling scenarios can be imported and exported as JSON without depending on
the Textual UI.

Required top-level fields:

- `algorithm`: one of `fcfs`, `sjf`, `priority`, or `rr`
- `processes`: list of process objects

Optional top-level fields:

- `title`: short scenario name
- `description`: longer notes
- `quantum`: positive integer, required when `algorithm` is `rr`

Each process requires:

- `pid`: non-empty string
- `arrival_time`: integer `>= 0`
- `burst_time`: integer `> 0`
- `priority`: integer, required when `algorithm` is `priority`

Example:

```json
{
  "title": "Round Robin demo",
  "description": "Three-process classroom example.",
  "algorithm": "rr",
  "quantum": 2,
  "processes": [
    {"pid": "P1", "arrival_time": 0, "burst_time": 5},
    {"pid": "P2", "arrival_time": 1, "burst_time": 3},
    {"pid": "P3", "arrival_time": 2, "burst_time": 1}
  ]
}
```
