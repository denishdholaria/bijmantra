import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from httpx import AsyncClient, ASGITransport
from app.main import app
# Mock Authentication
async def mock_auth_dependency():
    return {"id": 1, "username": "test_user", "organization_id": 1}

app.dependency_overrides["app.api.v2.dependencies.get_current_user"] = mock_auth_dependency

async def verify_traceability():
    print("🌱 Verifying Seed Traceability Module...")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        # 1. Register a Lot
        print("\n1. Registering Seed Lot...")
        lot_data = {
            "variety_id": "VAR-001",
            "variety_name": "Wheat Super X",
            "crop": "Wheat",
            "seed_class": "foundation",
            "production_year": 2024,
            "production_season": "Rabi",
            "production_location": "Field A1",
            "producer_id": "PROD-101",
            "producer_name": "John Doe",
            "quantity_kg": 1000.0,
            "germination_percent": 98.5,
            "purity_percent": 99.9
        }

        response = await ac.post("/api/v2/traceability/lots", json=lot_data)
        if response.status_code != 200:
            print(f"❌ Failed to register lot: {response.text}")
            return

        lot = response.json()["data"]
        lot_id = lot["lot_id"]
        print(f"✅ Lot Registered: {lot_id}")

        # 2. Record Event
        print("\n2. Recording Event...")
        event_data = {
            "event_type": "processing",
            "details": {"method": "cleaning", "machine": "M1"},
            "operator_name": "Alice",
            "location": "Processing Unit 1"
        }
        response = await ac.post(f"/api/v2/traceability/lots/{lot_id}/events", json=event_data)
        if response.status_code != 200:
            print(f"❌ Failed to record event: {response.text}")
            return
        print("✅ Event Recorded")

        # 3. Add Certification
        print("\n3. Adding Certification...")
        cert_data = {
            "cert_type": "phytosanitary",
            "cert_number": "CERT-2024-001",
            "issuing_authority": "Agri Dept",
            "issue_date": datetime.now().isoformat(),
            "expiry_date": datetime.now().isoformat()
        }
        response = await ac.post(f"/api/v2/traceability/lots/{lot_id}/certifications", json=cert_data)
        if response.status_code != 200:
            print(f"❌ Failed to add certification: {response.text}")
            return
        print("✅ Certification Added")

        # 4. Get History
        print("\n4. Fetching History...")
        response = await ac.get(f"/api/v2/traceability/lots/{lot_id}/history")
        history = response.json()["data"]
        print(f"✅ History retrieved: {len(history)} events")
        assert len(history) >= 1

        # 5. Get Statistics
        print("\n5. Fetching Statistics...")
        response = await ac.get("/api/v2/traceability/statistics")
        stats = response.json()["data"]
        print(f"✅ Statistics: {stats}")

    print("\n🎉 Backend Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_traceability())
