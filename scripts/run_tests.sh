#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# SakayOS — Test Runner
#
# Runs pytest and ruff (if available) inside the project virtual environment.
#
# Usage:
#   chmod +x scripts/run_tests.sh
#   ./scripts/run_tests.sh
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# ── Locate python ──────────────────────────────────────────────────────────
PYTHON=""
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "Error: python3 not found. Run scripts/setup_ubuntu.sh first." >&2
    exit 1
fi

echo "Using: $PYTHON ($($PYTHON --version 2>&1))"
echo ""

# ── Run pytest ─────────────────────────────────────────────────────────────
echo "═══ Running pytest ═══"
"$PYTHON" -m pytest tests/ -v
echo ""

# ── Run ruff (if installed) ────────────────────────────────────────────────
if "$PYTHON" -m ruff --version &>/dev/null 2>&1; then
    echo "═══ Running ruff ═══"
    "$PYTHON" -m ruff check sakayos/ tests/
else
    echo "(ruff not installed — skipping lint)"
fi

echo ""
echo "Done."
