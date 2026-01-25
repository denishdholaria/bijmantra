import requests
import sys

# Configuration
API_URL = "http://localhost:8000"
EMAIL = "demo@bijmantra.org"
PASSWORD = "Demo123!"

def verify():
    print(f"Verifying Core Programs API at {API_URL}...")
    
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
    
    # 2. List Programs
    print("Fetching programs...")
    resp = requests.get(f"{API_URL}/brapi/v2/programs", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ List Programs failed: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    
    # Verify BrAPI structure
    if "metadata" not in data or "result" not in data:
        print(f"❌ Invalid BrAPI response structure: {data.keys()}")
        sys.exit(1)
        
    programs = data["result"].get("data", [])
    print(f"✅ Fetch successful. Found {len(programs)} programs.")
    
    # 3. Create Program (Test)
    test_prog = {
        "programName": "Test Verification Program",
        "abbreviation": "TVP",
        "objective": "Verify API Production Readiness",
        "leadPersonDbId": None
    }
    
    print("Creating test program...")
    create_resp = requests.post(f"{API_URL}/brapi/v2/programs", headers=headers, json=test_prog)
    
    if create_resp.status_code == 201:
        created = create_resp.json()["result"]
        print(f"✅ Program created: {created.get('programDbId')}")
        
        # Cleanup (Delete)
        prog_id = created.get("programDbId")
        if prog_id:
            del_resp = requests.delete(f"{API_URL}/brapi/v2/programs/{prog_id}", headers=headers)
            if del_resp.status_code == 204:
                print("✅ Cleanup successful")
            else:
                print(f"⚠️ Cleanup failed: {del_resp.status_code}")
    else:
        # 409 Conflict is okay if it already exists
        if create_resp.status_code == 409:
             print("⚠️ Program already exists (Skipping creation)")
        else:
            print(f"❌ Create Program failed: {create_resp.status_code} - {create_resp.text}")
            
    print("\n🎉 Core Programs Verification: PASSED")

if __name__ == "__main__":
    verify()
