#!/usr/bin/env python3
"""Contract tests for canonical MailStack version management."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUMP = load_module("mailstack_bump_version", ROOT / "scripts/bump_version.py")
CHECK = load_module(
    "mailstack_check_version_consistency",
    ROOT / "scripts/check_version_consistency.py",
)


def make_root() -> Path:
    temporary = tempfile.TemporaryDirectory(prefix="mailstack-version-test-")
    roots.append(temporary)
    root = Path(temporary.name)
    (root / "mailbox-app").mkdir()
    (root / "documents").mkdir()
    (root / "design").mkdir()
    (root / "scripts").mkdir()
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    (root / "mailbox-app/pyproject.toml").write_text(
        '[project]\nname = "mailstack"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    frontmatter = "---\nstatus: active\nversion: 1.0.0\n---\n\n# Active\n"
    (root / "documents/active.md").write_text(frontmatter, encoding="utf-8")
    historical = "---\nstatus: historical\nversion: 0.9.0\n---\n\n# Historical\n"
    (root / "documents/historical.md").write_text(historical, encoding="utf-8")
    (root / "documents/DOCUMENTATION_MANIFEST.json").write_text(
        json.dumps({"release_version": "1.0.0"}), encoding="utf-8"
    )
    (root / "design/DESIGN_MANIFEST.json").write_text(
        json.dumps({"release_version": "1.0.0"}), encoding="utf-8"
    )
    return root


roots: list[tempfile.TemporaryDirectory[str]] = []


def test_bump_updates_active_metadata_only() -> None:
    root = make_root()
    calls: list[str] = []
    BUMP.run_generator = lambda _root, script: calls.append(script)
    BUMP.bump(root, "192.0.2.1")
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "192.0.2.1"
    assert 'version = "192.0.2.1"' in (root / "mailbox-app/pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert "version: 192.0.2.1" in (root / "documents/active.md").read_text(encoding="utf-8")
    assert "version: 0.9.0" in (root / "documents/historical.md").read_text(encoding="utf-8")
    assert calls == ["manage_documents.py", "manage_designs.py"]


def test_consistency_checker_rejects_mismatch() -> None:
    root = make_root()
    (root / "design/DESIGN_MANIFEST.json").write_text(
        json.dumps({"release_version": "0.9.0"}), encoding="utf-8"
    )
    try:
        CHECK.check(root)
    except ValueError as exc:
        assert "DESIGN_MANIFEST" in str(exc)
    else:
        raise AssertionError("metadata mismatch must fail closed")


def test_invalid_versions_are_rejected_and_same_version_syncs() -> None:
    root = make_root()
    for version in ("1.1", "1.1.0+local"):
        try:
            BUMP.bump(root, version)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid version must fail closed")
    BUMP.run_generator = lambda _root, _script: None
    BUMP.bump(root, "1.0.0")
    assert (root / "VERSION").read_text(encoding="utf-8").strip() == "1.0.0"


def main() -> int:
    tests = (
        test_bump_updates_active_metadata_only,
        test_consistency_checker_rejects_mismatch,
        test_invalid_versions_are_rejected_and_same_version_syncs,
    )
    for test in tests:
        test()
        print(f"PASS={test.__name__}")
    print(f"VERSION_WORKFLOW_TESTS={len(tests)}")
    print("VERSION_WORKFLOW_TEST_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
