#!/bin/bash
# Seed Demo Data Script for Beep.AI.Community
# This will seed comprehensive demo data for the platform
#
# Usage:
#   ./seed_demo_data.sh              - Normal seeding
#   ./seed_demo_data.sh --reset      - Clear and reseed
#   ./seed_demo_data.sh --users-only - Seed only users

cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  Seeding Demo Data for Beep.AI.Community"
echo "============================================================"
echo ""

# Determine Python executable
if [ -f "python-embedded/python.exe" ]; then
    PYTHON="python-embedded/python.exe"
elif [ -f "python-embedded/python" ]; then
    PYTHON="python-embedded/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo "[ERROR] Python not found!"
    echo "Please run ./run.sh first to set up the environment."
    exit 1
fi

# Run the seeding script
$PYTHON scripts/seed_demo_data.py "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to seed demo data"
    exit 1
fi

echo ""
echo "[SUCCESS] Demo data seeding completed!"

