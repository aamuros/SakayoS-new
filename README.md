# SakayOS

A terminal-based educational Python dashboard that teaches Operating Systems concepts through a Metro Manila commuting analogy.

> **Course Project** — Operating Systems

## What SakayOS Is

SakayOS is an interactive terminal UI built with [Textual](https://textual.textualize.io/). It helps students visualise and experiment with selected OS concepts:

| Module               | OS Concept                  | Analogy                          |
|----------------------|-----------------------------|----------------------------------|
| Passenger Manager    | Process viewer              | Passengers = running processes   |
| Dispatch Scheduler   | CPU scheduling simulation   | Dispatcher = CPU scheduler       |
| Seat Allocator       | Memory allocation simulation| Bus seats = memory blocks        |

SakayOS is not a real operating system. It is a classroom simulator and viewer for learning purposes.

## Simulation Limits

- Dispatch Scheduler does not replace or control the host OS scheduler. It runs textbook FCFS, SJF, Round Robin, and Priority Scheduling on sample input.
- Seat Allocator does not allocate or free real system memory. It demonstrates First Fit, Best Fit, and Worst Fit on a simulated memory layout.
- Passenger Manager reads process information through `psutil`, but it does not kill, pause, resume, or reprioritize processes.
- Process data can vary by operating system and permissions. Some fields may be unavailable on locked-down systems.
- The simulations intentionally simplify real OS behavior so the concepts are easier to inspect in a course-project setting.

## Platform

- **Primary target:** Linux (process data via `psutil`)
- **Development:** macOS is supported for development, but some `psutil` fields may differ.
- **Windows:** Not officially supported.
- **Python:** 3.10 or newer, as declared in `pyproject.toml`.

## Getting Started

### Prerequisites

- Python 3.10+
- `pip`
- `venv` support if you want an isolated environment

### Install Dependencies

Recommended development setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The editable install uses `pyproject.toml` and includes the development tools from the `dev` extra.

For runtime-only installs, the project also keeps `requirements.txt` for the Ubuntu setup script:

```bash
python -m pip install -r requirements.txt
```

### Run the Application

From an editable install:

```bash
sakayos
```

From the project directory:

```bash
chmod +x run.sh
./run.sh
```

Direct module command:

```bash
python -m sakayos.app
```

### Run Tests

Project test script:

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

Direct pytest command:

```bash
python -m pytest tests/ -v
```

### Run Lint

```bash
python -m ruff check sakayos/ tests/
```

`scripts/run_tests.sh` runs pytest first and then runs Ruff if it is installed.

## Current Modules

| Area | Files | Purpose |
|---|---|---|
| App shell | `sakayos/app.py`, `sakayos/app.tcss` | Textual application entry point and styling |
| Core | `sakayos/core/` | Data models, process reading, scheduling algorithms, memory algorithms, scheduling scenario import/export |
| Services | `sakayos/services/` | Thin service layer used by screens to call core logic |
| Screens | `sakayos/screens/` | Textual screens for home, Passenger Manager, Dispatch Scheduler, and Seat Allocator |
| UI helpers | `sakayos/ui/` | Rendering and parsing helpers for Gantt charts, memory views, and form inputs |
| Tests | `tests/` | Unit, rendering, parsing, and smoke tests |

## Project Structure

```
sakayos/
  __init__.py
  app.py                    # Main Textual application entry point
  app.tcss                  # Textual CSS stylesheet
  core/
    __init__.py
    models.py               # Data models (SchedulerProcess, MemoryBlock, ProcessInfo)
    scheduling.py           # CPU scheduling algorithms (FCFS, SJF, RR, Priority)
    memory.py               # Memory allocation (First/Best/Worst Fit)
    process_reader.py       # psutil-based process reader
    scenarios.py            # Scheduling scenario JSON import/export helpers
  services/
    __init__.py
    scheduling_service.py   # Service wrapper for scheduling operations
    memory_service.py       # Service wrapper for memory allocation operations
  ui/
    __init__.py
    gantt.py                # Gantt chart and metrics table rendering
    memory_view.py          # Memory bar, block table, fragmentation rendering
    parsing.py              # Input parsing helpers (process lines, quantum, memory)
  screens/
    __init__.py             # Screen re-exports
    home.py                 # Home screen with navigation and glossary
    passenger.py            # Passenger Manager — live process viewer
    dispatch.py             # Dispatch Scheduler — CPU scheduling simulation
    seat_allocator.py       # Seat Allocator — memory allocation simulation
scripts/
  setup_ubuntu.sh           # Ubuntu setup: venv + deps (no sudo)
  run_tests.sh              # Runs pytest + ruff
docs/
  DEPLOYMENT.md             # Ubuntu bootable USB deployment guide
  DEVELOPER_GUIDE.md        # Short guide for extending the project
  SCHEDULING_SCENARIOS.md   # Scheduling scenario JSON format
tests/
  __init__.py
  test_smoke.py             # Smoke test — verifies package imports
  test_models.py            # Data model validation tests
  test_scheduling.py        # Scheduling algorithm tests
  test_memory.py            # Memory allocator tests
  test_process_reader.py    # Process reader tests
  test_app.py               # Textual app skeleton tests
  test_dispatch_parsing.py  # Input parsing helper tests
  test_gantt.py             # Gantt chart rendering tests
  test_memory_parsing.py    # Memory input parsing tests
  test_memory_view.py       # Memory visualization tests
  test_passenger_view.py    # Process table rendering tests
```

## Developer Guide

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) for the short contributor guide.

In brief:

- Put OS concept logic in `sakayos/core/`.
- Keep Textual widgets and screen behavior in `sakayos/screens/`.
- Put reusable rendering and parsing helpers in `sakayos/ui/`.
- Use `sakayos/services/` when a screen needs a small adapter around core logic.
- Add tests in `tests/` beside the behavior being changed.

## Dependencies

| Package   | Purpose                             |
|-----------|-------------------------------------|
| `textual` | Terminal UI framework               |
| `rich`    | Rich text rendering (used by Textual) |
| `psutil`  | System process information          |
| `pytest`  | Testing (dev extra)                 |
| `ruff`    | Linting (dev extra)                 |

## Current Status

> **All modules implemented and tested.**
>
> - **Passenger Manager** — live process viewer using `psutil` (read-only).
> - **Dispatch Scheduler** — CPU scheduling simulation (FCFS, SJF, RR, Priority) with Gantt charts and metrics.
> - **Seat Allocator** — memory allocation simulation (First/Best/Worst Fit) with fragmentation visualization.
> - Metro Manila commuting analogy labels are applied throughout the UI.
> - Ubuntu bootable USB deployment guide available at `docs/DEPLOYMENT.md`.
> - Run with `sakayos`, `./run.sh`, or `python -m sakayos.app`.
