#!/usr/bin/env python3
"""Update the canonical release version and its active generated metadata."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(
    r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:\.(?:0|[1-9]\d*))?(?:-rc\.(?:0|[1-9]\d*))?$"
)
PYPROJECT_VERSION = re.compile(r'^(version\s*=\s*")([^"\r\n]+)("\s*)$', re.MULTILINE)
def read_current_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def validate_version(version: str) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"unsupported version format: {version!r}")


def update_package_version(root: Path, version: str) -> None:
    path = root / "mailbox-app" / "pyproject.toml"
    content = path.read_text(encoding="utf-8")
    updated, count = PYPROJECT_VERSION.subn(rf"\g<1>{version}\g<3>", content, count=1)
    if count != 1:
        raise ValueError(f"unable to update project version in {path}")
    path.write_text(updated, encoding="utf-8", newline="\n")


def update_active_document_versions(root: Path, version: str) -> int:
    updated_count = 0
    for path in sorted((root / "documents").rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        if not re.search(r"^status:\s*active\s*$", content, flags=re.MULTILINE):
            continue
        updated, count = re.subn(
            r"^(version:\s*)[^\r\n]+$",
            rf"\g<1>{version}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if count != 1:
            raise ValueError(f"active document has no version metadata: {path}")
        if updated != content:
            path.write_text(updated, encoding="utf-8", newline="\n")
            updated_count += 1
    return updated_count


def update_design_manifest_version(root: Path, version: str) -> None:
    path = root / "design" / "DESIGN_MANIFEST.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["release_version"] = version
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def run_generator(root: Path, script: str) -> None:
    subprocess.run(
        [sys.executable, str(root / "scripts" / script), "--root", str(root), "sync"],
        cwd=root,
        check=True,
    )


def bump(root: Path, version: str) -> None:
    validate_version(version)
    current = read_current_version(root)
    (root / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    update_package_version(root, version)
    updated_documents = update_active_document_versions(root, version)
    update_design_manifest_version(root, version)
    run_generator(root, "manage_documents.py")
    run_generator(root, "manage_designs.py")
    print(f"VERSION_UPDATED={current}->{version}")
    print(f"ACTIVE_DOCUMENTS_UPDATED={updated_documents}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="target release version")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        bump(args.root.resolve(), args.version)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"VERSION_BUMP_ERROR={exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
