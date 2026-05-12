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
  app.py                    # Main application entry point
  core/
    __init__.py
    models.py               # Data models (placeholder)
    scheduling.py           # CPU scheduling algorithms (placeholder)
    memory.py               # Memory allocation algorithms (placeholder)
    process_reader.py       # psutil-based process reader (placeholder)
  ui/
    __init__.py             # UI widgets (placeholder)
  screens/
    __init__.py             # Textual screens (placeholder)
tests/
  __init__.py
  test_smoke.py             # Smoke test — verifies package imports
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

> **Phase 1 — Repository skeleton and test harness only.**
>
> No algorithms, no Textual screens, no psutil reading implemented yet.
> Only the package structure and a smoke test exist.
