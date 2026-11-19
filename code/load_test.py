"""
Load test for the Group 6 Distributed Counter.

Fires many concurrent POST requests at /increment/unsafe and /increment/safe,
then prints expected vs actual counts side by side.

Usage (server must already be running):
    python load_test.py                          # 300 requests per mode, 100 at a time
    python load_test.py -n 500 -c 200            # 500 requests per mode, 200 at a time
    python load_test.py --url http://192.168.1.20:8000   # hit a server on another machine
"""

import argparse
import asyncio
import sys
import time

import httpx

MODES = [("unsafe", "WITHOUT lock"), ("safe", "WITH lock")]


async def fire_requests(client: httpx.AsyncClient, mode: str, total: int, concurrency: int) -> float:
    """Send `total` increments to one mode, at most `concurrency` in flight. Returns seconds taken."""
    gate = asyncio.Semaphore(concurrency)

    async def one_request():
        async with gate:
            response = await client.post(f"/increment/{mode}")
            response.raise_for_status()

    start = time.perf_counter()
    await asyncio.gather(*(one_request() for _ in range(total)))
    return time.perf_counter() - start


async def main() -> int:
    parser = argparse.ArgumentParser(description="Lost update demo: unsafe vs safe counter")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="server address")
    parser.add_argument("-n", "--requests", type=int, default=300, help="requests per mode (default 300)")
    parser.add_argument("-c", "--concurrency", type=int, default=100, help="requests in flight at once (default 100)")
    args = parser.parse_args()

    limits = httpx.Limits(max_connections=args.concurrency, max_keepalive_connections=args.concurrency)
    async with httpx.AsyncClient(base_url=args.url, timeout=120, limits=limits) as client:
        try:
            await client.post("/reset")
        except httpx.ConnectError:
            print(f"Could not reach the server at {args.url}. Start it first with:")
            print("    uvicorn app:app --host 127.0.0.1 --port 8000")
            return 1

        print()
        print("Group 6 - REST-based Distributed Counter : load test")
        print(f"Server: {args.url}   Requests per mode: {args.requests}   In parallel: {args.concurrency}")
        print()

        rows = []
        for mode, label in MODES:
            print(f"  Sending {args.requests} requests to /increment/{mode} ...")
            seconds = await fire_requests(client, mode, args.requests, args.concurrency)
            actual = (await client.get("/counter")).json()[mode]
            rows.append((label, args.requests, actual, args.requests - actual, seconds))

    print()
    print(f"{'Mode':<14}{'Expected':>10}{'Actual':>10}{'Lost':>10}{'Time':>10}")
    print("-" * 54)
    for label, expected, actual, lost, seconds in rows:
        print(f"{label:<14}{expected:>10}{actual:>10}{lost:>10}{seconds:>9.2f}s")
    print()

    unsafe_lost = rows[0][3]
    safe_lost = rows[1][3]
    pct = 100 * unsafe_lost / args.requests
    print(f"WITHOUT lock: {unsafe_lost} of {args.requests} increments were LOST ({pct:.0f}%).")
    if safe_lost == 0:
        print("WITH lock:    every increment was counted. The final count is correct.")
    else:
        print(f"WITH lock:    {safe_lost} increments missing - unexpected, was another test running?")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
