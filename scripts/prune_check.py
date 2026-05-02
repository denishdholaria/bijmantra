import os
import re

def get_pages():
    pages_dir = 'frontend/src/pages'
    pages = []
    for root, dirs, files in os.walk(pages_dir):
        for file in files:
            if file.endswith('.tsx') and not file.startswith('_'):
                # relative path from pages_dir
                rel_path = os.path.relpath(os.path.join(root, file), pages_dir)
                pages.append(rel_path)
    return pages

def check_usage(pages):
    routes_dir = 'frontend/src/routes'
    used_pages = set()

    # Read all route files
    route_content = ""
    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                with open(os.path.join(root, file), 'r') as f:
                    route_content += f.read()

    # Also check App.tsx and main.tsx just in case
    for extra in ['frontend/src/App.tsx', 'frontend/src/main.tsx']:
        if os.path.exists(extra):
            with open(extra, 'r') as f:
                route_content += f.read()

    unused = []
    for page in pages:
        # Simple check: filename without extension
        page_name = os.path.basename(page).replace('.tsx', '')
        # Check if the component name is used or the file path is imported
        # This is a heuristic
        if page_name not in route_content and page.replace('.tsx', '') not in route_content:
            unused.append(page)

    return unused

if __name__ == '__main__':
    pages = get_pages()
    unused = check_usage(pages)
    print("Found {} pages".format(len(pages)))
    print("Unused pages candidate list:")
    for p in unused:
        print("- " + p)
