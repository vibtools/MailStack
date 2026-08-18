#!/usr/bin/env python3
"""Verify and safely stage a deterministic MailStack source archive for upgrade."""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-rc\.(?P<rc>0|[1-9]\d*))?$"
)
PACKAGE_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:rc(?P<rc>0|[1-9]\d*))?$"
)
MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")
CANONICAL_ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
CANONICAL_ZIP_CREATE_SYSTEM = 3
CANONICAL_ZIP_VERSION = 20
BLOCKED_NAMES = {".env", ".coverage", "id_rsa", "id_ed25519", "credentials.json"}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db", ".log", ".bak"}
REQUIRED_MEMBERS = {
    "VERSION",
    "mailbox-app/manage.py",
    "mailbox-app/pyproject.toml",
    "mailbox-app/requirements/production.txt",
    "mailbox-app/scripts/verify_application.sh",
    "mailbox-app/scripts/upgrade.sh",
    "mailbox-app/scripts/rollback_upgrade.sh",
    "public-site/requirements.txt",
    "public-site/site-template/index.html",
    "scripts/render_public_site.py",
}


class UpgradeArchiveError(RuntimeError):
    """Raised when a target release cannot be proven safe for staging."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalized_version(value: str, *, package: bool = False) -> tuple[str, tuple[int, int, int, int, int]]:
    pattern = PACKAGE_PATTERN if package else VERSION_PATTERN
    match = pattern.fullmatch(value.strip())
    if not match:
        kind = "package version" if package else "VERSION"
        raise UpgradeArchiveError(f"unsupported {kind}: {value!r}")
    major, minor, patch = (int(match.group(name)) for name in ("major", "minor", "patch"))
    rc_text = match.group("rc")
    stable_rank = 1 if rc_text is None else 0
    rc = 0 if rc_text is None else int(rc_text)
    canonical = f"{major}.{minor}.{patch}" + (f"-rc.{rc}" if rc_text is not None else "")
    return canonical, (major, minor, patch, stable_rank, rc)


def package_from_release(version: str) -> str:
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        raise UpgradeArchiveError(f"unsupported VERSION: {version!r}")
    base = f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
    rc = match.group("rc")
    return f"{base}rc{rc}" if rc is not None else base


def read_current_version(app_root: Path) -> str:
    pyproject = app_root / "pyproject.toml"
    if not pyproject.is_file():
        raise UpgradeArchiveError(f"current application pyproject is missing: {pyproject}")
    try:
        package_version = str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise UpgradeArchiveError(f"unable to read current project.version: {exc}") from exc
    canonical, _ = normalized_version(package_version, package=True)
    return canonical


def read_checksum(checksum_path: Path, archive: Path) -> str:
    fields = checksum_path.read_text(encoding="utf-8").split()
    if len(fields) != 2:
        raise UpgradeArchiveError("checksum file must contain exactly one SHA-256 and filename")
    expected, filename = fields
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise UpgradeArchiveError("checksum file does not contain a valid SHA-256")
    if filename.lstrip("*") != archive.name:
        raise UpgradeArchiveError("checksum filename does not match target archive")
    return expected.lower()


def verify_archive(
    archive_path: Path,
    checksum_path: Path,
) -> tuple[zipfile.ZipFile, str, str, dict[str, str]]:
    expected = read_checksum(checksum_path, archive_path)
    actual = sha256(archive_path)
    if actual != expected:
        raise UpgradeArchiveError(f"archive checksum mismatch: expected {expected}, got {actual}")

    archive = zipfile.ZipFile(archive_path)
    bad = archive.testzip()
    if bad is not None:
        archive.close()
        raise UpgradeArchiveError(f"ZIP integrity failure: {bad}")
    if archive.comment:
        archive.close()
        raise UpgradeArchiveError("release archive comment must be empty")

    infos = archive.infolist()
    names = [info.filename for info in infos]
    if not names or len(names) != len(set(names)):
        archive.close()
        raise UpgradeArchiveError("release ZIP is empty or contains duplicate members")
    top_levels = {PurePosixPath(name).parts[0] for name in names}
    if len(top_levels) != 1:
        archive.close()
        raise UpgradeArchiveError("release must contain exactly one top-level directory")
    top_level = next(iter(top_levels))
    prefix = top_level + "/"

    for info in infos:
        pure = PurePosixPath(info.filename)
        if pure.is_absolute() or ".." in pure.parts or "" in pure.parts:
            archive.close()
            raise UpgradeArchiveError(f"unsafe ZIP member: {info.filename}")
        if pure.name in BLOCKED_NAMES or pure.suffix.lower() in BLOCKED_SUFFIXES:
            archive.close()
            raise UpgradeArchiveError(f"blocked file in release: {info.filename}")
        if info.is_dir():
            continue
        if info.date_time != CANONICAL_ZIP_TIMESTAMP:
            archive.close()
            raise UpgradeArchiveError(f"non-canonical ZIP timestamp: {info.filename}")
        if info.create_system != CANONICAL_ZIP_CREATE_SYSTEM:
            archive.close()
            raise UpgradeArchiveError(f"non-canonical ZIP host metadata: {info.filename}")
        if (
            info.create_version != CANONICAL_ZIP_VERSION
            or info.extract_version != CANONICAL_ZIP_VERSION
            or info.reserved != 0
            or info.flag_bits != 0
            or info.volume != 0
            or info.internal_attr != 0
            or info.compress_type != zipfile.ZIP_STORED
            or info.extra
            or info.comment
        ):
            archive.close()
            raise UpgradeArchiveError(f"non-canonical ZIP member metadata: {info.filename}")
        expected_mode = 0o755 if pure.name == "install.sh" or pure.suffix == ".sh" else 0o644
        actual_mode = (info.external_attr >> 16) & 0o777
        if actual_mode != expected_mode:
            archive.close()
            raise UpgradeArchiveError(f"non-canonical ZIP mode: {info.filename}: {oct(actual_mode)}")

    manifest_name = prefix + "SOURCE_MANIFEST.sha256"
    if manifest_name not in names:
        archive.close()
        raise UpgradeArchiveError("source manifest missing")
    expected_members: dict[str, str] = {}
    manifest_text = archive.read(manifest_name).decode("utf-8")
    for number, line in enumerate(manifest_text.splitlines(), start=1):
        match = MANIFEST_LINE.fullmatch(line)
        if not match:
            archive.close()
            raise UpgradeArchiveError(f"invalid source-manifest line {number}")
        expected_hash, relative = match.groups()
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or relative == "SOURCE_MANIFEST.sha256":
            archive.close()
            raise UpgradeArchiveError(f"unsafe source-manifest path: {relative}")
        member = prefix + relative
        if member in expected_members:
            archive.close()
            raise UpgradeArchiveError(f"duplicate source-manifest path: {relative}")
        expected_members[member] = expected_hash

    actual_members = {name for name in names if not name.endswith("/") and name != manifest_name}
    if set(expected_members) != actual_members:
        archive.close()
        raise UpgradeArchiveError("source manifest does not match archive member set")
    for member, expected_hash in expected_members.items():
        if sha256_bytes(archive.read(member)) != expected_hash:
            archive.close()
            raise UpgradeArchiveError(f"source-manifest hash mismatch: {member.removeprefix(prefix)}")

    missing = sorted(relative for relative in REQUIRED_MEMBERS if prefix + relative not in actual_members)
    if missing:
        archive.close()
        raise UpgradeArchiveError(f"release is missing upgrade-required members: {missing}")
    return archive, prefix, actual, expected_members


def migration_map_from_current(app_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    apps_root = app_root / "apps"
    if not apps_root.is_dir():
        raise UpgradeArchiveError(f"current application apps directory is missing: {apps_root}")
    for path in sorted(apps_root.glob("*/migrations/[0-9]*.py")):
        relative = path.relative_to(app_root).as_posix()
        result[relative] = sha256(path)
    return result


def migration_map_from_archive(archive: zipfile.ZipFile, prefix: str) -> dict[str, str]:
    marker = prefix + "mailbox-app/"
    result: dict[str, str] = {}
    for info in archive.infolist():
        name = info.filename
        if not name.startswith(marker) or info.is_dir():
            continue
        relative = name.removeprefix(marker)
        pure = PurePosixPath(relative)
        if (
            len(pure.parts) == 4
            and pure.parts[0] == "apps"
            and pure.parts[2] == "migrations"
            and re.fullmatch(r"[0-9].*\.py", pure.name)
        ):
            result[relative] = sha256_bytes(archive.read(name))
    return result


def compare_migrations(
    current: dict[str, str],
    target: dict[str, str],
) -> tuple[list[str], list[str], list[str]]:
    added = sorted(set(target) - set(current))
    removed = sorted(set(current) - set(target))
    modified = sorted(path for path in set(current) & set(target) if current[path] != target[path])
    return added, removed, modified


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise UpgradeArchiveError(f"extract destination is not empty: {destination}")
    top_level = PurePosixPath(archive.infolist()[0].filename).parts[0]
    for info in archive.infolist():
        if info.is_dir():
            continue
        target = destination.joinpath(*PurePosixPath(info.filename).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
        mode = (info.external_attr >> 16) & 0o777
        target.chmod(mode)
    return destination / top_level


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checksum", type=Path, required=True)
    parser.add_argument("--current-app", type=Path, required=True)
    parser.add_argument("--extract-to", type=Path, required=True)
    args = parser.parse_args()

    archive_path = args.archive.resolve(strict=True)
    checksum_path = args.checksum.resolve(strict=True)
    app_root = args.current_app.resolve(strict=True)
    destination = args.extract_to.resolve()

    try:
        current_version = read_current_version(app_root)
        _, current_order = normalized_version(current_version)
        archive, prefix, archive_sha, _ = verify_archive(archive_path, checksum_path)
        try:
            version_text = archive.read(prefix + "VERSION").decode("utf-8").strip()
            target_version, target_order = normalized_version(version_text)
            pyproject = tomllib.loads(archive.read(prefix + "mailbox-app/pyproject.toml").decode("utf-8"))
            package_version = str(pyproject["project"]["version"])
            if package_version != package_from_release(target_version):
                raise UpgradeArchiveError(
                    "target package version mismatch: "
                    f"VERSION={target_version}, project.version={package_version}"
                )
            if target_order <= current_order:
                raise UpgradeArchiveError(
                    "target version must be newer than current version: "
                    f"current={current_version}, target={target_version}"
                )

            current_migrations = migration_map_from_current(app_root)
            target_migrations = migration_map_from_archive(archive, prefix)
            added, removed, modified = compare_migrations(current_migrations, target_migrations)
            if removed:
                raise UpgradeArchiveError(f"target removes existing migration files: {removed}")
            if modified:
                raise UpgradeArchiveError(f"target modifies existing migration files: {modified}")

            target_root = safe_extract(archive, destination)
        finally:
            archive.close()

        print(f"CURRENT_VERSION={current_version}")
        print(f"TARGET_VERSION={target_version}")
        print(f"TARGET_ROOT={target_root}")
        print(f"UPGRADE_ARCHIVE_SHA256={archive_sha}")
        print(f"NEW_MIGRATIONS={len(added)}")
        for migration in added:
            print(f"NEW_MIGRATION={migration}")
        print("UPGRADE_ARCHIVE_VERIFY=PASS")
        return 0
    except (OSError, KeyError, TypeError, UnicodeDecodeError, zipfile.BadZipFile, UpgradeArchiveError) as exc:
        print(f"UPGRADE_ARCHIVE_FINDING={exc}")
        print("UPGRADE_ARCHIVE_VERIFY=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
