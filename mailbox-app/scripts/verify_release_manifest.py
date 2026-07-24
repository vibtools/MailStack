#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".runtime", "staticfiles", "htmlcov"}
IGNORED_FILES = {".coverage", "coverage.json", "coverage.xml", "RELEASE_MANIFEST.json"}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scanned_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(item for item in directories if item not in IGNORED_DIRS)
        current_path = Path(current)
        for directory in directories:
            candidate = current_path / directory
            if candidate.is_symlink():
                raise SystemExit(f"Symlinked directory is forbidden: {candidate.relative_to(root)}")
        for filename in sorted(filenames):
            if filename in IGNORED_FILES or filename.endswith((".pyc", ".pyo")):
                continue
            candidate = current_path / filename
            relative = candidate.relative_to(root).as_posix()
            if candidate.is_symlink() or not candidate.is_file():
                raise SystemExit(f"Unsupported release entry: {relative}")
            result[relative] = candidate
    return result


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {sys.argv[0]} /absolute/release/root")
    root = Path(sys.argv[1]).resolve(strict=True)
    manifest_path = root / "RELEASE_MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("release") != "1.2.1":
        raise SystemExit("Manifest release is not 1.2.1")
    expected = {item["path"]: item for item in data.get("files", [])}
    actual = scanned_files(root)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing or unexpected:
        raise SystemExit(f"Release file-set mismatch; missing={missing}, unexpected={unexpected}")
    for relative, item in expected.items():
        path = actual[relative]
        if path.stat().st_size != int(item["size"]):
            raise SystemExit(f"Release size mismatch: {relative}")
        if digest(path) != item["sha256"]:
            raise SystemExit(f"Release hash mismatch: {relative}")
    print(f"Release manifest verified: {len(actual)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
