#!/usr/bin/env python3
"""Verify a MailStack source release archive, manifest, permissions, and safety."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import re
import zipfile
from pathlib import Path, PurePosixPath

BLOCKED_NAMES = {".env", ".coverage", "id_rsa", "id_ed25519", "credentials.json"}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db", ".log", ".bak"}
PRIVATE_MARKERS = tuple(
    ("-----BEGIN " + key_type + "PRIVATE KEY-----").encode("ascii")
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
    rb"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)
IPV4_LITERAL = re.compile(
    rb"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"
)

MANIFEST_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip", type=Path)
    parser.add_argument("--checksum", type=Path)
    args = parser.parse_args()

    if not args.zip.is_file():
        raise SystemExit(f"release ZIP missing: {args.zip}")

    expected = None
    if args.checksum:
        fields = args.checksum.read_text(encoding="utf-8").split()
        if len(fields) < 2:
            raise SystemExit("invalid checksum file")
        expected = fields[0].lower()
        if fields[1] != args.zip.name:
            raise SystemExit("checksum filename does not match release ZIP")

    actual = sha256(args.zip)
    if expected and actual != expected:
        raise SystemExit(f"checksum mismatch: expected {expected}, got {actual}")

    with zipfile.ZipFile(args.zip) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"ZIP integrity failure: {bad}")

        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise SystemExit("duplicate ZIP member")
        if not names:
            raise SystemExit("empty release ZIP")

        top_levels = {PurePosixPath(name).parts[0] for name in names}
        if len(top_levels) != 1:
            raise SystemExit("release must contain exactly one top-level directory")
        prefix = next(iter(top_levels)) + "/"

        for info in infos:
            pure = PurePosixPath(info.filename)
            if pure.is_absolute() or ".." in pure.parts or "" in pure.parts:
                raise SystemExit(f"unsafe ZIP member: {info.filename}")
            if pure.name in BLOCKED_NAMES or pure.suffix.lower() in BLOCKED_SUFFIXES:
                raise SystemExit(f"blocked file in release: {info.filename}")
            if info.is_dir():
                continue
            data = archive.read(info)
            if any(marker in data for marker in PRIVATE_MARKERS):
                raise SystemExit(f"private-key material in release: {info.filename}")
            for match in EMAIL_LITERAL.finditer(data):
                domain = match.group(1).decode("ascii").lower()
                if domain not in ALLOWED_EMAIL_DOMAINS:
                    raise SystemExit(
                        f"unapproved email domain in release: {info.filename}: {domain}"
                    )
            for candidate in IPV4_LITERAL.findall(data):
                try:
                    address = ipaddress.ip_address(candidate.decode("ascii"))
                except ValueError:
                    continue
                if address.is_global:
                    raise SystemExit(f"global IP literal in release: {info.filename}")

        manifest_name = prefix + "SOURCE_MANIFEST.sha256"
        if manifest_name not in names:
            raise SystemExit("source manifest missing")
        manifest_text = archive.read(manifest_name).decode("utf-8")
        expected_members: dict[str, str] = {}
        for number, line in enumerate(manifest_text.splitlines(), start=1):
            match = MANIFEST_LINE.fullmatch(line)
            if not match:
                raise SystemExit(f"invalid manifest line {number}")
            expected_hash, relative = match.groups()
            member = prefix + relative
            if member in expected_members:
                raise SystemExit(f"duplicate manifest path: {relative}")
            expected_members[member] = expected_hash

        actual_members = {name for name in names if not name.endswith("/") and name != manifest_name}
        if set(expected_members) != actual_members:
            missing = sorted(actual_members - set(expected_members))
            extra = sorted(set(expected_members) - actual_members)
            raise SystemExit(f"manifest member mismatch; unlisted={missing}, missing={extra}")

        for member, expected_hash in expected_members.items():
            if sha256_bytes(archive.read(member)) != expected_hash:
                raise SystemExit(f"manifest mismatch: {member.removeprefix(prefix)}")

        executable_members = [
            info for info in infos
            if not info.is_dir() and (info.filename == prefix + "install.sh" or info.filename.endswith(".sh"))
        ]
        for executable_info in executable_members:
            executable_mode = (executable_info.external_attr >> 16) & 0o777
            if executable_mode & 0o111 == 0:
                raise SystemExit(f"shell program is not executable in the release archive: {executable_info.filename}")

    print(f"SHA256={actual}")
    print(f"ARCHIVE_MEMBERS={len(names)}")
    print(f"MANIFEST_MEMBERS={len(expected_members)}")
    print("RELEASE_VERIFY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
