"""
Group 6 - REST-based Distributed Counter (Concurrency Control Demo)

One FastAPI server keeps two counters in memory:

  * "unsafe" counter -> updated WITHOUT a lock  (shows the lost update problem)
  * "safe"   counter -> updated WITH a lock     (always ends up correct)

Both counters are updated with exactly the same three steps:

    1. READ  the current value
    2. WAIT  a few milliseconds (stands in for real work: a DB query, a network call...)
    3. WRITE back value + 1

The ONLY difference between the two modes is the lock around those steps.

Run it with:   uvicorn app:app --host 127.0.0.1 --port 8000
"""

import asyncio
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse

# Gap between READ and WRITE. In real systems this gap always exists (database
# round trip, remote call). We make it explicit so the race is easy to see.
WORK_DELAY_SECONDS = 0.005

app = FastAPI(
    title="Group 6 - Distributed Counter",
    description="Concurrency control demo: lost updates without a lock, correct count with a lock.",
    version="1.0",
)

# Shared state. Every client request reads and writes these numbers.
counters = {"unsafe": 0, "safe": 0}

# A mutex (mutual exclusion lock). Only one request at a time may hold it.
safe_lock = asyncio.Lock()

STATIC_DIR = Path(__file__).parent / "static"


async def increment_without_lock() -> int:
    current = counters["unsafe"]              # 1. READ
    await asyncio.sleep(WORK_DELAY_SECONDS)   # 2. WAIT - other requests run now and read the SAME old value
    counters["unsafe"] = current + 1          # 3. WRITE - may overwrite another request's update (lost update)
    return current + 1


async def increment_with_lock() -> int:
    async with safe_lock:                     # other requests queue here until the lock is free
        current = counters["safe"]            # 1. READ
        await asyncio.sleep(WORK_DELAY_SECONDS)   # 2. WAIT - nobody else can touch the counter meanwhile
        counters["safe"] = current + 1        # 3. WRITE
        return current + 1


# ----------------------------- REST endpoints ------------------------------

@app.get("/", include_in_schema=False)
async def home():
    """The demo web page with the two side-by-side panels."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/increment/unsafe")
async def increment_unsafe():
    """Mode 1: increment WITHOUT a lock."""
    return {"mode": "unsafe", "value": await increment_without_lock()}


@app.post("/increment/safe")
async def increment_safe():
    """Mode 2: increment WITH a lock."""
    return {"mode": "safe", "value": await increment_with_lock()}


@app.post("/increment")
async def increment(mode: Literal["safe", "unsafe"] = "safe"):
    """Same as above, but the mode is a query parameter: /increment?mode=unsafe"""
    if mode == "unsafe":
        return await increment_unsafe()
    return await increment_safe()


@app.get("/counter")
async def get_counter():
    """Current value of both counters."""
    return dict(counters)


@app.post("/reset")
async def reset():
    """Set both counters back to 0 (call it when no test is running)."""
    async with safe_lock:
        counters["unsafe"] = 0
        counters["safe"] = 0
    return dict(counters)
