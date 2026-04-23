"""
ReliantAI Platform — WebSocket Load Test

Tests the Orchestrator WebSocket endpoint (/ws) under concurrent load.
Expected behavior: Clients connect, receive real-time status updates.

Usage:
    python websocket_load_test.py --url ws://localhost:9000/ws \
                                  --clients 100 \
                                  --duration 300

Baselines:
  - 100  concurrent clients: stable, < 1% disconnect
  - 500  concurrent clients: acceptable, < 5% disconnect
  - 1000 concurrent clients: stress test, measure message latency
"""

import argparse
import asyncio
import time
import sys
import signal
from dataclasses import dataclass, field
from statistics import median
from typing import List

import websockets


@dataclass
class WSResult:
    client_id: int
    messages_received: int = 0
    bytes_received: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    error: str = ""
    latency_samples: List[float] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0


results: List[WSResult] = []
stop_event = asyncio.Event()


async def ws_client(client_id: int, url: str, duration: int) -> WSResult:
    result = WSResult(client_id=client_id, start_time=time.time())

    try:
        async with websockets.connect(url, open_timeout=10, close_timeout=5) as ws:
            result.latency_samples.append(time.time() - result.start_time)

            while not stop_event.is_set():
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    result.messages_received += 1
                    result.bytes_received += len(msg.encode("utf-8"))
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
    except Exception as e:
        result.error = str(e)
    finally:
        result.end_time = time.time()

    return result


async def run_test(url: str, clients: int, duration: int):
    global results
    results = []

    print(f"Starting WebSocket load test: {clients} clients, {duration}s duration")
    print(f"Target: {url}")
    print("-" * 60)

    tasks = [ws_client(i, url, duration) for i in range(clients)]

    async def timer():
        await asyncio.sleep(duration)
        stop_event.set()

    asyncio.create_task(timer())
    results = await asyncio.gather(*tasks)

    # ── Report ─────────────────────────────────────────────────────────
    successful = [r for r in results if not r.error]
    failed = [r for r in results if r.error]

    total_messages = sum(r.messages_received for r in successful)
    total_duration = sum(r.duration for r in successful)
    latencies = [s for r in successful for s in r.latency_samples]

    print("\n" + "=" * 60)
    print("WebSocket Load Test Results")
    print("=" * 60)
    print(f"Total clients:        {clients}")
    print(f"Successful:           {len(successful)} ({len(successful)/clients*100:.1f}%)")
    print(f"Failed:               {len(failed)} ({len(failed)/clients*100:.1f}%)")
    if failed:
        errors = {}
        for r in failed:
            errors[r.error] = errors.get(r.error, 0) + 1
        for err, count in errors.items():
            print(f"  - {err}: {count}")
    print(f"Total messages:       {total_messages}")
    print(f"Avg messages/client:  {total_messages/len(successful):.1f}" if successful else "N/A")
    print(f"Throughput:           {total_messages/max(total_duration, 1):.1f} msg/sec")
    if latencies:
        print(f"Connect p50:          {median(latencies)*1000:.1f}ms")
        print(f"Connect p95:          {sorted(latencies)[int(len(latencies)*0.95)]*1000:.1f}ms")
    print("=" * 60)

    success_rate = len(successful) / clients
    if success_rate < 0.95:
        return 1
    if latencies and median(latencies) > 2.0:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="ReliantAI WebSocket Load Test")
    parser.add_argument("--url", default="ws://localhost:9000/ws")
    parser.add_argument("--clients", type=int, default=100)
    parser.add_argument("--duration", type=int, default=60)
    args = parser.parse_args()

    def signal_handler(sig, frame):
        print("\nReceived interrupt, stopping...")
        stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    exit_code = asyncio.run(run_test(args.url, args.clients, args.duration))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
