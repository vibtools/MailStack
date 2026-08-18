#!/usr/bin/env python3
"""Fail-closed source audit for the public MailStack repository."""
from __future__ import annotations

import argparse
import ast
import hashlib
import ipaddress
import os
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from shell_runtime import bash_environment, bash_script_command, bash_syntax_command, resolve_bash

REQUIRED = {
    "README.md",
    "VERSION",
    "LICENSE",
    "ROADMAP.md",
    "CITATION.cff",
    "NOTICE.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    ".gitignore",
    "install.sh",
    "mailbox-app/manage.py",
    "public-site/contact_service/contact_app.py",
    "deployment/templates/mariadb/bootstrap.sql.tpl",
    ".github/workflows/ci.yml",
    ".github/pull_request_template.md",
    "scripts/check_docs.py",
    "scripts/generate_inventory.py",
    "docs/FORENSIC_FILE_INVENTORY.json",
    "scripts/test_installer.py",
    "scripts/test_operations.py",
    "scripts/release_gate.py",
    "scripts/test_release_workflow.py",
    "scripts/shell_runtime.py",
    "scripts/validate_templates.py",
    "docs/FEATURE_MATRIX.md",
    "docs/FORENSIC_AUDIT_REPORT.md",
    "docs/TEST_REPORT.md",
    "docs/SECURITY_REVIEW.md",
    "docs/PERFORMANCE_REVIEW.md",
    "docs/RELEASE_NOTES_1.3.0.md",
    "documents/README.md",
    "documents/USER_MANUAL.md",
    "documents/HOW_TO_USE.md",
    "documents/ADMIN_GUIDE.md",
    "documents/BASELINE.md",
    "documents/DOCUMENTATION_POLICY.md",
    "documents/DOCUMENTATION_MANIFEST.json",
    "documents/phases/PHASE-000-BASELINE.md",
    "documents/phases/PHASE-001-UI-DESIGN-INTAKE-BASELINE.md",
    "documents/phases/PHASE-002-SHARED-UI-FOUNDATION-AND-APPLICATION-SHELL.md",
    "documents/design/UI_FOUNDATION.md",
    "documents/design/SCREEN_CATALOG.md",
    "documents/design/COMPONENT_MATRIX.md",
    "documents/design/RESPONSIVE_SPECIFICATION.md",
    "documents/design/ACCESSIBILITY_SPECIFICATION.md",
    "documents/design/FUTURE_UI_ROADMAP.md",
    "documents/design/IMPLEMENTATION_STATUS.md",
    "design/README.md",
    "design/DESIGN_MANIFEST.json",
    "scripts/manage_designs.py",
    "scripts/test_designs.py",
    "scripts/test_ui_foundation.py",
    "mailbox-app/static/css/foundation.css",
    "mailbox-app/static/brand/mailstack-logo.svg",
    "mailbox-app/static/icons/mailstack-icons.svg",
    "mailbox-app/tests/functional/test_ui_foundation_shell.py",
    "scripts/manage_documents.py",
    "scripts/check_documentation_policy.py",
    "scripts/test_documents.py",
}
BLOCKED_NAMES = {
    ".env",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    ".coverage",
    "mariadb-backup.cnf",
}
BLOCKED_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".log",
    ".bak",
    ".tgz",
}
BLOCKED_DIRS = {
    ".git",
    ".venv",
    ".audit-venv",
    "venv",
    ".tox",
    ".nox",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "Maildir",
    "attachments",
}
PRIVATE_MARKERS = tuple(
    "-----BEGIN " + key_type + "PRIVATE KEY-----"
    for key_type in ("", "RSA ", "OPENSSH ")
)
ALLOWED_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "example.test",
    "other.test",
    "vibmail.my",
}
EMAIL_LITERAL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)
IPV4_LITERAL = re.compile(
    r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"
)


SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(?:password|passwd|secret(?:_key)?|api[_-]?key|access[_-]?key|token)\b"
    r"\s*[:=]\s*['\"]([^'\"\r\n]+)['\"]"
)
PLACEHOLDER_TERMS = {
    "example",
    "placeholder",
    "change-me",
    "changeme",
    "test",
    "dummy",
    "development",
    "insecure",
    "generate",
    "random",
    "redacted",
}


def is_ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in BLOCKED_DIRS or part in {"dist", "artifacts"} for part in relative.parts)


def run(command: list[str], cwd: Path, *, bash_runtime: bool = False) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=bash_environment() if bash_runtime else None,
    )
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--full", action="store_true", help="also run tests, lint, Bandit, and Django checks")
    args = parser.parse_args()
    root = args.root.resolve()
    findings: list[str] = []
    file_count = 0
    python_count = 0
    shell_count = 0

    for required in sorted(REQUIRED):
        if not (root / required).exists():
            findings.append(f"MISSING_REQUIRED:{required}")

    for path in sorted(root.rglob("*")):
        if is_ignored(path, root):
            continue
        relative = path.relative_to(root)
        if path.is_symlink():
            try:
                target = path.resolve(strict=True)
                target.relative_to(root)
            except (FileNotFoundError, ValueError):
                findings.append(f"UNSAFE_SYMLINK:{relative}")
            continue
        if not path.is_file():
            continue
        file_count += 1

        if path.name in BLOCKED_NAMES:
            findings.append(f"BLOCKED_FILENAME:{relative}")
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(f"BLOCKED_FILETYPE:{relative}")
        if path.suffix.lower() in {".zip", ".tar", ".gz"}:
            findings.append(f"GENERATED_ARCHIVE_IN_SOURCE:{relative}")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            findings.append(f"UNREADABLE:{relative}:{type(exc).__name__}")
            continue

        if "\r\n" in text:
            findings.append(f"CRLF_TEXT:{relative}")
        for marker in PRIVATE_MARKERS:
            if marker in text:
                findings.append(f"PRIVATE_KEY_MATERIAL:{relative}")

        for match in EMAIL_LITERAL.finditer(text):
            domain = match.group(1).lower()
            if domain not in ALLOWED_EMAIL_DOMAINS:
                findings.append(f"UNAPPROVED_EMAIL_DOMAIN:{relative}:{domain}")

        for candidate in IPV4_LITERAL.findall(text):
            try:
                address = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            if address.is_global:
                findings.append(f"GLOBAL_IP_LITERAL:{relative}")
                break

        # Literal credentials are allowed only in tests or obvious placeholders.
        if not any(part in {"tests", "test"} for part in relative.parts):
            for match in SECRET_ASSIGNMENT.finditer(text):
                value = match.group(1).lower()
                if not value.startswith(("$", "{{")) and not any(term in value for term in PLACEHOLDER_TERMS):
                    findings.append(f"LITERAL_CREDENTIAL_REVIEW:{relative}")
                    break

        if path.suffix == ".py":
            python_count += 1
            try:
                ast.parse(text, filename=str(relative))
            except SyntaxError as exc:
                findings.append(f"PYTHON_SYNTAX:{relative}:{exc.lineno}")
        elif path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                findings.append(f"JSON_SYNTAX:{relative}:{exc.lineno}")
        elif path.suffix == ".sh" or path.name == "install.sh":
            shell_count += 1
            code, output = run(bash_syntax_command(path, cwd=root), root, bash_runtime=True)
            if code:
                findings.append(f"SHELL_SYNTAX:{relative}:{output}")

    # Ensure the public-site template renders without leaving placeholder tokens.
    template_dir = root / "public-site/site-template"
    if template_dir.is_dir():
        with tempfile.TemporaryDirectory(prefix="vibmail-public-render-") as temporary:
            destination = Path(temporary) / "site"
            code, output = run(
                [
                    sys.executable,
                    str(root / "scripts/render_public_site.py"),
                    str(template_dir),
                    str(destination),
                    "--public-hostname", "example.com",
                    "--app-hostname", "app.example.com",
                    "--mail-hostname", "mail.example.com",
                    "--mail-domain", "example.com",
                ],
                root,
            )
            if code:
                findings.append(f"PUBLIC_TEMPLATE_RENDER:{output}")
            else:
                for rendered in destination.rglob("*"):
                    if rendered.is_file():
                        try:
                            rendered_text = rendered.read_text(encoding="utf-8")
                        except UnicodeDecodeError:
                            continue
                        if re.search(r"__[A-Z][A-Z0-9_]*__", rendered_text):
                            findings.append(f"UNRESOLVED_PUBLIC_TEMPLATE_TOKEN:{rendered.relative_to(destination)}")

    try:
        bash_runtime = resolve_bash()
    except RuntimeError as exc:
        findings.append(f"BASH_RUNTIME:{exc}")
        bash_runtime = None

    plan = bash_script_command(
        root / "install.sh",
        "--domain", "example.com",
        "--admin-email", "admin@example.com",
        "--server-ip", "203.0.113.10",
        "--non-interactive",
        "--plan",
        cwd=root,
    ) if bash_runtime else []
    if plan:
        code, output = run(plan, root, bash_runtime=True)
        if code or "PLAN_VALIDATION=PASS" not in output:
            findings.append(f"INSTALLER_PLAN:{output}")

    for command, label in (
        ([sys.executable, str(root / "scripts/manage_documents.py"), "--root", str(root), "check"], "USER_DOCUMENTATION_GATE"),
        ([sys.executable, str(root / "scripts/test_documents.py")], "DOCUMENTATION_TESTS"),
        ([sys.executable, str(root / "scripts/manage_designs.py"), "--root", str(root), "check"], "DESIGN_INTAKE_GATE"),
        ([sys.executable, str(root / "scripts/test_designs.py")], "DESIGN_TESTS"),
        ([sys.executable, str(root / "scripts/test_ui_foundation.py")], "UI_FOUNDATION_TESTS"),
        ([sys.executable, str(root / "scripts/check_docs.py")], "DOCUMENTATION_GATE"),
        ([sys.executable, str(root / "scripts/generate_inventory.py"), "--root", str(root), "--check"], "INVENTORY_GATE"),
        ([sys.executable, str(root / "scripts/validate_templates.py")], "TEMPLATE_VALIDATION"),
        ([sys.executable, str(root / "scripts/test_installer.py")], "INSTALLER_CONTRACT"),
        ([sys.executable, str(root / "scripts/test_operations.py")], "OPERATIONS_CONTRACT"),
        ([sys.executable, str(root / "scripts/test_release_workflow.py")], "RELEASE_WORKFLOW_CONTRACT"),
    ):
        code, output = run(command, root)
        if code:
            findings.append(f"{label}:{output}")

    if args.full:
        app = root / "mailbox-app"
        with tempfile.TemporaryDirectory(prefix="mailstack-full-audit-") as temporary:
            coverage_file = Path(temporary) / ".coverage"
            commands = [
                ([sys.executable, "-m", "pytest", "--cov=apps", "--cov-report=term-missing", "--cov-fail-under=85"], app, "PYTEST_COVERAGE", True),
                ([sys.executable, "-m", "ruff", "check", "."], app, "RUFF", True),
                ([sys.executable, "-m", "bandit", "-c", ".bandit", "-q", "-r", "apps", "config"], app, "BANDIT", True),
                (
                    [
                        sys.executable,
                        "-m",
                        "ruff",
                        "check",
                        "--config",
                        str(app / "pyproject.toml"),
                        str(root / "public-site/contact_service/contact_app.py"),
                    ],
                    root,
                    "CONTACT_RUFF",
                    False,
                ),
                (
                    [
                        sys.executable,
                        "-m",
                        "bandit",
                        "-c",
                        str(app / ".bandit"),
                        "-q",
                        str(root / "public-site/contact_service/contact_app.py"),
                    ],
                    root,
                    "CONTACT_BANDIT",
                    False,
                ),
                ([sys.executable, "manage.py", "makemigrations", "--check", "--dry-run", "--settings=config.settings.test"], app, "MIGRATION_DRIFT", True),
                ([sys.executable, "manage.py", "check", "--settings=config.settings.test"], app, "DJANGO_CHECK", True),
                ([sys.executable, "test_contact_app.py"], root / "public-site/contact_service", "CONTACT_TESTS", False),
                ([sys.executable, "-m", "pip", "check"], root, "PIP_CHECK", False),
            ]
            for command, cwd, label, django_environment in commands:
                env = os.environ.copy()
                if django_environment:
                    env["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
                else:
                    env.pop("DJANGO_SETTINGS_MODULE", None)
                if label == "PYTEST_COVERAGE":
                    env["COVERAGE_FILE"] = str(coverage_file)
                completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
                if completed.returncode:
                    findings.append(f"{label}:{(completed.stdout + completed.stderr).strip()}")

    print("=== MAILSTACK FORENSIC SOURCE AUDIT ===")
    print(f"ROOT={root}")
    print(f"FILES_SCANNED={file_count}")
    print(f"PYTHON_FILES={python_count}")
    print(f"SHELL_FILES={shell_count}")
    if bash_runtime:
        print(f"BASH_RUNTIME={bash_runtime}")
    if findings:
        for finding in sorted(set(findings)):
            print(f"FINDING={finding}")
        print(f"BLOCKING_FINDINGS={len(set(findings))}")
        print("FORENSIC_AUDIT=FAIL")
        return 1
    print("BLOCKING_FINDINGS=0")
    print("FORENSIC_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
