#!/usr/bin/env python3
"""Synchronize and validate the immutable MailStack UI design intake."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path

MANIFEST_PATH = "design/DESIGN_MANIFEST.json"
ORIGINAL_ROOT = "design/intake/original"
SCREEN_ID_PATTERN = re.compile(r"^UI-\d{3}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_CLASSIFICATIONS = {
    "brand-reference",
    "current-redesign",
    "current-redesign-variant",
    "current-redesign-with-scope-adjustment",
    "future-architecture-review",
    "planned-feature",
}
ALLOWED_LIFECYCLES = {"current-redesign", "future-review", "planned", "reference"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COLOR_MODES = {0: "L", 2: "RGB", 3: "P", 4: "LA", 6: "RGBA"}


class DesignError(RuntimeError):
    """Raised when design intake data violates the frozen-reference contract."""


def canonical_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def inspect_png(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise DesignError(f"invalid PNG signature: {path.name}")
    offset = len(PNG_SIGNATURE)
    ihdr: tuple[int, int, int, int] | None = None
    seen_idat = False
    seen_iend = False
    chunk_index = 0
    while offset < len(data):
        if offset + 12 > len(data):
            raise DesignError(f"truncated PNG chunk: {path.name}")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        crc_end = chunk_end + 4
        if crc_end > len(data):
            raise DesignError(f"truncated PNG payload: {path.name}")
        payload = data[chunk_start:chunk_end]
        recorded_crc = struct.unpack(">I", data[chunk_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != recorded_crc:
            raise DesignError(f"PNG CRC mismatch: {path.name}")
        if chunk_index == 0 and chunk_type != b"IHDR":
            raise DesignError(f"PNG IHDR is not first: {path.name}")
        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                raise DesignError(f"invalid PNG IHDR: {path.name}")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if width <= 0 or height <= 0 or compression != 0 or filtering != 0:
                raise DesignError(f"unsupported PNG header: {path.name}")
            if color_type not in COLOR_MODES or interlace not in {0, 1}:
                raise DesignError(f"unsupported PNG color or interlace mode: {path.name}")
            ihdr = (width, height, bit_depth, color_type)
        elif chunk_type == b"IDAT":
            seen_idat = True
        elif chunk_type == b"IEND":
            if length != 0:
                raise DesignError(f"invalid PNG IEND: {path.name}")
            seen_iend = True
            offset = crc_end
            break
        offset = crc_end
        chunk_index += 1
    if ihdr is None or not seen_idat or not seen_iend:
        raise DesignError(f"incomplete PNG structure: {path.name}")
    if offset != len(data):
        raise DesignError(f"unexpected bytes after PNG IEND: {path.name}")
    width, height, bit_depth, color_type = ihdr
    return {
        "format": "PNG",
        "mode": COLOR_MODES[color_type],
        "has_alpha": color_type in {4, 6},
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def load_manifest(root: Path) -> dict[str, object]:
    path = root / MANIFEST_PATH
    if not path.is_file():
        raise DesignError(f"missing design manifest: {MANIFEST_PATH}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DesignError(f"invalid design manifest JSON at line {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise DesignError("design manifest root must be an object")
    return payload


def validate_and_render(root: Path, payload: dict[str, object]) -> tuple[str, dict[str, int]]:
    if payload.get("schema_version") != 1 or payload.get("project") != "MailStack":
        raise DesignError("unsupported design manifest identity")
    if payload.get("release_version") != (root / "VERSION").read_text(encoding="utf-8").strip():
        raise DesignError("design manifest release version does not match VERSION")
    if payload.get("status") != "frozen-reference":
        raise DesignError("design manifest status must remain frozen-reference")
    source_archive = payload.get("source_archive")
    if not isinstance(source_archive, dict) or not SHA256_PATTERN.fullmatch(
        str(source_archive.get("sha256", ""))
    ):
        raise DesignError("design source archive SHA-256 is missing or invalid")
    if source_archive.get("archive_crc") != "PASS":
        raise DesignError("design source archive CRC status is not PASS")
    entries = payload.get("images")
    if not isinstance(entries, list) or not entries:
        raise DesignError("design manifest images must be a non-empty list")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    seen_sources: set[str] = set()
    canonical_entries: list[dict[str, object]] = []
    lifecycle_counts: Counter[str] = Counter()
    for raw in entries:
        if not isinstance(raw, dict):
            raise DesignError("design manifest image entry must be an object")
        screen_id = str(raw.get("screen_id", ""))
        if not SCREEN_ID_PATTERN.fullmatch(screen_id):
            raise DesignError(f"invalid screen_id: {screen_id}")
        if screen_id in seen_ids:
            raise DesignError(f"duplicate screen_id: {screen_id}")
        seen_ids.add(screen_id)
        path_text = str(raw.get("path", "")).replace("\\", "/")
        expected_prefix = f"{ORIGINAL_ROOT}/"
        if not path_text.startswith(expected_prefix):
            raise DesignError(f"design source must remain under {ORIGINAL_ROOT}: {path_text}")
        path = root / path_text
        if path.is_symlink() or not path.is_file():
            raise DesignError(f"missing or symlinked design source: {path_text}")
        if path_text in seen_paths:
            raise DesignError(f"duplicate design path: {path_text}")
        seen_paths.add(path_text)
        source_name = str(raw.get("source_name", ""))
        if source_name != path.name or source_name in seen_sources:
            raise DesignError(f"invalid or duplicate source_name: {source_name}")
        seen_sources.add(source_name)
        classification = str(raw.get("classification", ""))
        lifecycle = str(raw.get("lifecycle_status", ""))
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise DesignError(f"unsupported classification for {screen_id}: {classification}")
        if lifecycle not in ALLOWED_LIFECYCLES:
            raise DesignError(f"unsupported lifecycle for {screen_id}: {lifecycle}")
        if raw.get("implementation_phase") is not None:
            phase = str(raw["implementation_phase"])
            if not re.fullmatch(r"PHASE-\d{3}", phase):
                raise DesignError(f"invalid implementation phase for {screen_id}: {phase}")
        technical = inspect_png(path)
        canonical = dict(raw)
        canonical.update(technical)
        canonical["path"] = path_text
        canonical["source_name"] = source_name
        canonical_entries.append(canonical)
        lifecycle_counts[lifecycle] += 1

    actual_paths = {
        canonical_path(path, root)
        for path in (root / ORIGINAL_ROOT).rglob("*.png")
        if path.is_file()
    }
    if actual_paths != seen_paths:
        missing = sorted(seen_paths - actual_paths)
        extra = sorted(actual_paths - seen_paths)
        raise DesignError(f"design source file set mismatch; missing={missing}, extra={extra}")

    summary = {
        "images": len(canonical_entries),
        "current_redesign_references": lifecycle_counts["current-redesign"],
        "planned_feature_references": lifecycle_counts["planned"],
        "future_architecture_reviews": lifecycle_counts["future-review"],
        "brand_references": lifecycle_counts["reference"],
        "desktop_designs": sum(int(entry["width"]) >= 1200 for entry in canonical_entries),
        "mobile_designs": sum(int(entry["width"]) < 768 for entry in canonical_entries),
    }
    canonical_payload = dict(payload)
    canonical_payload["summary"] = summary
    canonical_payload["images"] = sorted(canonical_entries, key=lambda item: str(item["screen_id"]))
    rendered = json.dumps(canonical_payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return rendered, summary


def sync(root: Path) -> dict[str, int]:
    payload = load_manifest(root)
    rendered, summary = validate_and_render(root, payload)
    (root / MANIFEST_PATH).write_text(rendered, encoding="utf-8", newline="\n")
    return summary


def check(root: Path) -> dict[str, int]:
    payload = load_manifest(root)
    rendered, summary = validate_and_render(root, payload)
    current = (root / MANIFEST_PATH).read_text(encoding="utf-8")
    if current != rendered:
        raise DesignError(f"design manifest is stale: {MANIFEST_PATH}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("command", choices=("check", "sync"))
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        summary = check(root) if args.command == "check" else sync(root)
        print(f"DESIGN_IMAGES={summary['images']}")
        print(f"DESIGN_CURRENT_REFERENCES={summary['current_redesign_references']}")
        print(f"DESIGN_PLANNED_REFERENCES={summary['planned_feature_references']}")
        print(f"DESIGN_FUTURE_REVIEWS={summary['future_architecture_reviews']}")
        print(f"DESIGN_BRAND_REFERENCES={summary['brand_references']}")
        print(f"DESIGN_MANIFEST_{args.command.upper()}=PASS")
        return 0
    except (DesignError, OSError) as exc:
        print(f"DESIGN_FINDING={exc}")
        print(f"DESIGN_MANIFEST_{args.command.upper()}=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
