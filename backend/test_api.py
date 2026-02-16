"""
Simple API test script
Tests basic authentication and BrAPI endpoints
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_api():
    """Test API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Bijmantra API\n")

        # Test root endpoint
        print("1. Testing root endpoint...")
        response = await client.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test health check
        print("2. Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Test BrAPI serverinfo
        print("3. Testing BrAPI serverinfo...")
        response = await client.get(f"{BASE_URL}/brapi/v2/serverinfo")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Server: {data['result']['serverName']}")
        print(f"   Organization: {data['result']['organizationName']}\n")

        # Test login
        print("4. Testing login...")
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            data={
                "username": "admin@example.org",
                "password": "admin123"
            }
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print(f"   ✓ Login successful!")
            print(f"   Token: {token[:20]}...\n")

            # Test authenticated endpoint - list programs
            print("5. Testing authenticated endpoint (list programs)...")
            response = await client.get(
                f"{BASE_URL}/brapi/v2/programs",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Total programs: {data['metadata']['pagination']['totalCount']}\n")

            # Test create program
            print("6. Testing create program...")
            response = await client.post(
                f"{BASE_URL}/brapi/v2/programs",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "programName": "Test Breeding Program",
                    "abbreviation": "TBP",
                    "objective": "Testing the API"
                }
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 201:
                data = response.json()
                program_id = data['result']['programDbId']
                print(f"   ✓ Program created!")
                print(f"   Program ID: {program_id}\n")

                # Test get program
                print("7. Testing get program...")
                response = await client.get(
                    f"{BASE_URL}/brapi/v2/programs/{program_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"   Status: {response.status_code}")
                data = response.json()
                print(f"   Program name: {data['result']['programName']}\n")

            print("✅ All tests passed!")
        else:
            print(f"   ❌ Login failed: {response.json()}")


if __name__ == "__main__":
    print("Make sure the backend is running on http://localhost:8000\n")
    asyncio.run(test_api())
