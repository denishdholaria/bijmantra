import requests
import json
import sys
import os

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
LOGIN_URL = f"{BASE_URL}/api/auth/login"
MARS_URL = f"{BASE_URL}/api/v2/space/mars/environments"

USERNAME = os.environ.get("TEST_USERNAME", "demo@bijmantra.org")
PASSWORD = os.environ.get("TEST_PASSWORD", "Demo123!")

def verify_space():
    print(f"🔄 Authenticating as {USERNAME}...")
    try:
        # Login
        response = requests.post(
            LOGIN_URL,
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return

        token = response.json()["access_token"]
        print("✅ Login successful. Token acquired.")

        # Verify Space Endpoint
        print(f"🔄 verifying Mars Environment endpoint ({MARS_URL})...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Correct Payload based on MarsEnvironmentProfileCreate schema
        payload = {
            "pressure_kpa": 60.0,
            "co2_ppm": 1200.0,
            "o2_ppm": 210000.0,
            "radiation_msv": 10.0,
            "gravity_factor": 0.38,
            "photoperiod_hours": 12.0,
            "temperature_profile": {"avg": 22, "min": 18, "max": 26, "unit": "C"},
            "humidity_profile": {"avg": 50, "min": 40, "max": 60, "unit": "RH"}
        }

        response = requests.post(MARS_URL, json=payload, headers=headers)

        if response.status_code == 200:
            print("✅ Space Module Verification SUCCESS!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Space Module Verification FAILED: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_space()
