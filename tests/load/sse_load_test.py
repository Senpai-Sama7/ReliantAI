"""
ReliantAI Platform — SSE Load Test

Tests the Money /api/stream/dispatches endpoint under concurrent load.
Expected behavior: Server pushes dispatch updates via SSE; client receives
events until explicitly closed.

Usage:
    python sse_load_test.py --url http://localhost:8000/api/stream/dispatches \
                            --api-key test-api-key \
                            --clients 1000 \
                            --duration 300

Baselines:
  - 100  concurrent clients: stable, < 1% disconnect
  - 500  concurrent clients: acceptable, < 5% disconnect
  - 1000 concurrent clients: stress test, measure p95 latency
"""

import argparse
import asyncio
import time
import sys
import signal
from dataclasses import dataclass, field
from statistics import mean, median
from typing import List

import aiohttp


@dataclass
class ClientResult:
    client_id: int
    events_received: int = 0
    bytes_received: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    error: str = ""
    latency_samples: List[float] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0

    @property
    def events_per_sec(self) -> float:
        return self.events_received / self.duration if self.duration > 0 else 0


results: List[ClientResult] = []
stop_event = asyncio.Event()


async def sse_client(client_id: int, url: str, api_key: str, duration: int) -> ClientResult:
    result = ClientResult(client_id=client_id, start_time=time.time())
    headers = {"X-API-Key": api_key, "Accept": "text/event-stream"}

    try:
        timeout = aiohttp.ClientTimeout(total=duration + 30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    result.error = f"HTTP {resp.status}"
                    result.end_time = time.time()
                    return result

                async for line in resp.content:
                    if stop_event.is_set():
                        break
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("data:"):
                        result.events_received += 1
                        result.bytes_received += len(line)
                        if result.events_received == 1:
                            # First event latency
                            result.latency_samples.append(time.time() - result.start_time)
    except asyncio.TimeoutError:
        result.error = "timeout"
    except Exception as e:
        result.error = str(e)
    finally:
        result.end_time = time.time()

    return result


async def run_test(url: str, api_key: str, clients: int, duration: int):
    global results
    results = []

    print(f"Starting SSE load test: {clients} clients, {duration}s duration")
    print(f"Target: {url}")
    print("-" * 60)

    # Launch all clients concurrently
    tasks = [sse_client(i, url, api_key, duration) for i in range(clients)]

    # Duration timer
    async def timer():
        await asyncio.sleep(duration)
        stop_event.set()

    asyncio.create_task(timer())

    results = await asyncio.gather(*tasks)

    # ── Report ─────────────────────────────────────────────────────────
    successful = [r for r in results if not r.error]
    failed = [r for r in results if r.error]

    total_events = sum(r.events_received for r in successful)
    total_duration = sum(r.duration for r in successful)
    latencies = [s for r in successful for s in r.latency_samples]

    print("\n" + "=" * 60)
    print("SSE Load Test Results")
    print("=" * 60)
    print(f"Total clients:     {clients}")
    print(f"Successful:        {len(successful)} ({len(successful)/clients*100:.1f}%)")
    print(f"Failed:            {len(failed)} ({len(failed)/clients*100:.1f}%)")
    if failed:
        errors = {}
        for r in failed:
            errors[r.error] = errors.get(r.error, 0) + 1
        for err, count in errors.items():
            print(f"  - {err}: {count}")
    print(f"Total events:      {total_events}")
    print(f"Avg events/client: {total_events/len(successful):.1f}" if successful else "N/A")
    print(f"Throughput:        {total_events/max(total_duration, 1):.1f} events/sec")
    if latencies:
        print(f"First-event p50:   {median(latencies)*1000:.1f}ms")
        print(f"First-event p95:   {sorted(latencies)[int(len(latencies)*0.95)]*1000:.1f}ms")
    print("=" * 60)

    # Return exit code based on thresholds
    success_rate = len(successful) / clients
    if success_rate < 0.95:
        return 1
    if latencies and median(latencies) > 2.0:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="ReliantAI SSE Load Test")
    parser.add_argument("--url", default="http://localhost:8000/api/stream/dispatches")
    parser.add_argument("--api-key", default="test-api-key")
    parser.add_argument("--clients", type=int, default=100)
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()

    def signal_handler(sig, frame):
        print("\nReceived interrupt, stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    exit_code = asyncio.run(run_test(args.url, args.api_key, args.clients, args.duration))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
