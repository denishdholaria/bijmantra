import os
import re
import json
import glob

# Configuration
ROUTES_DIR = 'frontend/src/routes'
OUTPUT_FILE = 'frontend/e2e/tests/visual/routes.json'

def extract_routes():
    routes = set()
    
    # Pattern to match path: '...' or path: "..."
    # Matches: path: '/dashboard'
    pattern = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")
    
    # Get all .tsx files in routes directory
    files = glob.glob(os.path.join(ROUTES_DIR, '*.tsx'))
    
    print(f"Scanning {len(files)} files in {ROUTES_DIR}...")
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = pattern.findall(content)
                for match in matches:
                    # Filter out dynamic routes (containing :) and wildcards (*)
                    if ':' not in match and '*' not in match:
                        routes.add(match)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Sort routes for consistency
    sorted_routes = sorted(list(routes))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_routes, f, indent=2)
        
    print(f"Successfully wrote {len(sorted_routes)} static routes to {OUTPUT_FILE}")
    # Print first few for verification
    print("Sample routes:", sorted_routes[:5])

if __name__ == '__main__':
    # Adjust CWD to project root if running from script location
    if os.path.basename(os.getcwd()) == 'scripts':
        os.chdir('../..')
        
    extract_routes()
