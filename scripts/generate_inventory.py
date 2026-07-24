#!/usr/bin/env python3
"""Generate or verify the deterministic forensic file and symbol inventory."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

EXCLUDED_PARTS = {
    ".git", ".venv", ".audit-venv", "venv", ".tox", ".nox", "__pycache__",
    ".pytest_cache", ".ruff_cache", "dist", "artifacts",
}
SELF_PATH = "docs/FORENSIC_FILE_INVENTORY.json"
EXCLUDED_NAMES = {".coverage", "SOURCE_MANIFEST.sha256"}
SHELL_FUNCTION = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{", re.MULTILINE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def python_symbols(text: str) -> dict[str, object]:
    tree = ast.parse(text)
    classes: list[str] = []
    functions: list[str] = []
    methods: list[str] = []
    imports: set[str] = set()
    parents: list[str] = []

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            classes.append(".".join([*parents, node.name]))
            parents.append(node.name)
            self.generic_visit(node)
            parents.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            name = ".".join([*parents, node.name])
            (methods if parents else functions).append(name)
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Import(self, node: ast.Import) -> None:
            imports.update(alias.name for alias in node.names)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                imports.add(node.module)

    Visitor().visit(tree)
    return {
        "classes": sorted(classes),
        "functions": sorted(functions),
        "methods": sorted(methods),
        "imports": sorted(imports),
    }


def build(root: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    total_bytes = total_lines = text_files = binary_files = 0
    python_files = python_classes = python_functions = python_methods = 0
    shell_files = shell_functions = 0

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == SELF_PATH or path.name in EXCLUDED_NAMES or any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in {".zip", ".tar", ".gz"}:
            continue
        data = path.read_bytes()
        entry: dict[str, object] = {
            "path": relative,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        total_bytes += len(data)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            entry["kind"] = "binary"
            binary_files += 1
        else:
            line_count = len(text.splitlines())
            entry.update({"kind": "text", "lines": line_count})
            text_files += 1
            total_lines += line_count
            if path.suffix == ".py":
                symbols = python_symbols(text)
                entry["python"] = symbols
                python_files += 1
                python_classes += len(symbols["classes"])
                python_functions += len(symbols["functions"])
                python_methods += len(symbols["methods"])
            if path.suffix == ".sh" or path.name == "install.sh":
                functions = sorted(set(SHELL_FUNCTION.findall(text)))
                entry["shell_functions"] = functions
                shell_files += 1
                shell_functions += len(functions)
        entries.append(entry)

    return {
        "schema_version": 1,
        "release_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "scope": "All maintained repository files excluding generated archives, caches, build output and this inventory file itself.",
        "self_entry": {"path": SELF_PATH, "hash": "intentionally omitted to avoid recursive self-hashing"},
        "summary": {
            "files": len(entries),
            "text_files": text_files,
            "binary_files": binary_files,
            "total_bytes": total_bytes,
            "total_text_lines": total_lines,
            "python_files": python_files,
            "python_classes": python_classes,
            "python_functions": python_functions,
            "python_methods": python_methods,
            "shell_files": shell_files,
            "shell_functions": shell_functions,
        },
        "files": entries,
    }


def encoded(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or (root / SELF_PATH)
    content = encoded(build(root))
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            print(f"INVENTORY_OUT_OF_DATE={output}")
            return 1
        print(f"INVENTORY_FILE={output}")
        print("FORENSIC_INVENTORY=PASS")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8", newline="\n")
    summary = json.loads(content)["summary"]
    print(f"INVENTORY_FILE={output}")
    print(f"INVENTORY_FILES={summary['files']}")
    print(f"INVENTORY_TEXT_LINES={summary['total_text_lines']}")
    print("FORENSIC_INVENTORY=GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
