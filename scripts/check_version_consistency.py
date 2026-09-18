#!/usr/bin/env python3
"""Check active release metadata against the canonical VERSION file."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def read_package_version(root: Path) -> str:
    payload = tomllib.loads(
        (root / "mailbox-app" / "pyproject.toml").read_text(encoding="utf-8")
    )
    return str(payload["project"]["version"])


def active_document_versions(root: Path) -> list[tuple[Path, str]]:
    versions: list[tuple[Path, str]] = []
    for path in sorted((root / "documents").rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        if not re.search(r"^status:\s*active\s*$", content, flags=re.MULTILINE):
            continue
        match = re.search(r"^version:\s*([^\r\n]+)$", content, flags=re.MULTILINE)
        if match is None:
            raise ValueError(f"active document has no version: {path}")
        versions.append((path, match.group(1).strip()))
    return versions


def read_json_version(path: Path, key: str) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"missing string {key!r} in {path}")
    return value


def check(root: Path) -> str:
    version = read_version(root)
    values = {
        "VERSION": version,
        "PACKAGE_VERSION": read_package_version(root),
        "DOCUMENTATION_MANIFEST": read_json_version(
            root / "documents" / "DOCUMENTATION_MANIFEST.json", "release_version"
        ),
        "DESIGN_MANIFEST": read_json_version(
            root / "design" / "DESIGN_MANIFEST.json", "release_version"
        ),
    }
    mismatches = [f"{name}={value}" for name, value in values.items() if value != version]
    mismatches.extend(
        f"{path.relative_to(root).as_posix()}={document_version}"
        for path, document_version in active_document_versions(root)
        if document_version != version
    )
    if mismatches:
        raise ValueError("version metadata mismatch: " + ", ".join(mismatches))
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        version = check(args.root.resolve())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"VERSION_CONSISTENCY_ERROR={exc}", file=sys.stderr)
        return 1
    print(f"VERSION_SOURCE={version}")
    print("ACTIVE_METADATA=PASS")
    print("VERSION_CONSISTENCY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
