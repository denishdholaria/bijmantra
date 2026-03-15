import requests
import json
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v2"
BRAPI_URL = "http://localhost:8000/brapi/v2"
EMAIL = "admin@bijmantra.org"
PASSWORD = "Admin123!"

def login():
    """Get access token"""
    print(f"🔑 Logging in as {EMAIL}...")
    try:
        response = requests.post(
            f"http://localhost:8000/api/auth/login",
            data={"username": EMAIL, "password": PASSWORD}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Login successful")
        return token
    except Exception as e:
        print(f"❌ Login failed: {e}")
        try:
            print(response.text)
        except:
            pass
        return None

def wait_for_job(token, job_id, timeout=60):
    """Wait for import job to complete"""
    print(f"⏳ Waiting for Job {job_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_URL}/import/jobs", headers=headers)
            response.raise_for_status()
            jobs = response.json()
            # Find our job
            job = next((j for j in jobs if j["id"] == job_id), None)

            if job:
                status = job["status"]
                if status == "completed":
                    print(f"✅ Job {job_id} completed successfully")
                    return True
                elif status == "failed":
                    print(f"❌ Job {job_id} failed: {job.get('error_details', 'Unknown error')}")
                    return False
                else:
                    # print(f"🔄 Job {job_id} status: {status}")
                    pass
            else:
                print(f"⚠️ Job {job_id} not found in list")

        except Exception as e:
            print(f"⚠️ Error checking job status: {e}")

        time.sleep(2)

    print(f"❌ Timeout waiting for Job {job_id}")
    return False

def get_trait(token, name):
    """Check if trait exists"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BRAPI_URL}/traits",
            params={"observationVariableName": name},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json().get("result", {}).get("data", [])
            if data:
                return data[0]
    except Exception as e:
        print(f"⚠️ Error checking trait {name}: {e}")
    return None

def create_trait(token, name):
    """Create trait if not exists"""
    existing = get_trait(token, name)
    if existing:
        print(f"✅ Trait '{name}' already exists")
        return existing

    print(f"➕ Creating Trait '{name}'...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "observationVariableName": name,
        "traitName": name,
        "traitDescription": f"Test trait {name}",
        "traitClass": "Phenological",
        "defaultValue": "0"
    }

    try:
        response = requests.post(
            f"{BRAPI_URL}/traits",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        print(f"✅ Created Trait '{name}'")
        return response.json().get("result")
    except Exception as e:
        print(f"❌ Failed to create trait {name}: {e}")
        return None

def get_germplasm_id(token, name):
    """Get germplasm ID by name"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BRAPI_URL}/germplasm",
            params={"germplasmName": name},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json().get("result", {}).get("data", [])
            if data:
                return data[0]["germplasmDbId"]
    except Exception as e:
        print(f"⚠️ Error getting germplasm ID for {name}: {e}")
    return None

def create_study(token, name):
    """Create a new study"""
    print(f"➕ Creating Study '{name}'...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "studyName": name,
        "studyType": "Field Trial",
        "studyDescription": "Test Study for Import Verification"
    }

    try:
        # Check if exists first
        response = requests.get(
            f"{BRAPI_URL}/studies",
            params={"studyName": name},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json().get("result", {}).get("data", [])
            if data:
                print(f"✅ Study '{name}' already exists")
                return data[0]

        # Create
        response = requests.post(
            f"{BRAPI_URL}/studies",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        print(f"✅ Created Study '{name}'")
        return response.json().get("result")
    except Exception as e:
        print(f"❌ Failed to create study {name}: {e}")
        return None

def create_observation_unit(token, name, study_db_id, germplasm_db_id):
    """Create observation unit"""
    print(f"➕ Creating Unit '{name}'...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "observationUnitName": name,
        "studyDbId": study_db_id,
        "germplasmDbId": germplasm_db_id,
        "observationLevel": "plot"
    }

    try:
        # Check if exists
        response = requests.get(
            f"{BRAPI_URL}/observationunits",
            params={"observationUnitName": name, "studyDbId": study_db_id},
            headers=headers
        )
        if response.status_code == 200:
            data = response.json().get("result", {}).get("data", [])
            if data:
                print(f"✅ Unit '{name}' already exists")
                return data[0]

        # Create
        response = requests.post(
            f"{BRAPI_URL}/observationunits",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        print(f"✅ Created Unit '{name}'")
        return response.json().get("result")
    except Exception as e:
        print(f"❌ Failed to create unit {name}: {e}")
        try:
            print(response.text)
        except:
            pass
        return None

def verify_germplasm(token):
    """Test Germplasm Import"""
    print("\n🧬 Testing Germplasm Import...")
    
    # Generate dummy data
    batch_id = random.randint(1000, 9999)
    payload = {
        "data": [
            {
                "germplasmName": f"TEST-VAR-{batch_id}-A",
                "accessionNumber": f"ACC-{batch_id}-001",
                "genus": "Zea",
                "species": "mays",
                "commonCropName": "Maize",
                "pedigree": "B73 x Mo17",
                "countryOfOriginCode": "USA"
            },
            {
                "germplasmName": f"TEST-VAR-{batch_id}-B",
                "accessionNumber": f"ACC-{batch_id}-002",
                "genus": "Oryza",
                "species": "sativa",
                "commonCropName": "Rice",
                "pedigree": "IR64",
                "countryOfOriginCode": "PHL"
            }
        ],
        "options": {"format": "json"}
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{API_URL}/import/germplasm",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        print(f"✅ Import Result: {json.dumps(response.json(), indent=2)}")

        job_id = response.json().get("job_id")
        if job_id:
             if wait_for_job(token, job_id):
                 return batch_id
        return None
    except Exception as e:
        print(f"❌ Germplasm Import Failed: {e}")
        try:
            print(response.text)
        except:
            pass
        return None

def verify_observations(token, batch_id):
    """Test Observation Import"""
    print("\n📊 Testing Observation Import...")
    
    # Prerequisite: We need Traits and ObservationUnits in DB for this to work.
    
    # Create Dependencies
    print("🛠️ Creating Dependencies...")

    # 1. Traits
    create_trait(token, "Yield")
    create_trait(token, "Plant Height")

    # 2. Study
    study = create_study(token, f"Test Study {batch_id}")
    study_db_id = study.get("studyDbId") if study else None

    if not study_db_id:
        print("❌ Skipping observation test due to missing Study")
        return

    # 3. Germplasm IDs
    germplasm_a = get_germplasm_id(token, f"TEST-VAR-{batch_id}-A")
    germplasm_b = get_germplasm_id(token, f"TEST-VAR-{batch_id}-B")

    if not germplasm_a or not germplasm_b:
        print("❌ Skipping observation test due to missing Germplasm")
        return

    # 4. Observation Units
    unit_a_name = f"Plot-{batch_id}-001"
    unit_b_name = f"Plot-{batch_id}-002"

    create_observation_unit(token, unit_a_name, study_db_id, germplasm_a)
    create_observation_unit(token, unit_b_name, study_db_id, germplasm_b)
    
    
    payload = {
        "data": [
            {
                "observationUnitName": unit_a_name,
                "trait": "Yield",
                "value": "5.6",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            {
                "observationUnitName": unit_b_name,
                "trait": "Plant Height", 
                "value": "120",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        ],
        "options": {"format": "json"}
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{API_URL}/import/observations",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        print(f"✅ Import Result: {json.dumps(response.json(), indent=2)}")

        job_id = response.json().get("job_id")
        if job_id:
             wait_for_job(token, job_id)

    except Exception as e:
        print(f"❌ Observation Import Failed: {e}")
        try:
            print(response.text)
        except:
            pass

if __name__ == "__main__":
    token = login()
    if token:
        batch_id = verify_germplasm(token)
        if batch_id:
            verify_observations(token, batch_id)
