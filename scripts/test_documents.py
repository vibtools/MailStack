#!/usr/bin/env python3
"""Contract tests for the MailStack documentation baseline and policy tooling."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run(*arguments: str, cwd: Path = ROOT, expected: int = 0) -> str:
    completed = subprocess.run(
        [sys.executable, *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode != expected:
        raise AssertionError(
            f"command returned {completed.returncode}, expected {expected}: {arguments}\n{output}"
        )
    return output


def test_current_baseline() -> None:
    output = run("scripts/manage_documents.py", "--root", ".", "check")
    assert "DOCUMENTATION_GATE=PASS" in output
    manifest = json.loads((ROOT / "documents/DOCUMENTATION_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["project"] == "MailStack"
    assert manifest["summary"]["draft"] == 0
    assert manifest["summary"]["phases"] >= 3
    assert any(
        item.get("phase_id") == "PHASE-002"
        for item in manifest["documents"]
    )


def test_sync_is_deterministic() -> None:
    with tempfile.TemporaryDirectory(prefix="mailstack-docs-test-") as temporary:
        target = Path(temporary)
        shutil.copytree(ROOT / "documents", target / "documents")
        shutil.copytree(ROOT / "scripts", target / "scripts")
        shutil.copy2(ROOT / "VERSION", target / "VERSION")
        run("scripts/manage_documents.py", "--root", ".", "sync", cwd=target)
        first_readme = (target / "documents/README.md").read_bytes()
        first_manifest = (target / "documents/DOCUMENTATION_MANIFEST.json").read_bytes()
        run("scripts/manage_documents.py", "--root", ".", "sync", cwd=target)
        assert first_readme == (target / "documents/README.md").read_bytes()
        assert first_manifest == (target / "documents/DOCUMENTATION_MANIFEST.json").read_bytes()


def test_new_phase_is_draft_and_blocked() -> None:
    with tempfile.TemporaryDirectory(prefix="mailstack-docs-phase-") as temporary:
        target = Path(temporary)
        shutil.copytree(ROOT / "documents", target / "documents")
        shutil.copytree(ROOT / "scripts", target / "scripts")
        shutil.copy2(ROOT / "VERSION", target / "VERSION")
        phase_numbers = [
            int(path.name.split("-", 2)[1])
            for path in (target / "documents/phases").glob("PHASE-*.md")
        ]
        next_phase = f"PHASE-{max(phase_numbers, default=-1) + 1:03d}"
        output = run(
            "scripts/manage_documents.py",
            "--root",
            ".",
            "new-phase",
            "--phase-id",
            next_phase,
            "--title",
            "Contract test phase",
            "--summary",
            "Verify draft phase enforcement.",
            cwd=target,
        )
        assert "DOCUMENTATION_PHASE_CREATED=DRAFT" in output
        check_output = run(
            "scripts/manage_documents.py",
            "--root",
            ".",
            "check",
            cwd=target,
            expected=1,
        )
        assert "draft document cannot pass" in check_output


def test_change_policy() -> None:
    policy = load_module("mailstack_documentation_policy", ROOT / "scripts/check_documentation_policy.py")
    findings = policy.evaluate_policy(["mailbox-app/templates/base.html"])
    assert len(findings) == 3
    findings = policy.evaluate_policy(
        [
            "mailbox-app/templates/base.html",
            "documents/phases/PHASE-001-NAVIGATION.md",
            "documents/USER_MANUAL.md",
            "CHANGELOG.md",
        ]
    )
    assert findings == []
    findings = policy.evaluate_policy(
        [
            "scripts/build_release.py",
            "documents/phases/PHASE-001-RELEASE.md",
            "CHANGELOG.md",
        ]
    )
    assert findings == []
    assert policy.evaluate_policy(["mailbox-app/requirements/locked.txt"]) == []
    assert policy.evaluate_policy(["public-site/requirements.txt"]) == []
    assert policy.evaluate_policy([".github/workflows/ci.yml"]) == []
    assert policy.evaluate_policy(["public-site/contact_service/test_contact_app.py"]) == []
    assert policy.evaluate_policy(["scripts/test_installer.py"]) == []
    design_only = policy.evaluate_policy(["design/intake/original/Dashboard.png"])
    assert len(design_only) == 2
    assert policy.evaluate_policy([
        "design/intake/original/Dashboard.png",
        "documents/phases/PHASE-001-UI-DESIGN.md",
        "CHANGELOG.md",
    ]) == []
    assert policy.evaluate_policy(["design/DESIGN_MANIFEST.json"]) == []
    renamed_ui = policy.evaluate_policy(
        [
            "R100\tmailbox-app/templates/base.html\tdocs/base.html",
            "documents/phases/PHASE-001-NAVIGATION.md",
            "CHANGELOG.md",
        ]
    )
    assert len(renamed_ui) == 1
    deleted_docs = policy.evaluate_policy(
        [
            "mailbox-app/templates/base.html",
            "D\tdocuments/phases/PHASE-001-NAVIGATION.md",
            "D\tdocuments/USER_MANUAL.md",
            "CHANGELOG.md",
        ]
    )
    assert len(deleted_docs) == 2


def main() -> int:
    tests = (
        test_current_baseline,
        test_sync_is_deterministic,
        test_new_phase_is_draft_and_blocked,
        test_change_policy,
    )
    for test in tests:
        test()
        print(f"PASS={test.__name__}")
    print(f"DOCUMENTATION_TESTS={len(tests)}")
    print("DOCUMENTATION_TEST_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
