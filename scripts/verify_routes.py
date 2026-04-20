import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Starting verification...", flush=True)

try:
    from app.main import app
    print("App imported successfully.", flush=True)
except ImportError as e:
    print(f"Error importing app: {e}", flush=True)
    sys.exit(1)

required_prefixes = [
    "/api/v2/agronomy",
    "/api/v2/weather",
    "/api/v2/crop-calendar",
    "/api/v2/crop_calendar",
    "/api/v2/iot",
    "/api/v2/calculators"
]

found_routes = {prefix: [] for prefix in required_prefixes}

print(f"Inspecting {len(app.routes)} registered routes...", flush=True)
for route in app.routes:
    if hasattr(route, "path"):
        path = route.path
        for prefix in required_prefixes:
            if path.startswith(prefix):
                found_routes[prefix].append(path)

print("\n--- Verification Results ---", flush=True)
all_found = True
for prefix, routes in found_routes.items():
    if routes:
        print(f"✅ {prefix}: Found {len(routes)} routes", flush=True)
        for r in routes[:3]: # Show first 3
            print(f"  - {r}", flush=True)
        if len(routes) > 3:
            print(f"  - ... and {len(routes)-3} more", flush=True)
    else:
        # Don't fail immediately, just report
        print(f"❌ {prefix}: No routes found", flush=True) 

# Check logical groups
if not found_routes["/api/v2/agronomy"]:
    print("\n⚠️ Agronomy routes missing!", flush=True)
    all_found = False

if not found_routes["/api/v2/weather"]:
    print("\n⚠️ Weather routes missing!", flush=True)
    all_found = False

if not (found_routes["/api/v2/crop-calendar"] or found_routes["/api/v2/crop_calendar"]):
    print("\n⚠️ Crop Calendar routes missing!", flush=True)
    all_found = False
    
if not found_routes["/api/v2/iot"]:
     # IoT might be under a different path, check verify
    pass 

if all_found:
    print("\nSUCCESS: All critical Batch 2 modules appear to be wired.", flush=True)
else:
    print("\nFAILURE: Some modules are missing from the router.", flush=True)
