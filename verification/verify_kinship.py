import requests
import numpy as np
import json

API_URL = "http://127.0.0.1:8000/api/v2/breeding-value/kinship"

def verify_kinship():
    print("🧬 Verifying Genomic Kinship API (VanRaden)...")
    
    # 1. Create synthetic marker data
    # 3 Individuals, 5 Markers per individual
    # Format: 0, 1, 2 (Dosage)
    
    # Ind 1: Heterozygous everywhere
    # Ind 2: Identical to Ind 1
    # Ind 3: Different (Homozygous Ref)
    
    markers = [
        {"id": "Ind1", "genotypes": [1, 1, 1, 1, 1]},
        {"id": "Ind2", "genotypes": [1, 1, 1, 1, 1]}, # Rel = 1.0 with Ind1
        {"id": "Ind3", "genotypes": [0, 0, 0, 0, 0]}  # Distant
    ]
    
    payload = {
        "markers": markers,
        "method": "vanraden"
    }
    
    try:
        print(f"   Sending {len(markers)} individuals...")
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                K = np.array(data["data"]["K"])
                print("✅ Kinship Calculation Successful")
                print("\n   Kinship Matrix (K):")
                print(np.round(K, 3))
                
                # Validation checks
                # Diagonal elements should be roughly 1 + F (Inbreeding)
                # K[0,1] should be high (identical)
                
                diag = np.diag(K)
                print(f"\n   Diagonals: {np.round(diag, 3)}")
                
                rel_1_2 = K[0, 1]
                print(f"   Relationship Ind1-Ind2: {rel_1_2:.3f} (Expected high)")
                
                if rel_1_2 > 0.9:
                    print("✅ Identity verified correctly")
                else:
                    print("⚠️ Identity check suspicious")
                    
            else:
                 print(f"❌ API success false: {data}")
        else:
             print(f"❌ Request failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_kinship()
