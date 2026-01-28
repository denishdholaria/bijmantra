import sys
import os
import asyncio
from httpx import AsyncClient, ASGITransport

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.main import app

async def verify():
    print("Verifying Genotyping Calls Endpoint...")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Check /brapi/v2/calls
        print("Calling GET /brapi/v2/calls")
        response = await ac.get("/brapi/v2/calls")
        print(f"GET /brapi/v2/calls Status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error: {response.text}")
            return

        data = response.json()
        calls = data.get("result", {}).get("data", [])
        print(f"Number of calls: {len(calls)}")

        if len(calls) > 0:
            print("✅ Verification SUCCESS: Calls returned.")
        else:
            print("⚠️ Verification WARNING: No calls returned (Database might be empty).")

if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error during verification: {e}")
