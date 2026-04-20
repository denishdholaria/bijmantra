import asyncio
import json
import os
import sys


# Set up path to backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.schemas.simulation import SimulationProtocol
from app.services.simulation_service import SimulationService


async def test_sadhana_engine():
    print("🚜 Sadhana Engine Verification Protocol...")

    # 1. Load Protocol Definition
    protocol_path = "docs/schemas/simulation_protocol.json"
    print(f"📖 Loading Protocol: {protocol_path}")

    try:
        with open(protocol_path) as f:
            data = json.load(f)

        # Extract the exampe from the JSON schema "examples" list
        # (The schema file itself contains an 'examples' list at the bottom)
        if "examples" in data and isinstance(data["examples"], list):
            example_protocol = data["examples"][0]
        else:
            print("❌ No examples found in schema file")
            return

        # 2. Parse into Pydantic Model
        print("🧩 Parsing Protocol Schema...")
        protocol = SimulationProtocol(**example_protocol)
        print(f"   ✅ Validated Protocol: {protocol.simulation_id}")

        # 3. Initialize Engine
        print("⚙️ Initializing Simulation Service...")
        service = SimulationService()

        # 4. Run Simulation
        print("🚀 Executing Simulation...")
        results = await service.run_simulation(protocol)

        # 5. Display Results
        print("\n📊 Simulation Results:")
        print(f"   Status: {results['status']}")
        print(f"   Steps Completed: {results['steps_completed']}")
        print("   Metrics:")
        for k, v in results["metrics"].items():
            print(f"     - {k}: {v}")

        # Validation Checks
        if results["status"] == "COMPLETED" and results["metrics"].get("biomass_kg", 0) > 0:
            print("\n✅ SADHANA ENGINE IS OPERATIONAL")
        else:
            print("\n❌ Simulation Failed or produced invalid results")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_sadhana_engine())
