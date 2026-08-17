#!/usr/bin/env python3
"""Non-destructive contract tests for backup, restore, health, and verification scripts."""
from __future__ import annotations

import ipaddress
import re
import subprocess
from pathlib import Path

from shell_runtime import bash_syntax_command, resolve_bash

ROOT = Path(__file__).resolve().parents[1]
APP_SCRIPTS = ROOT / "mailbox-app/scripts"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(name: str) -> str:
    path = APP_SCRIPTS / name
    require(path.is_file(), f"missing operational script: {name}")
    result = subprocess.run(bash_syntax_command(path, cwd=ROOT), capture_output=True, text=True)
    require(result.returncode == 0, result.stdout + result.stderr)
    return path.read_text(encoding="utf-8")


def main() -> int:
    print(f"BASH_RUNTIME={resolve_bash()}")
    shell_runtime = (ROOT / "scripts/shell_runtime.py").read_text(encoding="utf-8")
    require("_windows_git_bash_candidates" in shell_runtime, "Git Bash discovery contract is missing")
    require("BASH_EXECUTABLE" in shell_runtime, "Bash runtime override contract is missing")
    require("MAILSTACK_BASH_OK" in shell_runtime, "Bash runtime probe contract is missing")

    backup = read("backup.sh")
    restore = read("restore.sh")
    health = read("health_check.sh")
    verify = read("verify_application.sh")

    for name, text in {
        "backup.sh": backup,
        "restore.sh": restore,
        "health_check.sh": health,
        "verify_application.sh": verify,
    }.items():
        require("set -Eeuo pipefail" in text, f"{name} is not fail-closed")

    for fragment in (
        "DB_NAME=${DB_NAME:-vibmail_app}",
        "MAILSERVER_DB_NAME=${MAILSERVER_DB_NAME:-vibmail}",
        'mariadb-dump "${DUMP_OPTIONS[@]}"',
        "--single-transaction",
        "contact-state.tar.gz",
        "configuration.tar.gz",
        "BACKUP_METADATA.json",
        "sha256sum --check",
        "vibmail-public-contact postfix dovecot vibmail-ingestion vibmail-gunicorn",
    ):
        require(fragment in backup, f"backup contract missing: {fragment}")

    for fragment in (
        "validate_tar_archive",
        "member.issym()",
        "sha256sum --check",
        'mariadb "${DB_OPTIONS[@]}" --binary-mode',
        "manage.py verify_mailserver_schema",
        "manage.py verify_postfix_contract",
        "manage.py collectstatic --noinput",
        "postfix check",
        "nginx -t",
    ):
        require(fragment in restore, f"restore contract missing: {fragment}")

    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
    ipv4_pattern = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
    allowed_email_domains = {"example.com", "example.org", "example.net", "example.test", "other.test"}

    for text, name in (
        (backup, "backup.sh"),
        (restore, "restore.sh"),
        (health, "health_check.sh"),
        (verify, "verify_application.sh"),
    ):
        for candidate in ipv4_pattern.findall(text):
            try:
                address = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            require(not address.is_global, f"global IP literal leaked in {name}")

        for match in email_pattern.finditer(text):
            domain = match.group(1).lower()
            require(domain in allowed_email_domains, f"unapproved email domain leaked in {name}: {domain}")

    require('-H "Host: $APP_HOSTNAME"' in health, "health check does not use configured app hostname")
    require('-H "Host: $APP_HOSTNAME"' in verify, "application verifier does not use configured app hostname")
    require("manage.py check --deploy" in verify, "application verifier omits deployment checks")
    require(
        "manage.py ingest_maildir --once --dry-run" in verify,
        "application verifier omits non-mutating Maildir validation",
    )
    require(
        "systemctl stop vibmail-ingestion" not in verify,
        "application verifier must not stop the live ingestion worker",
    )

    print("OPERATIONAL_SCRIPTS=4")
    print("BACKUP_RESTORE_CONTRACT=PASS")
    print("HEALTH_VERIFY_CONTRACT=PASS")
    print("OPERATIONS_TESTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
