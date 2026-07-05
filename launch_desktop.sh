#!/bin/bash
# OpenComputer Desktop Application Launcher (Linux/macOS)
# Run: chmod +x launch_desktop.sh && ./launch_desktop.sh

set -e

echo "============================================"
echo "  OpenComputer Desktop - Starting..."
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found! Please install Python 3.9+ first."
    exit 1
fi

# Check PyQt5
if ! python3 -c "import PyQt5" 2>/dev/null; then
    echo "[INFO] Installing PyQt5..."
    pip3 install PyQt5>=5.15
fi

# Check project dependencies
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "[INFO] Installing project dependencies..."
    pip3 install -r requirements.txt
fi

# Launch
exec python3 desktop_app/main.py
