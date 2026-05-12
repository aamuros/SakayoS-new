# SakayOS 🚌

A terminal-based educational Python dashboard that teaches Operating Systems concepts — process management, CPU scheduling, and memory allocation — through a Metro Manila commuting analogy.

> **Course Project** — Operating Systems

## What SakayOS Is

SakayOS is an interactive terminal UI (built with [Textual](https://textual.textualize.io/)) that helps students visualise and experiment with core OS concepts:

| Module               | OS Concept                  | Analogy                          |
|----------------------|-----------------------------|----------------------------------|
| Passenger Manager    | Process viewer              | Passengers = running processes   |
| Dispatch Scheduler   | CPU scheduling simulation   | Dispatcher = CPU scheduler       |
| Seat Allocator       | Memory allocation simulation| Bus seats = memory blocks        |

## What SakayOS Does **Not** Do

- **Does not replace the real OS scheduler.** Dispatch Scheduler runs textbook algorithms (FCFS, SJF, Round Robin, Priority) on user-provided input — it is a *simulation only*.
- **Does not control real system memory.** Seat Allocator demonstrates First Fit / Best Fit / Worst Fit on a simulated memory layout.
- **Does not require root/admin privileges.** Process reading uses `psutil` with graceful fallback for restricted fields.

## Platform

- **Primary target:** Linux (process data via `psutil`)
- **Development:** macOS is supported for development, but some `psutil` fields may differ.
- **Windows:** Not officially supported.

## Getting Started

### Prerequisites

- Python 3.10+

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
chmod +x run.sh
./run.sh

# Or directly:
python -m sakayos.app
```

### Run Tests

```bash
python -m pytest tests/ -v
```

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


## Dependencies

| Package   | Purpose                             |
|-----------|-------------------------------------|
| `textual` | Terminal UI framework               |
| `rich`    | Rich text rendering (used by Textual) |
| `psutil`  | System process information          |
| `pytest`  | Testing                             |
| `ruff`    | Linting (dev)                       |

## Current Status

> **All modules implemented and tested.**
>
> - **Passenger Manager** — live process viewer using `psutil` (read-only).
> - **Dispatch Scheduler** — CPU scheduling simulation (FCFS, SJF, RR, Priority) with Gantt charts and metrics.
> - **Seat Allocator** — memory allocation simulation (First/Best/Worst Fit) with fragmentation visualization.
> - Metro Manila commuting analogy labels are applied throughout the UI.
> - Ubuntu bootable USB deployment guide available at `docs/DEPLOYMENT.md`.
> - Run with `./run.sh` or `python -m sakayos.app`.
