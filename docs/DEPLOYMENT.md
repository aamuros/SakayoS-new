# SakayOS — Deployment Guide (Ubuntu Bootable USB)

This document covers running SakayOS on an **Ubuntu Desktop bootable USB** — the kind you create with Rufus or balenaEtcher for classroom demos.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **OS** | Ubuntu 22.04 LTS or newer (Desktop live USB or installed) |
| **Python** | 3.10 or newer (ships with Ubuntu 22.04+) |
| **Terminal** | Any — GNOME Terminal, Konsole, xterm, etc. |
| **No sudo required** | The setup script does not install system packages |

### If Python is missing (unlikely on Ubuntu Desktop)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

> **Note:** Ubuntu Desktop 22.04+ includes Python 3.10 by default. You should only need the command above on minimal/server installs.

---

## Quick Start (3 commands)

```bash
# 1. Clone or copy the project to the USB filesystem
cd /path/to/SakayoS-new

# 2. Run the automated setup
chmod +x scripts/setup_ubuntu.sh
./scripts/setup_ubuntu.sh

# 3. Launch the app
./run.sh
```

That's it. The setup script creates a virtual environment, installs dependencies, and verifies the app can import.

---

## Step-by-Step Walkthrough

### 1. Get the project onto the USB

**Option A — Git clone** (if the USB has internet):
```bash
git clone <repository-url> ~/SakayoS-new
cd ~/SakayoS-new
```

**Option B — Copy from a flash drive:**
```bash
cp -r /media/ubuntu/USBDRIVE/SakayoS-new ~/SakayoS-new
cd ~/SakayoS-new
```

### 2. Run the setup script

```bash
chmod +x scripts/setup_ubuntu.sh
./scripts/setup_ubuntu.sh
```

This will:
1. Check that Python 3.10+ is available.
2. Create a `.venv` virtual environment inside the project.
3. Install all packages from `requirements.txt` into the venv.
4. Verify that `sakayos.app` can be imported.

### 3. Launch SakayOS

```bash
./run.sh
```

Or directly:
```bash
.venv/bin/python -m sakayos.app
```

The terminal UI will launch. Use the arrow keys, Enter, and Tab to navigate.

### 4. Run tests (optional)

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

This runs `pytest` and `ruff` (if installed) against the full test suite.

---

## Project Scripts

| Script | Purpose |
|---|---|
| `run.sh` | Launch SakayOS (auto-detects `.venv`) |
| `scripts/setup_ubuntu.sh` | One-time setup: venv + deps + verify |
| `scripts/run_tests.sh` | Run pytest + ruff |

---

## Troubleshooting

### `python3: command not found`

```bash
sudo apt update && sudo apt install python3 python3-venv python3-pip
```

### `No module named venv` / `ensurepip is not available`

```bash
sudo apt install python3-venv
```

### Terminal UI looks broken / no colors

Make sure you are using a modern terminal emulator (GNOME Terminal, Konsole, or Alacritty). Textual requires a terminal with 256-color or truecolor support.

If colors are still wrong:
```bash
export TERM=xterm-256color
./run.sh
```

### `psutil` shows no processes

On some locked-down systems, `psutil` may not be able to read process info. The Passenger Manager will display a clear message. The other two modules (Dispatch Scheduler and Seat Allocator) are simulations and work without real process data.

### Bootable USB has no persistent storage

If you are running Ubuntu from a live USB without persistence, the `.venv` will be lost on reboot. Re-run `./scripts/setup_ubuntu.sh` after each boot. This takes ~10 seconds with a cached pip.

---

## What This Does **Not** Do

- Does **not** create ISO images or modify bootloaders.
- Does **not** require `sudo` for normal operation.
- Does **not** modify system packages or global pip.
- Does **not** write outside the project directory.
- Does **not** kill, pause, or modify any real processes.

---

## Dependencies

| Package | Purpose |
|---|---|
| `textual` | Terminal UI framework |
| `rich` | Rich text rendering (used by Textual) |
| `psutil` | System process information (read-only) |
| `pytest` | Testing |
| `ruff` | Linting (dev) |

All dependencies are installed inside `.venv` — nothing touches the system Python.
