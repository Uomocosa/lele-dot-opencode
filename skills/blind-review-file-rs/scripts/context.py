#!/usr/bin/env python3
"""Round-2 context for a blind review: definitions of the crate types a file uses,
plus the method bodies behind any `#[atomic_delegates]` / `#[atomic_delegate(T)]` shell.

usage: context.py FILE [--crate DIR]   (DIR defaults to the nearest ancestor with Cargo.toml)

Needs `ast-grep` on PATH. Prints markdown to stdout.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RULE = """id: defs
language: rust
rule:
  any:
    - kind: struct_item
    - kind: enum_item
    - kind: type_item
    - kind: trait_item
  not:
    inside:
      kind: impl_item
      stopBy: end
"""
NAME = re.compile(r"\b(?:struct|enum|type|trait)\s+([A-Za-z_]\w*)")
IDENT = re.compile(r"\b([A-Z][A-Za-z0-9]*)\b")
SHELL_IMPL = re.compile(r"#\[atomic_delegates\]\s*impl(?:<[^>]*>)?\s+(?:[\w:]+\s+for\s+)?([\w:]+)")
SHELL_FN = re.compile(r"#\[atomic_delegate\((\w+)\)\]")


def snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


def find_crate(file: Path) -> Path:
    for parent in file.parents:
        if (parent / "Cargo.toml").exists():
            return parent
    sys.exit(f"no Cargo.toml above {file}")


def definitions(crate: Path) -> dict[str, list[tuple[str, str]]]:
    roots = [str(crate / r) for r in ("src", "methods") if (crate / r).is_dir()]
    out = subprocess.run(
        ["ast-grep", "scan", "--inline-rules", RULE, "--json=compact", *roots],
        capture_output=True, text=True,
    )
    if out.returncode not in (0, 1):
        sys.exit(f"ast-grep failed: {out.stderr}")
    index: dict[str, list[tuple[str, str]]] = {}
    for match in json.loads(out.stdout or "[]"):
        name = NAME.search(match["text"])
        if name:
            rel = str(Path(match["file"]).resolve().relative_to(crate))
            index.setdefault(name.group(1), []).append((rel, match["text"]))
    return index


def methods_dir(crate: Path, type_name: str) -> Path | None:
    for base in (crate / "methods", crate / "src" / "methods"):
        candidate = base / snake(type_name)
        if candidate.is_dir():
            return candidate
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("--crate", type=Path)
    args = ap.parse_args()
    file = args.file.resolve()
    crate = (args.crate or find_crate(file)).resolve()
    text = file.read_text()
    rel_self = str(file.relative_to(crate))

    index = definitions(crate)
    used = sorted(set(IDENT.findall(text)))
    print(f"# Context for `{rel_self}`\n\n## Types it uses\n")
    for name in used:
        for path, body in index.get(name, []):
            if path == rel_self:
                continue
            print(f"`{path}`\n```rust\n{body}\n```\n")

    shells = [m.split("::")[-1] for m in SHELL_IMPL.findall(text)] + SHELL_FN.findall(text)
    if shells:
        print("## Delegate bodies\n")
    for type_name in dict.fromkeys(shells):
        folder = methods_dir(crate, type_name)
        if folder is None:
            print(f"(no methods folder found for `{type_name}`)\n")
            continue
        for path in sorted(folder.glob("*.rs")):
            if path.name == "mod.rs":
                continue
            print(f"`{path.relative_to(crate)}`\n```rust\n{path.read_text().rstrip()}\n```\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
