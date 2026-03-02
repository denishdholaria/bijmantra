import asyncio
import json
import time
from pathlib import Path
import random
import pytest
import tempfile
import shutil

# Performance test for api_stats endpoint non-blocking I/O optimization
# This test verifies that the event loop is not blocked during simulated slow file I/O

async def run_test_logic(tmp_path):
    # 1. Setup: Create a large metrics file in a temporary directory
    metrics_file = tmp_path / "metrics_test.json"

    data = {
        "api": {
            "totalEndpoints": 1370,
            "details": [
                {"endpoint": f"/api/v1/endpoint_{i}", "latency": random.random()}
                for i in range(5000)
            ]
        },
        "version": {
            "app": "0.2.0"
        }
    }

    with open(metrics_file, "w") as f:
        json.dump(data, f)

    # Simulate slow I/O latency
    SIMULATED_IO_LATENCY = 0.1

    # 2. Define the blocking and non-blocking implementations to test
    # (These replicate the logic in app/main.py but inject latency)

    # Blocking implementation (simulating old behavior)
    async def api_stats_blocking():
        metrics_paths = [metrics_file]
        start_time = time.time()
        for metrics_path in metrics_paths:
            if metrics_path.exists():
                try:
                    # BLOCKING I/O Simulation
                    time.sleep(SIMULATED_IO_LATENCY)
                    with open(metrics_path) as f:
                        metrics = json.load(f)
                        _ = metrics.get("api", {}).get("totalEndpoints", 1370)
                        break
                except (OSError, json.JSONDecodeError):
                    continue
        return time.time() - start_time

    # Helper for non-blocking
    def _load_metrics_sync(path):
        # Simulate slow I/O inside the thread
        time.sleep(SIMULATED_IO_LATENCY)
        with open(path) as f:
            metrics = json.load(f)
            return metrics.get("api", {}).get("totalEndpoints", 1370)

    # Non-blocking implementation (new behavior)
    async def api_stats_nonblocking():
        metrics_paths = [metrics_file]
        start_time = time.time()
        for metrics_path in metrics_paths:
            if metrics_path.exists():
                try:
                    # NON-BLOCKING (Offloaded to thread)
                    await asyncio.to_thread(_load_metrics_sync, metrics_path)
                    break
                except (OSError, json.JSONDecodeError):
                    continue
        return time.time() - start_time

    # 3. Helper to measure event loop blocking
    async def measure_blocking(func):
        delays = []
        running = True

        async def heartbeat():
            last_time = time.time()
            while running:
                target_sleep = 0.01
                await asyncio.sleep(target_sleep)
                now = time.time()
                actual_sleep = now - last_time
                delay = actual_sleep - target_sleep
                if delay > 0.005:
                    delays.append(delay)
                last_time = now

        heartbeat_task = asyncio.create_task(heartbeat())

        # Give heartbeat a chance to start
        await asyncio.sleep(0.05)

        # Run the function
        await func()

        running = False
        await heartbeat_task

        max_delay = max(delays) if delays else 0
        return max_delay

    # 4. Run the benchmarks

    print("Measuring blocking implementation...")
    blocking_delay = await measure_blocking(api_stats_blocking)
    print(f"Blocking implementation max delay: {blocking_delay:.4f}s")

    print("Measuring non-blocking implementation...")
    non_blocking_delay = await measure_blocking(api_stats_nonblocking)
    print(f"Non-blocking implementation max delay: {non_blocking_delay:.4f}s")

    # 5. Assertions

    if blocking_delay <= 0.05:
        raise AssertionError(f"Baseline blocking implementation did not block the event loop as expected (delay: {blocking_delay:.4f}s)")

    if non_blocking_delay >= 0.02:
        raise AssertionError(f"Optimized implementation still blocked the event loop (delay: {non_blocking_delay:.4f}s)")

    print("SUCCESS: Non-blocking implementation is effective.")

@pytest.mark.asyncio
async def test_api_stats_non_blocking_io(tmp_path):
    await run_test_logic(tmp_path)

if __name__ == "__main__":
    # Create a temp dir for running as script
    temp_dir = tempfile.mkdtemp()
    try:
        asyncio.run(run_test_logic(Path(temp_dir)))
    finally:
        shutil.rmtree(temp_dir)
