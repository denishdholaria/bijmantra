import os
import re

directories_to_scan = ['.']
ignore_dirs = {'.git', 'node_modules', '.venv', '.vscode', '.agent', 'venv', 'dist', 'build', '__pycache__'}

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return
        
    original = content
    content = content.replace('gitlab.com/denishdholaria/bijmantraorg', 'gitlab.com/denishdholaria/bijmantraorg')
    content = content.replace('gitlab.com/denishdholaria/bijmantraorg', 'gitlab.com/denishdholaria/bijmantraorg')
    content = content.replace('gitlab', 'gitlab') # shield github to gitlab etc could be complex
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        if file.endswith(('.md', '.py', '.ts', '.tsx', '.sh', '.txt', '.yml', '.yaml', '.json')):
            filepath = os.path.join(root, file)
            replace_in_file(filepath)
