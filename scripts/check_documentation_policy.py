#!/usr/bin/env python3
"""Require phase and user-document updates for maintained MailStack feature changes."""
from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

PHASE_SENSITIVE_PREFIXES = (
    "design/",
    "deployment/templates/",
    "mailbox-app/apps/",
    "mailbox-app/config/",
    "mailbox-app/deployment/",
    "mailbox-app/scripts/",
    "mailbox-app/static/",
    "mailbox-app/templates/",
    "public-site/contact_service/",
    "public-site/deployment/",
    "public-site/site-template/",
    "public-site/site/",
    "scripts/",
)
PHASE_SENSITIVE_FILES = {"install.sh", "VERSION"}
USER_FACING_PREFIXES = (
    "mailbox-app/apps/accounts/",
    "mailbox-app/apps/dashboard/",
    "mailbox-app/apps/mailboxes/",
    "mailbox-app/apps/messages/",
    "mailbox-app/static/",
    "mailbox-app/templates/",
    "public-site/site-template/",
    "public-site/site/",
)
CANONICAL_GUIDES = {
    "documents/ADMIN_GUIDE.md",
    "documents/HOW_TO_USE.md",
    "documents/USER_MANUAL.md",
}
GENERATED_ONLY = {
    "documents/DOCUMENTATION_MANIFEST.json",
    "documents/README.md",
    "design/DESIGN_MANIFEST.json",
    "docs/FORENSIC_FILE_INVENTORY.json",
}
ZERO_SHA = "0" * 40
GIT_EXECUTABLE = os.getenv("GIT_EXECUTABLE", "git")


class PolicyError(RuntimeError):
    """Raised when Git state cannot be inspected safely."""


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str

    @property
    def deleted(self) -> bool:
        return self.status.startswith("D")


def parse_changed_line(value: str | ChangedFile) -> list[ChangedFile]:
    if isinstance(value, ChangedFile):
        return [value]
    raw = value.strip()
    if "\t" not in raw:
        return [ChangedFile(status="M", path=raw.replace("\\", "/"))]
    parts = raw.split("\t")
    status = parts[0].strip() or "M"
    if status.startswith(("R", "C")) and len(parts) >= 3:
        old_path = parts[-2].strip().replace("\\", "/")
        new_path = parts[-1].strip().replace("\\", "/")
        return [
            ChangedFile(status="D", path=old_path),
            ChangedFile(status="A", path=new_path),
        ]
    path = parts[-1].strip().replace("\\", "/")
    return [ChangedFile(status=status, path=path)]


def run_git(root: Path, arguments: list[str], *, check: bool = True) -> str:
    try:
        completed = subprocess.run(
            [GIT_EXECUTABLE, *arguments],
            cwd=root,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        raise PolicyError(f"unable to execute Git at {GIT_EXECUTABLE}: {exc}") from exc
    if check and completed.returncode:
        raise PolicyError((completed.stdout + completed.stderr).strip())
    return completed.stdout.strip()


def commit_exists(root: Path, revision: str) -> bool:
    try:
        completed = subprocess.run(
            [GIT_EXECUTABLE, "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=root,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        raise PolicyError(f"unable to execute Git at {GIT_EXECUTABLE}: {exc}") from exc
    return completed.returncode == 0


def resolve_base(root: Path, requested: str | None, head: str) -> str | None:
    candidate = (requested or "").strip()
    if candidate and candidate != ZERO_SHA and commit_exists(root, candidate):
        return candidate
    parent = f"{head}^"
    if commit_exists(root, parent):
        return parent
    return None


def changed_files_from_git(root: Path, base: str | None, head: str) -> list[ChangedFile]:
    if base is None:
        return []
    output = run_git(root, ["diff", "--name-status", "--find-renames", base, head])
    changed = [
        item
        for line in output.splitlines()
        if line.strip()
        for item in parse_changed_line(line)
    ]
    return sorted(set(changed), key=lambda item: (item.path, item.status))



def is_test_only_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        "/tests/" in path
        or path.startswith("mailbox-app/tests/")
        or path.startswith("scripts/test_")
        or name.startswith("test_")
    )


def is_phase_sensitive(path: str) -> bool:
    if is_test_only_path(path):
        return False
    return path in PHASE_SENSITIVE_FILES or path.startswith(PHASE_SENSITIVE_PREFIXES)


def is_user_facing(path: str) -> bool:
    return path.startswith(USER_FACING_PREFIXES)


def evaluate_policy(changed_files: list[str | ChangedFile]) -> list[str]:
    changed = sorted(
        {normalized for item in changed_files for normalized in parse_changed_line(item)},
        key=lambda item: (item.path, item.status),
    )
    substantive = [item for item in changed if item.path not in GENERATED_ONLY]
    phase_sensitive = [item for item in substantive if is_phase_sensitive(item.path)]
    user_facing = [item for item in substantive if is_user_facing(item.path)]
    changed_phase_docs = [
        item
        for item in substantive
        if not item.deleted
        and item.path.startswith("documents/phases/")
        and item.path.endswith(".md")
    ]
    changed_guides = [
        item for item in substantive if not item.deleted and item.path in CANONICAL_GUIDES
    ]
    changelog_updated = any(
        not item.deleted and item.path == "CHANGELOG.md" for item in substantive
    )
    findings: list[str] = []
    if phase_sensitive and not changed_phase_docs:
        findings.append(
            "maintained runtime, deployment, or tooling changes require a "
            "documents/phases/PHASE-NNN-*.md update"
        )
    if phase_sensitive and not changelog_updated:
        findings.append("maintained feature-phase changes require CHANGELOG.md")
    if user_facing and not changed_guides:
        findings.append(
            "user-facing changes require USER_MANUAL.md, HOW_TO_USE.md, or ADMIN_GUIDE.md"
        )
    return findings


def main() -> int:
    global GIT_EXECUTABLE
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--git-executable", default=GIT_EXECUTABLE)
    args = parser.parse_args()
    GIT_EXECUTABLE = args.git_executable
    root = args.root.resolve()
    try:
        if args.changed_file:
            changed_files = [
                normalized
                for item in args.changed_file
                for normalized in parse_changed_line(item)
            ]
            base = "explicit-file-list"
        else:
            requested_base = args.base or os.getenv("DOCUMENTATION_BASE_SHA")
            base = resolve_base(root, requested_base, args.head)
            if base is None:
                print("DOCUMENTATION_POLICY=PASS_INITIAL_COMMIT")
                return 0
            changed_files = changed_files_from_git(root, base, args.head)
        findings = evaluate_policy(changed_files)
        print(f"DOCUMENTATION_POLICY_BASE={base}")
        print(f"DOCUMENTATION_POLICY_CHANGED_FILES={len(changed_files)}")
        for item in changed_files:
            print(f"DOCUMENTATION_POLICY_CHANGED={item.status}\t{item.path}")
        if findings:
            for finding in findings:
                print(f"DOCUMENTATION_POLICY_FINDING={finding}")
            print("DOCUMENTATION_POLICY=FAIL")
            return 1
        print("DOCUMENTATION_POLICY=PASS")
        return 0
    except PolicyError as exc:
        print(f"DOCUMENTATION_POLICY_FINDING={exc}")
        print("DOCUMENTATION_POLICY=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
