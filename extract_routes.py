import glob
import re
import json
import os

def extract_routes():
    route_files = glob.glob("frontend/src/routes/*.tsx")
    routes = []

    # Regex to find: { path: '/some/path', ... }
    # Handles simple quotes and varying spacing
    path_pattern = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")

    print(f"🔍 Scanning {len(route_files)} route files...")

    for file_path in route_files:
        with open(file_path, 'r') as f:
            content = f.read()
            matches = path_pattern.findall(content)
            for match in matches:
                # Filter out wildcards or params for now if simple check is desired
                # Or keep them and instructing test to use default IDs
                if '*' in match:
                    continue

                # Replace dynamic params with dummy ID '1' for testing
                # e.g., /people/:id -> /people/1
                clean_path = re.sub(r':[a-zA-Z0-9_]+', '1', match)

                if clean_path not in routes:
                    routes.append(clean_path)

    # Sort for consistent testing
    routes.sort()

    output_path = "frontend/e2e/all_routes.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(routes, f, indent=2)

    print(f"✅ Extracted {len(routes)} unique routes to {output_path}")

if __name__ == "__main__":
    extract_routes()
