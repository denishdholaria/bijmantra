import requests
import json
import numpy as np

API_URL = "http://127.0.0.1:8000/api/v2/breeding-value/gblup"

def verify_gblup():
    print("🧬 Verifying GBLUP Solver...")
    
    # Synthetic Data
    # 3 Individuals
    # Phenotypes: Yield
    # Genotypes: 5 Markers
    
    # Ind 1: High Yield, Genotype A
    # Ind 2: High Yield, Genotype A (Clone/Twin)
    # Ind 3: Low Yield, Genotype B (Distant)
    
    # Expectation: 
    # Ind 1 and 2 should have similar GEBVs.
    # Ind 3 should have lower GEBV.
    
    payload = {
        "phenotypes": [
            {"id": "Ind1", "yield": 100.0},
            {"id": "Ind2", "yield": 98.0},
            {"id": "Ind3", "yield": 50.0}
        ],
        "markers": [
            {"id": "Ind1", "genotypes": [1, 1, 1, 1, 1]},
            {"id": "Ind2", "genotypes": [1, 1, 1, 1, 1]},
            {"id": "Ind3", "genotypes": [0, 0, 0, 0, 0]}
        ],
        "trait": "yield",
        "heritability": 0.5
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                result = data["data"]
                bvs = result["breeding_values"]
                
                print("✅ GBLUP Analysis Successful")
                print(f"   Genetic Variance: {result['genetic_variance']}")
                print(f"   Residual Variance: {result['residual_variance']}")
                
                print("\n   Breeding Values:")
                for bv in bvs:
                    print(f"   - {bv['individual_id']}: GEBV={bv['gebv']}, Reliability={bv['reliability']}")
                    
                # Verification Logic
                gebv_map = {bv['individual_id']: bv['gebv'] for bv in bvs}
                
                if gebv_map['Ind1'] > 0 and gebv_map['Ind3'] < 0:
                     print("✅ Directionality correct (High yield > 0, Low yield < 0)")
                else:
                     print("⚠️ Directionality suspicious")
                     
                if abs(gebv_map['Ind1'] - gebv_map['Ind2']) < 5.0:
                     print("✅ Clones have similar GEBVs")
                else:
                     print("⚠️ Clones divergent")

            else:
                 print(f"❌ API reported failure: {data}")
        else:
             print(f"❌ Request failed: {response.status_code} - {response.text}")
             
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_gblup()
