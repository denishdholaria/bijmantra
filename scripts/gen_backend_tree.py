"""Generate a folder/file tree of the backend directory."""
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent

# Collect files from core backend dirs
result = subprocess.run(
    [
        "find",
        "backend/app",
        "backend/tests",
        "backend/alembic",
        "-not", "-path", "*/__pycache__/*",
        "-not", "-name", "*.pyc",
        "-not", "-name", ".DS_Store",
    ],
    capture_output=True,
    text=True,
    cwd=REPO,
)

# Root-level backend files
root_result = subprocess.run(
    [
        "find", "backend", "-maxdepth", "1", "-type", "f",
        "-not", "-name", ".DS_Store",
        "-not", "-name", ".env",
        "-not", "-name", "uv.lock",
    ],
    capture_output=True,
    text=True,
    cwd=REPO,
)

all_paths = sorted(set(
    [p for p in result.stdout.strip().split("\n") if p]
    + [p for p in root_result.stdout.strip().split("\n") if p]
))

# Build nested dict tree
tree = {}
for f in all_paths:
    parts = Path(f).parts
    node = tree
    for part in parts:
        node = node.setdefault(part, {})


def render(node, prefix="", is_last=True, name=""):
    lines = []
    if name:
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + name)
        prefix += "    " if is_last else "│   "
    # dirs first (non-empty dicts), then files, both alphabetical
    children = sorted(node.keys(), key=lambda x: (not bool(node[x]), x.lower()))
    for i, child in enumerate(children):
        last = i == len(children) - 1
        lines.extend(render(node[child], prefix, last, child))
    return lines


tree_lines = render(tree)

file_count = sum(1 for p in all_paths if Path(REPO / p).is_file())
dir_count = len(set(str(Path(p).parent) for p in all_paths))

output_path = REPO / "public-docs" / "backend-file-tree.md"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as f:
    f.write("# Backend File Tree\n\n")
    f.write(f"Generated from `backend/` — {file_count} files across {dir_count} directories.\n\n")
    f.write("```\n")
    f.write("\n".join(tree_lines))
    f.write("\n```\n")

print(f"Written: {len(tree_lines)} lines, {file_count} files, {dir_count} dirs")
print(f"Output: {output_path}")
