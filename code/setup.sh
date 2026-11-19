#!/usr/bin/env bash
# One-time setup on Ubuntu/Linux: creates a virtual environment and installs dependencies.
# Usage:  ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found. On Ubuntu install it with:"
    echo "    sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi

echo "Using $(python3 --version)"

# Ubuntu ships python3 without the venv module; install it if it is missing.
if ! python3 -m venv --help >/dev/null 2>&1 || ! python3 -c "import ensurepip" >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installing python3-venv (needs your sudo password)..."
        sudo apt-get update
        sudo apt-get install -y python3-venv
    else
        echo "The Python venv module is missing. Install python3-venv with your package manager, then run ./setup.sh again."
        exit 1
    fi
fi

if [ ! -d venv ]; then
    echo "Creating virtual environment in code/venv ..."
    python3 -m venv venv
fi

echo "Installing dependencies ..."
venv/bin/python -m pip install --upgrade pip --quiet
venv/bin/python -m pip install -r requirements.txt --quiet

echo
echo "Setup complete."
echo "  Start the server:   ./run_server.sh"
echo "  Run the load test:  ./run_load_test.sh      (in a second terminal)"
echo "  Open the web UI:    http://127.0.0.1:8000"
