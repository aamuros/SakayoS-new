#!/usr/bin/env bash
# SakayOS — Launch Script
# Requires Python 3.10+ and dependencies from requirements.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed." >&2
    exit 1
fi

python3 -m sakayos.app
