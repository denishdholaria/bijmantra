
import sys
import os
import requests
# Add backend to path
sys.path.append(os.getcwd())

from app.core.security import create_access_token
from app.core.config import settings

def test_api_quota():
    print("🧪 Testing AI Quota API...")
    
    # 1. Create a dummy token for a user
    # We assume 'test@example.com' exists or the token logic doesn't strictly check DB for decode
    # But for a real request, the API dependency `get_current_user` will check the DB.
    # So we need a valid user email. 'denish@bijmantra.com' usually exists.
    access_token = create_access_token(
        data={"sub": "denish@bijmantra.com"}
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # 2. Call the Endpoint
    try:
        url = "http://localhost:8000/api/v2/chat/usage"
        print(f"   - GET {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ Success (200 OK): {response.json()}")
        else:
            print(f"   ❌ Failed ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        print("      (Is the backend server running?)")

if __name__ == "__main__":
    test_api_quota()
