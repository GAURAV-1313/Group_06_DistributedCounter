#!/usr/bin/env bash
# Fires concurrent requests at both modes and prints expected vs actual counts.
# The server must already be running (./run_server.sh in another terminal).
# Usage:  ./run_load_test.sh
#         ./run_load_test.sh -n 500 -c 200
#         ./run_load_test.sh --url http://192.168.1.20:8000
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x venv/bin/python ]; then
    echo "Run ./setup.sh first."
    exit 1
fi

exec venv/bin/python load_test.py "$@"
