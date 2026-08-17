#!/usr/bin/env python3
"""Non-destructive contract tests for the root Ubuntu installer."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"
BASH = os.getenv("BASH_EXECUTABLE", "bash")


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BASH, str(INSTALLER), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    valid = run(
        "--domain", "example.com",
        "--admin-email", "admin@example.com",
        "--server-ip", "203.0.113.10",
        "--non-interactive",
        "--plan",
    )
    require(valid.returncode == 0, valid.stdout + valid.stderr)
    require("PLAN_VALIDATION=PASS" in valid.stdout, "valid plan did not pass")
    require("app.example.com" in valid.stdout, "default application hostname missing")
    require("mail.example.com" in valid.stdout, "default mail hostname missing")

    custom = run(
        "--domain", "example.org",
        "--app-host", "inbox.example.org",
        "--mail-host", "mx.example.org",
        "--public-host", "www.example.org",
        "--admin-email", "ops@example.org",
        "--server-ip", "2001:db8::10",
        "--non-interactive",
        "--skip-dns-check",
        "--plan",
    )
    require(custom.returncode == 0, custom.stdout + custom.stderr)
    require("https://inbox.example.org" in custom.stdout, "custom application hostname missing")
    require("mx.example.org" in custom.stdout, "custom mail hostname missing")

    invalid_cases = [
        ("invalid domain", ["--domain", "invalid", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("foreign app host", ["--domain", "example.com", "--app-host", "app.other.test", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("invalid email", ["--domain", "example.com", "--admin-email", "not-an-email", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("invalid IP", ["--domain", "example.com", "--admin-email", "admin@example.com", "--server-ip", "999.1.2.3", "--non-interactive", "--plan"]),
        ("unknown option", ["--domain", "example.com", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--not-a-real-option", "--plan"]),
        ("duplicate app and mail host", ["--domain", "example.com", "--app-host", "mail.example.com", "--mail-host", "mail.example.com", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("duplicate public and app host", ["--domain", "example.com", "--public-host", "app.example.com", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("invalid password env name", ["--domain", "example.com", "--admin-email", "admin@example.com", "--admin-password-env", "BAD-NAME", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
        ("double www", ["--domain", "example.com", "--public-host", "www.example.com", "--www", "--admin-email", "admin@example.com", "--server-ip", "203.0.113.10", "--non-interactive", "--plan"]),
    ]
    for label, arguments in invalid_cases:
        result = run(*arguments)
        require(result.returncode != 0, f"{label} unexpectedly passed")
        require("PLAN_VALIDATION=PASS" not in result.stdout, f"{label} printed PASS")

    installer_text = INSTALLER.read_text(encoding="utf-8")
    required_fragments = (
        "set -Eeuo pipefail",
        "flock -n 9",
        "apt-get install -y --no-install-recommends",
        "mariadb-server mariadb-client",
        "postfix postfix-mysql",
        "dovecot-core dovecot-lmtpd",
        "systemctl stop postfix dovecot",
        "mariadb --protocol=socket",
        "certbot certonly --webroot",
        "smtpd_sasl_auth_enable = no",
        "virtual_transport = lmtp:unix:private/dovecot-lmtp",
        'postconf -M "${service}/inet="',
        "manage.py check --deploy",
        "/etc/logrotate.d/vibmail",
        "systemctl is-active --quiet",
        "VIBMAIL_INSTALL=PASS",
    )
    for fragment in required_fragments:
        require(fragment in installer_text, f"installer contract missing: {fragment}")
    require("pip install --upgrade" not in installer_text, "installer performs an unpinned pip upgrade")
    require("install -d -m 0750 /var/log" not in installer_text, "installer mutates global /var/log mode")
    require("runuser -u vmail -- env -i" in installer_text, "vmail subprocess environment is not sanitized")
    require(
        "/run/vibmail/mailbox-provision-locks" in installer_text,
        "installer does not prepare the mailbox provisioning runtime lock path",
    )
    require("--if-missing" in installer_text, "repair bootstrap does not use idempotent management commands")
    require(
        installer_text.index('write_initial_credentials "$ADMIN_PASSWORD"')
        < installer_text.index('CURRENT_PHASE="nginx-bootstrap"'),
        "initial credentials are not persisted immediately after administrator creation",
    )
    require("tmux/screen" in installer_text, "SSH session resilience warning is missing")
    dovecot_template = (ROOT / "deployment/templates/dovecot/99-vibmail.conf.tpl").read_text(encoding="utf-8")
    require("allow_all_users=yes" in dovecot_template, "Dovecot static userdb LMTP fix is missing")
    mariadb_template = (ROOT / "deployment/templates/mariadb/bootstrap.sql.tpl").read_text(encoding="utf-8")
    require(
        mariadb_template.count("CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci") >= 2,
        "MariaDB case-insensitive utf8mb4 collation contract is missing",
    )
    production_settings = (ROOT / "mailbox-app/config/settings/production.py").read_text(encoding="utf-8")
    require(
        '"mysql.W003"' in production_settings and '"models.W044"' in production_settings,
        "qualified MariaDB compatibility warnings are not scoped in production settings",
    )
    require(
        installer_text.index('CURRENT_PHASE="acceptance-checks"')
        < installer_text.index("VIBMAIL_INSTALL=PASS"),
        "installer can print PASS before acceptance checks",
    )

    print("INSTALLER_VALID_CASES=2")
    print(f"INSTALLER_INVALID_CASES={len(invalid_cases)}")
    print("INSTALLER_CONTRACT_TESTS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
