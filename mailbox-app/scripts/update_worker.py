#!/usr/bin/env python3
"""Run the fixed, root-only MailStack upgrade request."""
from __future__ import annotations

import json
import os
import pwd
import stat
import subprocess  # nosec B404 # noqa: S404
import tempfile
import time
import urllib.parse
import urllib.request
from contextlib import suppress
from pathlib import Path

REQUEST_PATH = Path("/run/vibmail/update_request.json")
PROCESSING_PATH = Path("/run/vibmail/update_request.processing.json")
STATUS_PATH = Path("/run/vibmail/update_status.json")
UPGRADE_SCRIPT = Path("/opt/vibmail/app/scripts/upgrade.sh")
GITHUB_REPO = "vibtools/MailStack"


def write_status(step: str, message: str, progress: int) -> None:
    STATUS_PATH.write_text(
        json.dumps({"step": step, "message": message, "progress": progress}),
        encoding="utf-8",
    )


def valid_request_file() -> bool:
    try:
        request_stat = REQUEST_PATH.lstat()
        vmail_uid = pwd.getpwnam("vmail").pw_uid
        return (
            stat.S_ISREG(request_stat.st_mode)
            and request_stat.st_uid == vmail_uid
            and stat.S_IMODE(request_stat.st_mode) in (0o600, 0o640)
        )
    except (OSError, KeyError):
        return False


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlsplit(value)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.startswith(f"/{GITHUB_REPO}/releases/download/")
        and not parsed.query
        and not parsed.fragment
    )


def process_request() -> None:
    archive_path = None
    checksum_path = None
    try:
        if not valid_request_file():
            raise ValueError("Updater request ownership or permissions are invalid.")
        os.replace(REQUEST_PATH, PROCESSING_PATH)
        payload = json.loads(PROCESSING_PATH.read_text(encoding="utf-8"))
        archive_url = payload.get("archive_url")
        checksum_url = payload.get("checksum_url")
        if payload.keys() != {"archive_url", "checksum_url", "confirm_upgrade"}:
            raise ValueError("Updater request fields are invalid.")
        if (
            payload.get("confirm_upgrade") is not True
            or not valid_url(archive_url)
            or not valid_url(checksum_url)
        ):
            raise ValueError("Updater request failed validation.")
        if (
            os.geteuid() != 0
            or not os.access(UPGRADE_SCRIPT, os.X_OK)
        ):
            raise ValueError("Root updater worker is not correctly installed.")

        write_status("queued", "Request accepted by the root updater worker.", 0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as archive_file:
            archive_path = Path(archive_file.name)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip.sha256") as checksum_file:
            checksum_path = Path(checksum_file.name)
        write_status("download", "Downloading update archive...", 2)
        urllib.request.urlretrieve(archive_url, archive_path)  # nosec B310 # noqa: S310
        write_status("download", "Downloading checksum...", 5)
        urllib.request.urlretrieve(checksum_url, checksum_path)  # nosec B310 # noqa: S310
        write_status("execute", "Starting upgrade script...", 8)
        result = subprocess.run(  # nosec B603 # noqa: S603
            [
                str(UPGRADE_SCRIPT),
                "--archive", str(archive_path),
                "--checksum", str(checksum_path),
                "--confirm-upgrade",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            write_status("error", result.stderr.strip() or "Upgrade script failed.", -1)
    except Exception as exc:
        write_status("error", str(exc), -1)
    finally:
        with suppress(OSError):
            REQUEST_PATH.unlink()
        with suppress(OSError):
            PROCESSING_PATH.unlink()
        for path in (archive_path, checksum_path):
            if path is not None:
                with suppress(OSError):
                    path.unlink()


def main() -> None:
    while True:
        if REQUEST_PATH.is_file() and not PROCESSING_PATH.exists():
            process_request()
        time.sleep(1)


if __name__ == "__main__":
    main()
