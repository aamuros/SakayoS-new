# SakayOS Developer Guide

This guide is for students working on SakayOS as an Operating Systems course project. SakayOS is a terminal-based simulator and process viewer, not a real operating system.

## Project Layout

```text
sakayos/
  app.py              # Textual app entry point
  app.tcss            # Textual stylesheet
  core/               # OS concept logic and data models
  services/           # Small adapters between screens and core logic
  screens/            # Textual screens and user workflows
  ui/                 # Reusable rendering and parsing helpers
tests/                # Unit, parsing, rendering, and smoke tests
scripts/              # Setup, launch, and test helper scripts
docs/                 # Project documentation
```

## Core vs UI vs Screens vs Services

`sakayos/core/` should hold the course concept implementation. Scheduling algorithms, memory allocation algorithms, process data models, and scenario parsing belong here. Core code should be easy to test without launching the Textual app.

`sakayos/screens/` should hold screen-level behavior. These files define what the user sees and how input events flow through the Passenger Manager, Dispatch Scheduler, Seat Allocator, and Home screens.

`sakayos/ui/` should hold reusable helpers for presentation and input handling. Gantt chart rendering, memory view rendering, and text input parsing live here so screens stay smaller.

`sakayos/services/` should hold thin coordination code between screens and core modules. Use services when a screen needs a clean interface to call core behavior or prepare display-ready results.

## Adding New OS Concepts

Add the concept logic to `sakayos/core/` first. Keep it independent from Textual where possible so it can be tested with plain unit tests.

Add a service in `sakayos/services/` if the screen needs an adapter around the core logic.

Add UI rendering or parsing helpers in `sakayos/ui/` if the concept needs repeated display formatting or structured input parsing.

Add or update a screen in `sakayos/screens/` when the concept needs an interactive workflow.

Add tests in `tests/` for the core behavior and any parsing/rendering helpers. If the concept has a screen, include a smoke or interaction-oriented test where practical.

## Current Commands

Install for development:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the app:

```bash
sakayos
```

Alternative app commands:

```bash
./run.sh
python -m sakayos.app
```

Run tests:

```bash
python -m pytest tests/ -v
```

Run lint:

```bash
python -m ruff check sakayos/ tests/
```

Run both through the helper script:

```bash
./scripts/run_tests.sh
```

## Supported Python Versions

SakayOS supports Python 3.10 or newer. The project metadata in `pyproject.toml` declares `requires-python = ">=3.10"`, and Ruff is configured with `target-version = "py310"`.

## Simulation Boundaries

Keep documentation and UI text clear that SakayOS demonstrates OS concepts but does not replace host OS behavior. New features should avoid claiming that the app controls real CPU scheduling, memory allocation, or process execution unless that behavior is actually implemented and safe.
