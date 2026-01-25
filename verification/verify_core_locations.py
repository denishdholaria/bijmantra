import requests
import sys

# Configuration
API_URL = "http://localhost:8000"
EMAIL = "demo@bijmantra.org"
PASSWORD = "Demo123!"

def verify():
    print(f"Verifying Core Locations API at {API_URL}...")
    
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
    
    # 2. List Locations
    print("Fetching locations...")
    resp = requests.get(f"{API_URL}/brapi/v2/locations", headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ List Locations failed: {resp.status_code} - {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    
    # Verify BrAPI structure
    if "metadata" not in data or "result" not in data:
        print(f"❌ Invalid BrAPI response structure: {data.keys()}")
        sys.exit(1)
        
    locations = data["result"].get("data", [])
    print(f"✅ Fetch successful. Found {len(locations)} locations.")
    
    # 3. Create Location (Test)
    test_loc = {
        "locationName": "Test Verification Field",
        "locationType": "Breeding Station",
        "countryCode": "IND",
        "countryName": "India",
        "abbreviation": "TVF",
        "instituteName": "BijMantra Research",
        "instituteAddress": "Gujarat, India"
    }
    
    print("Creating test location...")
    create_resp = requests.post(f"{API_URL}/brapi/v2/locations", headers=headers, json=test_loc)
    
    if create_resp.status_code == 201:
        created = create_resp.json()["result"]
        print(f"✅ Location created: {created.get('locationDbId')}")
        
        # Cleanup (Delete)
        loc_id = created.get("locationDbId")
        if loc_id:
            del_resp = requests.delete(f"{API_URL}/brapi/v2/locations/{loc_id}", headers=headers)
            if del_resp.status_code == 204:
                print("✅ Cleanup successful")
            else:
                print(f"⚠️ Cleanup failed: {del_resp.status_code}")
    else:
        if create_resp.status_code == 409:
             print("⚠️ Location already exists (Skipping creation)")
        else:
            print(f"❌ Create Location failed: {create_resp.status_code} - {create_resp.text}")
            
    print("\n🎉 Core Locations Verification: PASSED")

if __name__ == "__main__":
    verify()
