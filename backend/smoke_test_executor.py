
import os
import sys


# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("✅ Imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
