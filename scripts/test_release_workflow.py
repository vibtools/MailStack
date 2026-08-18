#!/usr/bin/env python3
"""Contract tests for fail-closed tag-to-GitHub-Release automation."""
from __future__ import annotations

import importlib.util
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


GATE = load_module("mailstack_release_gate", ROOT / "scripts/release_gate.py")


def make_root(version: str, package_version: str) -> Path:
    temporary = tempfile.TemporaryDirectory(prefix="mailstack-release-gate-test-")
    roots.append(temporary)
    root = Path(temporary.name)
    (root / "mailbox-app").mkdir()
    (root / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")
    (root / "mailbox-app/pyproject.toml").write_text(
        f'[project]\nname = "mailstack"\nversion = "{package_version}"\n',
        encoding="utf-8",
        newline="\n",
    )
    return root


roots: list[tempfile.TemporaryDirectory[str]] = []


def test_version_normalization() -> None:
    assert GATE.normalize_package_version("1.3.0-rc.5") == "1.3.0rc5"
    assert GATE.normalize_package_version("1.3.0") == "1.3.0"
    try:
        GATE.normalize_package_version("1.3")
    except GATE.ReleaseGateError:
        pass
    else:
        raise AssertionError("unsupported VERSION must fail closed")


def test_tag_identity_and_manual_mode() -> None:
    root = make_root("1.3.0-rc.5", "1.3.0rc5")
    identity = GATE.validate_local_identity(
        root,
        event_name="push",
        ref_type="tag",
        ref_name="v1.3.0-rc.5",
        sha="a" * 40,
    )
    assert identity.publish is True
    assert identity.prerelease is True
    assert identity.tag == "v1.3.0-rc.5"

    manual = GATE.validate_local_identity(
        root,
        event_name="workflow_dispatch",
        ref_type="branch",
        ref_name="main",
        sha="b" * 40,
    )
    assert manual.publish is False

    stable_root = make_root("1.3.0", "1.3.0")
    stable = GATE.validate_local_identity(
        stable_root,
        event_name="push",
        ref_type="tag",
        ref_name="v1.3.0",
        sha="e" * 40,
    )
    assert stable.prerelease is False

    try:
        GATE.validate_local_identity(
            root,
            event_name="push",
            ref_type="tag",
            ref_name="v1.3.0-rc.4",
            sha="a" * 40,
        )
    except GATE.ReleaseGateError:
        pass
    else:
        raise AssertionError("tag/version mismatch must fail closed")


def test_package_version_mismatch_fails() -> None:
    root = make_root("1.3.0-rc.5", "1.3.0rc4")
    try:
        GATE.validate_local_identity(
            root,
            event_name="workflow_dispatch",
            ref_type="branch",
            ref_name="main",
            sha="c" * 40,
        )
    except GATE.ReleaseGateError:
        pass
    else:
        raise AssertionError("VERSION/project.version mismatch must fail closed")


def test_successful_main_ci_payload_contract() -> None:
    sha = "d" * 40
    payload = {
        "workflow_runs": [
            {
                "head_sha": sha,
                "head_branch": "main",
                "event": "push",
                "status": "completed",
                "conclusion": "success",
            }
        ]
    }
    assert GATE.payload_has_successful_main_ci(payload, sha=sha, default_branch="main")
    payload["workflow_runs"][0]["head_branch"] = "feature"
    assert not GATE.payload_has_successful_main_ci(payload, sha=sha, default_branch="main")



def test_existing_release_status_fails_closed() -> None:
    GATE.require_release_lookup_absent_status(404, "v1.3.0-rc.5")
    for status in (200, 500):
        try:
            GATE.require_release_lookup_absent_status(status, "v1.3.0-rc.5")
        except GATE.ReleaseGateError:
            pass
        else:
            raise AssertionError(f"release lookup status {status} must fail closed")


def test_exact_main_head_guard() -> None:
    original = GATE.git_output
    matching = "f" * 40

    def fake_git_output(root: Path, *arguments: str) -> str:
        if arguments and arguments[0] == "fetch":
            return ""
        if arguments[:2] == ("rev-parse", "refs/remotes/origin/main"):
            return matching
        raise AssertionError(arguments)

    GATE.git_output = fake_git_output
    try:
        GATE.require_exact_main_head(ROOT, matching, "main")
        try:
            GATE.require_exact_main_head(ROOT, "0" * 40, "main")
        except GATE.ReleaseGateError:
            pass
        else:
            raise AssertionError("non-main tag target must fail closed")
    finally:
        GATE.git_output = original

def test_workflow_contract() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    required = (
        'workflow_dispatch:',
        'tags:',
        '- "v*"',
        'build-verified-source:',
        'publish-github-release:',
        'needs: build-verified-source',
        "contents: read",
        "actions: read",
        "contents: write",
        "python scripts/release_gate.py",
        "--remote",
        'release create "$RELEASE_TAG"',
        'gh "${args[@]}"',
        "--verify-tag",
        "--prerelease",
        "--latest=false",
        "--latest",
        'dist/*.zip',
        'dist/*.sha256',
        'docs/RELEASE_NOTES_1.3.1.md',
    )
    for marker in required:
        assert marker in text, marker
    assert "--clobber" not in text
    assert "gh release edit" not in text
    assert "github.event_name == 'push'" in text
    assert "github.ref_type == 'tag'" in text


def main() -> int:
    tests = (
        test_version_normalization,
        test_tag_identity_and_manual_mode,
        test_package_version_mismatch_fails,
        test_successful_main_ci_payload_contract,
        test_existing_release_status_fails_closed,
        test_exact_main_head_guard,
        test_workflow_contract,
    )
    try:
        for test in tests:
            test()
            print(f"PASS={test.__name__}")
    finally:
        for temporary in roots:
            temporary.cleanup()
    print(f"RELEASE_WORKFLOW_TESTS={len(tests)}")
    print("RELEASE_WORKFLOW_TEST_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
