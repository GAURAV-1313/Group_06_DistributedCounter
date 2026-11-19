#!/usr/bin/env bash
# Starts the counter server. Stop it with Ctrl+C.
# Usage:  ./run_server.sh            (port 8000)
#         PORT=9000 ./run_server.sh  (another port)
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x venv/bin/python ]; then
    echo "Run ./setup.sh first."
    exit 1
fi

PORT="${PORT:-8000}"
echo "Server starting. Open http://127.0.0.1:${PORT} in a browser (Ctrl+C to stop)."
# 0.0.0.0 lets other machines on the network reach it too (one process only: the counters live in memory).
exec venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port "$PORT"
