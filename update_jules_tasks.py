import os

DIRECTORY = "/Volumes/ai/PlantBreedingAPP/bijmantra/.Jules/CEO"

DIRECTIVES = """
> [!IMPORTANT] 
> **OS ARCHITECTURE COMPLIANCE**
> This task must be executed within the "Agricultural Linux" OS Architecture:
> 1. **Strict Workspace Isolation**: All UI components must verify `useActiveWorkspace()`.
> 2. **Contextual Navigation**: Do NOT add global links. Register pages strictly within their specific Workspace (e.g., Breeding, Genebank).
> 3. **Backend Modularity**: Do NOT modify `main.py`. Use domain-level router aggregation in `app/api/v2/`.

"""

count = 0
for filename in os.listdir(DIRECTORY):
    if filename.endswith(".md"):
        filepath = os.path.join(DIRECTORY, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        # Check if already applied to avoid duplication
        if "OS ARCHITECTURE COMPLIANCE" in content:
            continue

        # Inset after the H1 title
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            lines.insert(1, DIRECTIVES)
            new_content = "\n".join(lines)
            
            with open(filepath, "w") as f:
                f.write(new_content)
            count += 1
            print(f"Updated {filename}")

print(f"Total files updated: {count}")
