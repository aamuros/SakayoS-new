#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# SakayOS — Ubuntu Setup Script
#
# Safe to run on classroom / bootable USB Ubuntu environments.
# Does NOT require sudo. Does NOT install system packages.
#
# What it does:
#   1. Checks that Python 3.10+ is available.
#   2. Creates a virtual environment (.venv) if one does not exist.
#   3. Installs project dependencies from requirements.txt.
#   4. Prints the command to launch the app.
#
# Usage:
#   chmod +x scripts/setup_ubuntu.sh
#   ./scripts/setup_ubuntu.sh
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# ── Colours ────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

info()  { echo -e "${GREEN}[✔]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✘]${NC} $*" >&2; }

# ── 1. Check Python ───────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    error "python3 is not installed."
    echo ""
    echo "  On Ubuntu, run:"
    echo "    sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo ""
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    error "Python 3.10+ is required, but found Python $PY_VERSION"
    exit 1
fi

info "Python $PY_VERSION found."

# ── 2. Create virtual environment ─────────────────────────────────────────
if [ ! -d ".venv" ]; then
    info "Creating virtual environment (.venv)…"
    python3 -m venv .venv
    info "Virtual environment created."
else
    info "Virtual environment (.venv) already exists."
fi

# ── 3. Install dependencies ───────────────────────────────────────────────
info "Installing dependencies…"
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
info "Dependencies installed."

# ── 4. Quick import check ─────────────────────────────────────────────────
info "Verifying sakayos imports…"
if .venv/bin/python -c "import sakayos.app" 2>/dev/null; then
    info "Import check passed."
else
    warn "Import check failed — the app may still work, but review errors above."
fi

# ── 5. Done ───────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo ""
echo "  To run the app:"
echo "    ./run.sh"
echo ""
echo "  Or directly:"
echo "    .venv/bin/python -m sakayos.app"
echo ""
echo "  To run tests:"
echo "    ./scripts/run_tests.sh"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
