# Group 6: REST-based Distributed Counter (Concurrency Control Demo)

**Concepts:** concurrency control, the lost update problem, locking (mutual exclusion)

Many clients send `POST` requests at the same time to a shared counter on a REST server.

- **Mode 1, without a lock** (`/increment/unsafe`): updates get lost, so the final count ends up **lower** than the number of requests.
- **Mode 2, with a lock** (`/increment/safe`): the final count is **always correct**.

## Architecture

A single **FastAPI** server (run by Uvicorn) keeps two counters in memory: `unsafe` and `safe`.
Both endpoints do the same read → wait 5 ms → write steps. The 5 ms wait stands in for real work such as a database call.
Without a lock, parallel requests read the same old value and overwrite each other's writes (lost update).
With an `asyncio.Lock` (a mutex), only one request at a time runs the read-modify-write, so no update is lost. The price is that requests wait in a queue.
The clients are `load_test.py` (hundreds of concurrent HTTP requests) and a browser page that shows both modes side by side.

```
  CLIENTS (run in parallel)                    SERVER  (FastAPI + Uvicorn, 1 process)
 +-------------------------+   HTTP/JSON   +-----------------------------------------------+
 | load_test.py            |  -----------> |  POST /increment/unsafe                       |
 |  300 concurrent POSTs   |               |     read -> sleep 5ms -> write  (NO lock)  --+ |
 +-------------------------+               |                                              | |
 | Browser UI  (/)         |  -----------> |  POST /increment/safe                        v |
 |  "Send requests" button |               |     [ asyncio.Lock ]              +-----------+ |
 +-------------------------+               |     read -> sleep 5ms -> write -> | counters  | |
 | curl / other machines   |  -----------> |                                   | unsafe: n | |
 +-------------------------+               |  GET  /counter   POST /reset  --> | safe:   n | |
                                           |                                   +-----------+ |
                                           +-----------------------------------------------+
```

## Folder structure

```
Group_06_DistributedCounter/
  code/
    app.py              REST server (both modes)
    load_test.py        fires concurrent requests, prints expected vs actual
    requirements.txt    Python dependencies
    static/index.html   side-by-side demo page
  README.md
  group_details.txt
  demo_video.mp4
```

## Dependencies

- Python 3.9 or newer
- `fastapi`, `uvicorn`, `httpx` (installed from `code/requirements.txt`)

## How to run on Ubuntu / Linux

You need two terminals. Run everything from inside the `code/` folder.

**Terminal 1: install and start the server**

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
cd Group_06_DistributedCounter/code
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 2: run the load test**

```bash
cd Group_06_DistributedCounter/code
source venv/bin/activate
python load_test.py
```

To use the web UI, open **http://127.0.0.1:8000** in a browser and click **Send requests**. Each dot is one request: filled dots were counted, red rings were lost.
Interactive API docs are at http://127.0.0.1:8000/docs.

## How to run on Windows (PowerShell)

Install Python from python.org and tick **"Add python.exe to PATH"** during setup.
These commands call the venv's Python directly, so you never need `Activate.ps1` or to change the execution policy.

**Window 1: server**

```powershell
cd Group_06_DistributedCounter\code
py -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

**Window 2: load test**

```powershell
cd Group_06_DistributedCounter\code
venv\Scripts\python load_test.py
```

To use the web UI, open http://127.0.0.1:8000.

## Load test options

```bash
python load_test.py -n 500 -c 200                    # 500 requests per mode, 200 in parallel
python load_test.py --url http://<server-ip>:8000    # client on a different machine
```

## REST API

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/increment/unsafe` | +1 **without** a lock (can lose updates) |
| POST | `/increment/safe` | +1 **with** a lock (always correct) |
| POST | `/increment?mode=unsafe\|safe` | same as the two above, with the mode as a parameter |
| GET | `/counter` | `{"unsafe": n, "safe": n}` |
| POST | `/reset` | sets both counters to 0 |

## Sample output (real run)

```
Mode            Expected    Actual      Lost      Time
------------------------------------------------------
WITHOUT lock         300        90       210     0.66s
WITH lock            300       300         0     1.76s

WITHOUT lock: 210 of 300 increments were LOST (70%).
WITH lock:    every increment was counted. The final count is correct.
```

The exact "lost" number changes on every run because of timing, but it is always well above 0. The "with lock" row is always exact.

## Notes

- Run the server as **one process** (Uvicorn's default). The counters live in that process's memory. With `--workers 4`, each worker would have its own copy of the counters.
- To scale to several server replicas, the lock and the counter have to live in a shared place, for example Redis `INCR` or a database row lock (`SELECT ... FOR UPDATE`). This is the "distributed lock" version of the same idea.
