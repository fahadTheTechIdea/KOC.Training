#!/bin/bash
# KOC A.I. Digital Campus - Linux/macOS Launcher
# This script automatically sets up and runs KOC A.I. Digital Campus
#
# Usage:
#   ./run.sh                    - Normal mode
#   ./run.sh --port=5003        - Run on custom port
#   ./run.sh --host=0.0.0.0     - Listen on all interfaces
#   ./run.sh --reset-db         - Reset database before starting
#   ./run.sh --seed-demo        - Seed demo data before starting
#   ./run.sh --reset-db --seed-demo - Reset and seed demo data

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo "  KOC A.I. Digital Campus - Linux/macOS Launcher"
echo "============================================================"
echo ""

# Check for --reset-db flag
if [[ "$*" == *"--reset-db"* ]]; then
    echo "[INFO] Resetting database..."
    rm -f "instance/community.db" 2>/dev/null
    rm -f "community.db" 2>/dev/null
    rm -f "instance/setup_complete.json" 2>/dev/null
    echo "[OK] Database reset complete"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Make script executable
chmod +x run_community.py 2>/dev/null

# Check for --seed-demo flag
if [[ "$*" == *"--seed-demo"* ]]; then
    echo "[INFO] Seeding demo data..."
    python3 scripts/seed_demo_data.py
    if [ $? -ne 0 ]; then
        echo "[WARN] Demo seeding had issues, continuing anyway..."
    else
        echo "[OK] Demo data seeded successfully"
    fi
fi

# Run the Python launcher
python3 run_community.py "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to start Beep.AI.Community"
    exit 1
fi
