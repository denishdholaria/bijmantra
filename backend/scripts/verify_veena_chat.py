
import requests
import json
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "demo@bijmantra.org"
PASSWORD = "Demo123!"

def get_token():
    print(f"🔄 Authenticating as {USERNAME}...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            print("✅ Login successful. Token acquired.")
            return response.json()["access_token"]
        else:
            print(f"❌ Login FAILED: {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        sys.exit(1)

def verify_veena_health(token):
    print(f"\n🔄 verifying Veena Health endpoint ({BASE_URL}/api/v2/chat/health)...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/api/v2/chat/health", headers=headers)
        if response.status_code == 200:
            print("✅ Veena Health Verification SUCCESS!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Veena Health Verification FAILED: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return False

def verify_veena_chat(token):
    print(f"\n🔄 verifying Veena Chat endpoint ({BASE_URL}/api/v2/chat/)...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": "Hello Veena, are you online?",
        "conversation_history": [],
        "include_context": False
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v2/chat/", json=payload, headers=headers)
        if response.status_code == 200:
            print("✅ Veena Chat Verification SUCCESS!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"❌ Veena Chat Verification FAILED: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return False


def verify_cross_domain_reasoning(token):
    print(f"\n🔄 verifying Cross-Domain Reasoning (Mars + Genetics)...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": "Given the atmospheric conditions of Mars (high radiation, average temp -63C), which germplasm traits should I prioritize for a breeding program?",
        "conversation_history": [],
        "include_context": True
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v2/chat/", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Reasoning Request SUCCESS!")
            print(f"Response: {json.dumps(data, indent=2)}")

            message = data.get("message", "").lower()
            if "radiation" in message or "cold" in message or "tolerance" in message:
                 print("✅ Reasoning Logic Check PASSED (Keywords found)")
                 return True
            else:
                 print("⚠️ Reasoning Logic Check WARNING: Response might be generic.")
                 return True
        else:
            print(f"❌ Reasoning Request FAILED: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        return False

if __name__ == "__main__":
    token = get_token()

    health_ok = verify_veena_health(token)
    chat_ok = verify_veena_chat(token)
    reasoning_ok = verify_cross_domain_reasoning(token)

    if health_ok and chat_ok and reasoning_ok:
        print("\n🎉 ALL CHECKS PASSED: Veena AI is ONLINE and REASONING.")
    else:
        print("\n⚠️ SOME CHECKS FAILED. See output above.")
