#!/usr/bin/env python3
"""Non-destructive contract tests for the generic MailStack upgrade/rollback mechanism."""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from shell_runtime import bash_syntax_command, resolve_bash

ROOT = Path(__file__).resolve().parents[1]
APP_SCRIPTS = ROOT / "mailbox-app/scripts"
CANONICAL_TIME = (2026, 1, 1, 0, 0, 0)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_shell(name: str) -> str:
    path = APP_SCRIPTS / name
    require(path.is_file(), f"missing upgrade script: {name}")
    result = subprocess.run(bash_syntax_command(path, cwd=ROOT), capture_output=True, text=True)
    require(result.returncode == 0, result.stdout + result.stderr)
    return path.read_text(encoding="utf-8")


def load_verifier():
    path = APP_SCRIPTS / "verify_upgrade_archive.py"
    require(path.is_file(), "missing upgrade archive verifier")
    spec = importlib.util.spec_from_file_location("mailstack_verify_upgrade_archive", path)
    require(spec is not None and spec.loader is not None, "unable to load upgrade verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=CANONICAL_TIME)
    info.create_system = 3
    info.create_version = 20
    info.extract_version = 20
    info.reserved = 0
    info.flag_bits = 0
    info.volume = 0
    info.internal_attr = 0
    info.compress_type = zipfile.ZIP_STORED
    info.extra = b""
    info.comment = b""
    mode = 0o755 if Path(name).suffix == ".sh" or Path(name).name == "install.sh" else 0o644
    info.external_attr = mode << 16
    archive.writestr(info, data)


def build_fixture_archive(temp: Path) -> tuple[Path, Path, Path]:
    current = temp / "current-app"
    (current / "apps/core/migrations").mkdir(parents=True)
    (current / "pyproject.toml").write_text('[project]\nname="mailstack"\nversion="1.3.0rc5"\n', encoding="utf-8")
    migration_v1 = b"# migration one\n"
    (current / "apps/core/migrations/0001_initial.py").write_bytes(migration_v1)

    prefix = "mailstack-1.3.0-rc.6/"
    files: dict[str, bytes] = {
        "VERSION": b"1.3.0-rc.6\n",
        "mailbox-app/manage.py": b"#!/usr/bin/env python3\n",
        "mailbox-app/pyproject.toml": b'[project]\nname="mailstack"\nversion="1.3.0rc6"\n',
        "mailbox-app/requirements/production.txt": b"Django==5.2.16\n",
        "mailbox-app/scripts/verify_application.sh": b"#!/usr/bin/env bash\nset -Eeuo pipefail\n",
        "mailbox-app/scripts/upgrade.sh": b"#!/usr/bin/env bash\nset -Eeuo pipefail\n",
        "mailbox-app/scripts/rollback_upgrade.sh": b"#!/usr/bin/env bash\nset -Eeuo pipefail\n",
        "mailbox-app/apps/core/migrations/0001_initial.py": migration_v1,
        "mailbox-app/apps/core/migrations/0002_upgrade.py": b"# migration two\n",
        "public-site/requirements.txt": b"\n",
        "public-site/site-template/index.html": b"<!doctype html>\n",
        "scripts/render_public_site.py": b"#!/usr/bin/env python3\n",
    }
    manifest = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())
    ).encode("utf-8")
    archive_path = temp / "mailstack-1.3.0-rc.6-source.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.comment = b""
        for name, data in sorted(files.items()):
            add_member(archive, prefix + name, data)
        add_member(archive, prefix + "SOURCE_MANIFEST.sha256", manifest)
    checksum = temp / (archive_path.name + ".sha256")
    checksum.write_text(
        f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {archive_path.name}\n",
        encoding="utf-8",
    )
    return current, archive_path, checksum


def main() -> int:
    print(f"BASH_RUNTIME={resolve_bash()}")
    upgrade = read_shell("upgrade.sh")
    rollback = read_shell("rollback_upgrade.sh")
    verifier_text = (APP_SCRIPTS / "verify_upgrade_archive.py").read_text(encoding="utf-8")
    module = load_verifier()

    for name, text in {"upgrade.sh": upgrade, "rollback_upgrade.sh": rollback}.items():
        require("set -Eeuo pipefail" in text, f"{name} is not fail-closed")
        require("flock -n" in text, f"{name} does not use a non-blocking runtime lock")

    for fragment in (
        "--archive",
        "--checksum",
        "--confirm-upgrade",
        "--allow-migrations",
        "verify_upgrade_archive.py",
        'BACKUP_ROOT="$DATA_ROOT"',
        '"$APP_ROOT/scripts/backup.sh"',
        "sha256sum --check SHA256SUMS",
        "MIGRATION_RISK=1",
        "MANUAL_SCHEMA_RECONCILIATION_REQUIRED",
        "rsync -a --delete-delay",
        '"$VENV/bin/pip" install --requirement',
        "manage.py migrate --noinput",
        "manage.py verify_mailserver_schema",
        "manage.py verify_mail_storage",
        "manage.py verify_postfix_contract",
        "manage.py collectstatic --noinput",
        "INBOUND_CONTINUITY=POSTFIX_DOVECOT_LEFT_ACTIVE_DURING_SOURCE_MUTATION",
        "systemctl stop vibmail-public-contact.service vibmail-ingestion.service vibmail-gunicorn.service",
        'systemctl is-active --quiet postfix.service',
        'systemctl is-active --quiet dovecot.service',
        "MAILSTACK_UPGRADE=PASS",
    ):
        require(fragment in upgrade, f"upgrade contract missing: {fragment}")
    require("systemctl stop postfix" not in upgrade, "upgrade mutation must not directly stop Postfix")
    require("systemctl stop dovecot" not in upgrade, "upgrade mutation must not directly stop Dovecot")

    for fragment in (
        "/var/backups/vibmail/upgrades/*",
        "sha256sum --check SHA256SUMS",
        "validate_tar_archive",
        "--accept-forward-schema",
        "ROLLBACK_DATABASE_ACTION=NOT_PERFORMED",
        "MAILSTACK_ROLLBACK=PASS",
        '"$VENV/bin/pip" install --requirement',
        "manage.py collectstatic --noinput",
        '"$APP_ROOT/scripts/verify_application.sh"',
    ):
        require(fragment in rollback, f"rollback contract missing: {fragment}")

    for fragment in (
        "SOURCE_MANIFEST.sha256",
        "CANONICAL_ZIP_TIMESTAMP",
        "checksum filename does not match target archive",
        "target version must be newer than current version",
        "target removes existing migration files",
        "target modifies existing migration files",
        "source-manifest hash mismatch",
        "safe_extract",
    ):
        require(fragment in verifier_text, f"upgrade archive verification contract missing: {fragment}")

    stable, stable_order = module.normalized_version("1.3.0")
    rc, rc_order = module.normalized_version("1.3.0-rc.5")
    require(stable == "1.3.0" and rc == "1.3.0-rc.5", "version normalization failed")
    require(stable_order > rc_order, "stable release must sort after RC of the same base version")
    added, removed, modified = module.compare_migrations(
        {"apps/core/migrations/0001.py": "a"},
        {"apps/core/migrations/0001.py": "a", "apps/core/migrations/0002.py": "b"},
    )
    require(added == ["apps/core/migrations/0002.py"] and not removed and not modified, "migration comparison failed")

    with tempfile.TemporaryDirectory(prefix="mailstack-upgrade-test-") as temp_name:
        temp = Path(temp_name)
        current, archive, checksum = build_fixture_archive(temp)
        extract_to = temp / "stage"
        result = subprocess.run(
            [
                sys.executable,
                str(APP_SCRIPTS / "verify_upgrade_archive.py"),
                "--archive",
                str(archive),
                "--checksum",
                str(checksum),
                "--current-app",
                str(current),
                "--extract-to",
                str(extract_to),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        require(result.returncode == 0, result.stdout + result.stderr)
        require("CURRENT_VERSION=1.3.0-rc.5" in result.stdout, "fixture current version was not detected")
        require("TARGET_VERSION=1.3.0-rc.6" in result.stdout, "fixture target version was not detected")
        require("NEW_MIGRATIONS=1" in result.stdout, "fixture migration delta was not detected")
        require("UPGRADE_ARCHIVE_VERIFY=PASS" in result.stdout, "fixture archive did not verify")
        require((extract_to / "mailstack-1.3.0-rc.6/mailbox-app/manage.py").is_file(), "verified archive was not staged")

        checksum.write_text("0" * 64 + f"  {archive.name}\n", encoding="utf-8")
        bad = subprocess.run(
            [
                sys.executable,
                str(APP_SCRIPTS / "verify_upgrade_archive.py"),
                "--archive",
                str(archive),
                "--checksum",
                str(checksum),
                "--current-app",
                str(current),
                "--extract-to",
                str(temp / "bad-stage"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        require(bad.returncode != 0 and "UPGRADE_ARCHIVE_VERIFY=FAIL" in bad.stdout, "bad checksum did not fail closed")

    print("UPGRADE_ARCHIVE_CONTRACT=PASS")
    print("UPGRADE_MIGRATION_GATE=PASS")
    print("UPGRADE_ROLLBACK_CONTRACT=PASS")
    print("UPGRADE_TESTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
