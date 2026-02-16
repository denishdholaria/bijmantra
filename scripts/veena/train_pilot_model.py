
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import requests
import onnx

# 1. Generate Mock Data (Drought Resistance)
# Features: [Soil Moisture (%), Temp (C), Humidity (%), Chlorophyll Index]
# Target: 0 (Sensitive), 1 (Resistant)

print("🌱 Generating mock agricultural data...")
X = np.array([
    [10, 35, 20, 0.2], [12, 34, 25, 0.3], [15, 30, 40, 0.5], # Sensitive conditions
    [40, 25, 60, 0.8], [45, 24, 65, 0.9], [35, 28, 55, 0.7], # Resistant conditions
    [11, 36, 18, 0.1], [50, 22, 70, 0.95]
], dtype=np.float32)

y = np.array([0, 0, 0, 1, 1, 1, 0, 1]) # Labels

# 2. Train Model
print("🧠 Training Random Forest Classifier...")
rf = RandomForestClassifier(n_estimators=10, random_state=42)
rf.fit(X, y)

# 3. Convert to ONNX
print("🔄 Converting model to ONNX...")
initial_type = [('float_input', FloatTensorType([None, 4]))]
onnx_model = convert_sklearn(rf, initial_types=initial_type)

# Save locally for reference
with open("drought_resistance.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

# 4. Upload to SurrealDB
# Endpoint: http://localhost:8082/ml/import
# Check connectivity first
print("🚀 Uploading model to SurrealDB (Veena)...")

headers = {
    "Accept": "application/json",
    "NS": "bijmantra",
    "DB": "science",
    # Auth: root:root (default from compose)
    "Authorization": "Basic cm9vdDpyb290" 
}

# Namespace and Database must be created first or passed in headers/query params
# The python requests library doesn't automatically handle NS/DB headers correctly for some Surreal endpoints unless specified in the URL or if the DB exists.
# Let's try creating the NS/DB first via SQL, then upload.

# 4a. Create NS/DB
# 4a. Create NS/DB
sql_url = "http://localhost:8082/sql"
init_sql = "DEFINE NAMESPACE bijmantra; DEFINE DATABASE science;"
try:
    print(f"🛠 Creating Namespace and Database via {sql_url}...")
    # Use Basic Auth explicitly
    resp = requests.post(sql_url, data=init_sql, headers=headers)
    print(f"Creation response: {resp.status_code} {resp.text}")
    if resp.status_code != 200:
        print("⚠️ Warning: Failed to create NS/DB via SQL. Proceeding anyway...")
except Exception as e:
    print(f"⚠️ Error creating NS/DB: {e}")

# 4b. Upload Model
# Function name in DB will be 'drought_resistance'
# Version will be '0.0.1'
url = "http://localhost:8082/ml/import"

# Construct .surml file manually since library installation is tricky in this env
# Format is loosely: Header (JSON) + 0x00 delimiter + ONNX Bytes? 
# or just raw bytes if simpler endpoint is used.
# Actually, the /ml/import endpoint expects a .surml file in the body.
# Let's try to simulate a basic surml file structure.
# Based on reverse engineering or docs:
import struct
import json

# Header structure for SurrealML
header = {
    "name": "drought_resistance",
    "version": "0.0.1",
    "description": "Random Forest Classifier for Drought Resistance",
    "inputs": [
        {"name": "soil_moisture", "type": "float", "shape": [1]},
        {"name": "temperature", "type": "float", "shape": [1]},
        {"name": "humidity", "type": "float", "shape": [1]},
        {"name": "chlorophyll_index", "type": "float", "shape": [1]}
    ],
    "outputs": [
        {"name": "is_resistant", "type": "float", "shape": [1]}
    ]
}

# The actual format is likely complex (msgpack or similar).
# Strategy B: Use the raw SQL import if possible, or try the 'surreal import' with the surml file.
# BUT we can't generate the .surml file without the library.
# Let's try to install the library again but ignore dependencies or use a virtualenv.
# OR use the 'surreal' CLI in the container to generate it if possible? No, CLI is for import/export.
# 
# Wait, let's look at the `surrealml` python library documentation or source if available.
# Since installation failed, let's try to install a compatible version or just force it.
# 
# RETRYING TO INSTALL surrealml with --no-deps to avoid destroying numpy
try:
    import surrealml
except ImportError:
    print("⚠️  surrealml library not found. Launching subprocess to install it in isolation...")
    import subprocess
    import sys
    # Install into user site or venv with no deps to avoid conflict
    subprocess.check_call([sys.executable, "-m", "pip", "install", "surrealml", "--no-deps"])

try:
    from surrealml import SurMlFile
    from surrealml.engine import Engine
    print("✅ surrealml library loaded")
    
    # Create SurMlFile using Engine.SKLEARN
    # We pass the fitted sklearn model directly, and sample input X for type inference
    print("📦 Packaging sklearn model into .surml format (using Engine.SKLEARN)...")
    # Note: inputs=X works because skl2onnx.to_onnx accepts sample input
    model_file = SurMlFile(model=rf, name="drought_resistance", inputs=X, engine=Engine.SKLEARN)
    model_file.save("./drought_resistance.surml")
    
    # Now upload the .surml file
    print("📡 Uploading .surml file to SurrealDB using library...")
    
    SurMlFile.upload(
        path="./drought_resistance.surml",
        url="http://localhost:8082", 
        chunk_size=4096,
        namespace="bijmantra",
        database="science",
        username="root",
        password="root"
    )
    print("✅ Model uploaded successfully via SurMlFile.upload!")

except Exception as e:
    print(f"❌ Failed to process/upload model with surrealml: {e}")
    import traceback
    traceback.print_exc()
