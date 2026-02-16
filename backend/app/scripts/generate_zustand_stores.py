"""Experimental: generate Zustand store typings from Pydantic schema names."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_ROOT = ROOT / "backend" / "app" / "schemas"
OUT = ROOT / "frontend" / "src" / "stores" / "autogen"


def iter_schema_names() -> list[str]:
    names: list[str] = []
    for py_file in SCHEMA_ROOT.rglob("*.py"):
        for line in py_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("class ") and "BaseModel" in line:
                names.append(line.split("class ", 1)[1].split("(", 1)[0].strip())
    return sorted(set(names))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in iter_schema_names():
        file_path = OUT / f"use{name}Store.ts"
        file_path.write_text(
            "\n".join(
                [
                    "import { create } from 'zustand';",
                    "",
                    f"type {name}State = {{",
                    "  data: Record<string, unknown> | null;",
                    "  setData: (data: Record<string, unknown>) => void;",
                    "};",
                    "",
                    f"export const use{name}Store = create<{name}State>((set) => ({{",
                    "  data: null,",
                    "  setData: (data) => set({ data }),",
                    "}));",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    print(f"Generated stores in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
