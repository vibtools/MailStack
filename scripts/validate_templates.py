#!/usr/bin/env python3
"""Render and structurally validate all deployment templates without server changes."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "deployment/templates"
TOKEN_RE = re.compile(r"{{[A-Z][A-Z0-9_]*}}")
VALUES = {
    "MAIL_DOMAIN": "example.com",
    "APP_HOSTNAME": "app.example.com",
    "MAIL_HOSTNAME": "mail.example.com",
    "PUBLIC_HOSTNAME": "example.com",
    "PUBLIC_SERVER_NAMES": "example.com www.example.com",
    "ADMIN_EMAIL": "admin@example.com",
    "SERVER_IP": "203.0.113.10",
    "CERT_NAME": "vibmail-stack",
    "MAIL_DB_NAME": "vibmail",
    "APP_DB_NAME": "vibmail_app",
    "APP_DB_USER": "vibmail_app",
    "POSTFIX_DB_USER": "vibmail_postfix",
    "APP_DB_PASSWORD": "a" * 64,
    "POSTFIX_DB_PASSWORD": "b" * 64,
    "DJANGO_SECRET_KEY": "c" * 96,
    "CONTACT_HASH_SECRET": "d" * 96,
    "GUNICORN_WORKERS": "3",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    env = os.environ.copy()
    env.update(VALUES)
    rendered: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="vibmail-template-test-") as temporary:
        output_root = Path(temporary)
        for template in sorted(TEMPLATES.rglob("*.tpl")):
            relative = template.relative_to(TEMPLATES)
            output = output_root / relative.with_suffix("")
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/render_template.py"),
                    str(template),
                    str(output),
                    "--mode",
                    "0600",
                ],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            text = output.read_text(encoding="utf-8")
            require(not TOKEN_RE.search(text), f"unresolved token in {relative}")
            rendered[relative.with_suffix("").as_posix()] = text

        public_output = output_root / "public-site"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/render_public_site.py"),
                str(ROOT / "public-site/site-template"),
                str(public_output),
                "--public-hostname",
                VALUES["PUBLIC_HOSTNAME"],
                "--app-hostname",
                VALUES["APP_HOSTNAME"],
                "--mail-hostname",
                VALUES["MAIL_HOSTNAME"],
                "--mail-domain",
                VALUES["MAIL_DOMAIN"],
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        for path in public_output.rglob("*"):
            if path.is_file():
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                require(not re.search(r"__[A-Z][A-Z0-9_]*__", text), f"public token in {path}")

    sql = rendered["mariadb/bootstrap.sql"]
    for required in (
        "mail_domains",
        "mailboxes",
        "mail_aliases",
        "postfix_virtual_domains",
        "postfix_virtual_mailboxes",
        "postfix_virtual_aliases",
        "SQL SECURITY INVOKER",
    ):
        require(required in sql, f"MariaDB bootstrap missing {required}")
    require("GRANT ALL PRIVILEGES ON `vibmail`" not in sql, "application user has mail-schema DDL")
    require(
        "GRANT SELECT (`domain_id`, `local_part`, `email`, `maildir`, `active`)" in sql,
        "Postfix invoker lacks column-scoped mailbox access",
    )
    require(
        "GRANT SELECT (`domain_id`, `source`, `destination`, `active`)" in sql,
        "Postfix invoker lacks column-scoped alias access",
    )
    postfix_grant_section = sql.split("SQL SECURITY INVOKER views require", 1)[-1]
    postfix_grants = "\n".join(
        line for line in postfix_grant_section.splitlines()
        if not line.lstrip().startswith("--")
    )
    require("password_hash" not in postfix_grants, "Postfix user can access password hashes")
    for forbidden in ("GRANT INSERT", "GRANT UPDATE", "GRANT DELETE", "GRANT ALL"):
        require(forbidden not in postfix_grants, f"Postfix user has unsafe privilege: {forbidden}")

    for map_name in ("domains", "mailboxes", "aliases"):
        mapping = rendered[f"postfix/mysql-virtual-{map_name}.cf"]
        require("hosts = 127.0.0.1" in mapping, f"{map_name} map is not loopback-only")
        require("query = SELECT" in mapping, f"{map_name} map must be read-only")
        require("INSERT" not in mapping and "UPDATE" not in mapping and "DELETE" not in mapping, f"unsafe {map_name} map")

    dovecot = rendered["dovecot/99-vibmail.conf"]
    require("protocols = lmtp" in dovecot, "Dovecot must be LMTP-only")
    require("protocols = imap" not in dovecot and "protocols = pop3" not in dovecot, "unexpected mailbox protocol")
    require("/var/spool/postfix/private/dovecot-lmtp" in dovecot, "LMTP socket missing")
    require("service lmtp" in dovecot and "user = vmail" in dovecot, "LMTP is not reduced to vmail")
    require("password={PLAIN}" not in dovecot, "Dovecot contains a static plaintext login password")

    app_nginx = rendered["nginx/app.conf"]
    require("include proxy_params" not in app_nginx, "duplicate proxy header risk")
    require(app_nginx.count("proxy_set_header Host $host;") == 2, "unexpected Host header count")
    require("internal;" in app_nginx and "/_protected_attachments/" in app_nginx, "protected attachment route missing")

    public_nginx = rendered["nginx/public.conf"]
    require("/api/contact/" in public_nginx, "contact proxy missing")
    require("Content-Security-Policy" in public_nginx, "public CSP missing")
    require("includeSubDomains; preload" in public_nginx, "public HSTS preload policy missing")

    app_environment = rendered["env/vibmail.env"]
    require("SECURE_HSTS_PRELOAD=true" in app_environment, "application HSTS preload is disabled")

    for unit_name in (
        "systemd/vibmail-gunicorn.service",
        "systemd/vibmail-ingestion.service",
        "systemd/vibmail-public-contact.service",
    ):
        unit = rendered[unit_name]
        require("NoNewPrivileges=true" in unit, f"{unit_name} lacks NoNewPrivileges")
        require("ProtectSystem=" in unit, f"{unit_name} lacks ProtectSystem")
        require("Restart=on-failure" in unit, f"{unit_name} lacks restart policy")

    print(f"TEMPLATES_RENDERED={len(rendered)}")
    print("DEPLOYMENT_TEMPLATE_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
