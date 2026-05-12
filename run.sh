#!/usr/bin/env bash
# SakayOS — Launch Script
# Requires Python 3.10+ and dependencies from requirements.txt
#
# Usage:
#   chmod +x run.sh
#   ./run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Locate python ──────────────────────────────────────────────────────────
PYTHON=""
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "Error: python3 is not installed." >&2
    echo "Run:  sudo apt install python3 python3-venv python3-pip" >&2
    exit 1
fi

echo "Using: $PYTHON ($($PYTHON --version 2>&1))"
exec "$PYTHON" -m sakayos.app
