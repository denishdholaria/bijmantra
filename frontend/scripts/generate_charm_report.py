import os
import glob
from datetime import datetime

# Configuration
SCREENSHOTS_DIR = 'frontend/e2e/charm-screenshots'
REPORT_FILE = 'CHARM_REPORT.md'

def generate_report():
    print(f"Generating report from {SCREENSHOTS_DIR}...")
    
    # Get all png files
    fs = glob.glob(os.path.join(SCREENSHOTS_DIR, '*.png'))
    if not fs:
        print("No screenshots found!")
        return

    # Sort files
    files = sorted(fs)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Charm Check Report\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Pages Scanned:** {len(files)}\n\n")
        
        f.write("| Page | Screenshot |\n")
        f.write("|------|------------|\n")
        
        for file_path in files:
            filename = os.path.basename(file_path)
            # Route name from filename (remove extension and replace _ with /)
            route = filename.replace('.png', '').replace('_', '/')
            if not route.startswith('/'):
                route = '/' + route
                
            # Relative path for markdown image
            rel_path = os.path.join(SCREENSHOTS_DIR, filename)
            
            f.write(f"| `{route}` | ![{route}]({rel_path}) |\n")
            
    print(f"Successfully wrote report to {REPORT_FILE}")

if __name__ == '__main__':
    # Adjust CWD to project root if running from script location
    if os.path.basename(os.getcwd()) == 'scripts':
        os.chdir('../..')
        
    generate_report()
