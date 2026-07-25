#!/usr/bin/env python3
"""Contract tests for the MailStack UI design intake."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    path = ROOT / "scripts/manage_designs.py"
    spec = importlib.util.spec_from_file_location("mailstack_manage_designs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load design manager")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_minimal_root(module, *, entries: int = 1) -> Path:
    temporary = Path(tempfile.mkdtemp(prefix="mailstack-design-test-"))
    (temporary / "design/intake/original").mkdir(parents=True)
    (temporary / "VERSION").write_text((ROOT / "VERSION").read_text(encoding="utf-8"), encoding="utf-8")
    source_manifest = json.loads((ROOT / module.MANIFEST_PATH).read_text(encoding="utf-8"))
    selected = source_manifest["images"][:entries]
    for item in selected:
        source = ROOT / item["path"]
        target = temporary / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    source_manifest["images"] = selected
    source_manifest["summary"] = {}
    (temporary / module.MANIFEST_PATH).write_text(
        json.dumps(source_manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    module.sync(temporary)
    return temporary


def test_current_baseline() -> None:
    module = load_module()
    summary = module.check(ROOT)
    assert summary["images"] == 25
    assert summary["mobile_designs"] == 0


def test_sync_is_deterministic() -> None:
    module = load_module()
    target = make_minimal_root(module)
    try:
        module.sync(target)
        first = (target / module.MANIFEST_PATH).read_bytes()
        module.sync(target)
        second = (target / module.MANIFEST_PATH).read_bytes()
        assert first == second
    finally:
        shutil.rmtree(target)


def test_tampered_source_is_blocked() -> None:
    module = load_module()
    target = make_minimal_root(module)
    try:
        manifest = json.loads((target / module.MANIFEST_PATH).read_text(encoding="utf-8"))
        image = target / manifest["images"][0]["path"]
        data = bytearray(image.read_bytes())
        data[-8] ^= 1
        image.write_bytes(data)
        try:
            module.check(target)
        except module.DesignError:
            return
        raise AssertionError("tampered design source unexpectedly passed")
    finally:
        shutil.rmtree(target)


def test_duplicate_id_and_extra_asset_are_blocked() -> None:
    module = load_module()
    target = make_minimal_root(module, entries=2)
    try:
        manifest_path = target / module.MANIFEST_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["images"][1]["screen_id"] = manifest["images"][0]["screen_id"]
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        try:
            module.check(target)
        except module.DesignError as exc:
            assert "duplicate screen_id" in str(exc)
        else:
            raise AssertionError("duplicate screen ID unexpectedly passed")

    finally:
        shutil.rmtree(target)

    target = make_minimal_root(module)
    try:
        source = next((ROOT / module.ORIGINAL_ROOT).glob("*.png"))
        shutil.copy2(source, target / module.ORIGINAL_ROOT / "untracked-design.png")
        try:
            module.check(target)
        except module.DesignError as exc:
            assert "file set mismatch" in str(exc)
        else:
            raise AssertionError("untracked design source unexpectedly passed")
    finally:
        shutil.rmtree(target)


def main() -> int:
    tests = (
        test_current_baseline,
        test_sync_is_deterministic,
        test_tampered_source_is_blocked,
        test_duplicate_id_and_extra_asset_are_blocked,
    )
    for test in tests:
        test()
        print(f"PASS={test.__name__}")
    print(f"DESIGN_TESTS={len(tests)}")
    print("DESIGN_TEST_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
