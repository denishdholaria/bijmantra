import requests
import cv2
import numpy as np
import base64
import os
import io

API_URL = "http://127.0.0.1:8000/api/v2/image-analysis/spectral-indices"

def verify_image_analysis():
    print("🧪 Verifying Image Analysis API...")
    
    # 1. Create a synthetic test image (Green square on Blue background)
    # TGI should highlight green.
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = [255, 0, 0] # Blue background (BGR)
    img[25:75, 25:75] = [0, 255, 0] # Green square (BGR)
    
    # Encode to bytes for upload
    success, encoded_img = cv2.imencode('.png', img)
    if not success:
        print("❌ Failed to create test image")
        return

    # 2. Test TGI (Triangular Greenness Index)
    print("\n📸 Testing TGI Index...")
    files = {'file': ('test.png', encoded_img.tobytes(), 'image/png')}
    data = {'index': 'tgi'}
    
    try:
        response = requests.post(API_URL, files=files, data=data)
        
        if response.status_code == 200:
            json_resp = response.json()
            if json_resp.get("success"):
                print("✅ TGI Analysis Successful")
                print(f"   Response Length: {len(json_resp['image_data'])}")
                
                # Verify content is roughly correct?
                # TGI Formula: G - 0.39*R - 0.61*B
                # Green Square: 255 - 0 - 0 = 255
                # Blue Background: 0 - 0 - 0.61*255 = -155 -> Clipped to 0
                # So output should be white square on black background.
                pass
            else:
                print(f"❌ API reported failure: {json_resp}")
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 3. Test CCC (Canopy Cover)
    print("\n📸 Testing CCC Index...")
    # Reset file pointer or recreate files dict (requests consumes it?)
    files = {'file': ('test.png', encoded_img.tobytes(), 'image/png')}
    data = {'index': 'ccc'}
    
    try:
        response = requests.post(API_URL, files=files, data=data)
        if response.status_code == 200 and response.json().get("success"):
            print("✅ CCC Analysis Successful")
        else:
            print(f"❌ CCC Request failed: {response.text}")
    except Exception as e:
         print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_image_analysis()
