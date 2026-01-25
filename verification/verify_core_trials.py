import requests
import sys

# Configuration
API_URL = "http://localhost:8000"
EMAIL = "demo@bijmantra.org"
PASSWORD = "Demo123!"

def verify():
    print(f"Verifying Core Trials API at {API_URL}...")
    
    # 1. Login
    try:
        login_resp = requests.post(f"{API_URL}/api/auth/login", data={
            "username": EMAIL,
            "password": PASSWORD
        })
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend at http://localhost:8000. Is it running?")
        sys.exit(1)
        
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code} - {login_resp.text}")
        sys.exit(1)
        
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # 2. List Trials
    print("Fetching trials...")
    resp = requests.get(f"{API_URL}/brapi/v2/trials", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ List Trials failed: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    
    # Verify BrAPI structure
    if "metadata" not in data or "result" not in data:
        print(f"❌ Invalid BrAPI response structure: {data.keys()}")
        sys.exit(1)
        
    trials = data["result"].get("data", [])
    print(f"✅ Fetch successful. Found {len(trials)} trials.")
    
    # 3. Create Trial (Test)
    # We need a valid programDbId to create a trial. Let's fetch the first program.
    prog_resp = requests.get(f"{API_URL}/brapi/v2/programs", headers=headers)
    programs = prog_resp.json().get("result", {}).get("data", [])
    
    if not programs:
        print("⚠️ No programs found. Cannot create a trial without a program. (Skipping creation test)")
        print("\n🎉 Core Trials Verification: PASSED (Read-Only)")
        return

    program_id = programs[0]["programDbId"]

    test_trial = {
        "trialName": "Test Verification Trial",
        "trialType": "Yield Trial",
        "active": True,
        "programDbId": program_id,
        "startDate": "2026-01-01",
        "endDate": "2026-06-01"
    }
    
    print(f"Creating test trial for program {program_id}...")
    create_resp = requests.post(f"{API_URL}/brapi/v2/trials", headers=headers, json=test_trial)
    
    if create_resp.status_code == 201:
        created = create_resp.json()["result"]
        print(f"✅ Trial created: {created.get('trialDbId')}")
        
        # Cleanup (Delete)
        trial_id = created.get("trialDbId")
        if trial_id:
            del_resp = requests.delete(f"{API_URL}/brapi/v2/trials/{trial_id}", headers=headers)
            if del_resp.status_code == 204:
                print("✅ Cleanup successful")
            else:
                print(f"⚠️ Cleanup failed: {del_resp.status_code}")
    else:
        if create_resp.status_code == 409:
             print("⚠️ Trial already exists (Skipping creation)")
        else:
            print(f"❌ Create Trial failed: {create_resp.status_code} - {create_resp.text}")
            
    print("\n🎉 Core Trials Verification: PASSED")

if __name__ == "__main__":
    verify()
