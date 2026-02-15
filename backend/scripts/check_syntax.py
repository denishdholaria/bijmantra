import ast, sys
from pathlib import Path

errors = []
for f in sorted(Path("app/api/v2").glob("*.py")):
    try:
        ast.parse(f.read_text())
    except SyntaxError as e:
        errors.append((f.name, e.lineno, str(e)))

if errors:
    for n, l, m in errors:
        print(f"SYNTAX ERROR in {n}:{l}: {m}")
    sys.exit(1)
else:
    print(f"All {len(list(Path('app/api/v2').glob('*.py')))} API files parse successfully ✅")
