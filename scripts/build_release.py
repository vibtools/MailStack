#!/usr/bin/env python3
"""Build and verify a deterministic source release ZIP."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", ".audit-venv", "venv", ".tox", ".nox", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "artifacts"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".gz", ".log", ".sqlite", ".sqlite3", ".db"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def included(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return not any(part in EXCLUDED_PARTS for part in relative.parts) and path.suffix.lower() not in EXCLUDED_SUFFIXES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", default=(Path(__file__).resolve().parents[1] / "VERSION").read_text(encoding="utf-8").strip())
    parser.add_argument("--skip-audit", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not args.skip_audit:
        subprocess.run([sys.executable, str(root / "scripts/forensic_audit.py"), "--root", str(root)], check=True)

    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    package_name = f"mailstack-{args.version}"
    zip_path = dist / f"{package_name}-source.zip"
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")

    with tempfile.TemporaryDirectory(prefix="mailstack-release-") as temp:
        stage = Path(temp) / package_name
        stage.mkdir()
        for source in sorted(root.rglob("*")):
            if not source.is_file() or not included(source, root):
                continue
            relative = source.relative_to(root)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        manifest = stage / "SOURCE_MANIFEST.sha256"
        lines = []
        for path in sorted(stage.rglob("*")):
            if path.is_file() and path != manifest:
                lines.append(f"{digest(path)}  {path.relative_to(stage).as_posix()}")
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        temporary = zip_path.with_suffix(".zip.tmp")
        temporary.unlink(missing_ok=True)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
            for path in sorted(stage.rglob("*")):
                if not path.is_file():
                    continue
                arcname = (Path(package_name) / path.relative_to(stage)).as_posix()
                info = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                mode = 0o755 if path.name == "install.sh" or path.suffix == ".sh" else 0o644
                info.external_attr = mode << 16
                archive.writestr(info, path.read_bytes())
        temporary.replace(zip_path)

    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"corrupt ZIP member: {bad}")
        names = archive.namelist()
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise SystemExit("unsafe ZIP path")

    sha = digest(zip_path)
    checksum_path.write_text(f"{sha}  {zip_path.name}\n", encoding="utf-8")
    print(f"RELEASE_ZIP={zip_path}")
    print(f"RELEASE_SHA256={sha}")
    print(f"RELEASE_SIZE_BYTES={zip_path.stat().st_size}")
    print("RELEASE_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
