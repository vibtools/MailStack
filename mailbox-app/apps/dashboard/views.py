from __future__ import annotations

import json
import logging
import os
import subprocess  # nosec B404 # noqa: S404
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection, models
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from apps.core.access import accessible_mailboxes, accessible_messages, is_admin
from apps.core.models import ServiceHeartbeat
from apps.mailboxes.models import Mailbox

logger = logging.getLogger(__name__)
GITHUB_REPO = "vibtools/MailStack"
UPDATE_STATUS_PATH = Path("/run/vibmail/update_status.json")


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _storage_ok(path) -> bool:
    try:
        return path.is_dir() and os.access(path, os.R_OK | os.W_OK | os.X_OK)
    except OSError:
        return False


@login_required
def index(request):
    mailboxes = accessible_mailboxes(request.user)
    messages = accessible_messages(request.user)
    administrator = is_admin(request.user)
    context = {
        "total_mailboxes": mailboxes.count(),
        "active_mailboxes": mailboxes.filter(status=Mailbox.Status.ACTIVE).count(),
        "disabled_mailboxes": mailboxes.filter(status=Mailbox.Status.DISABLED).count(),
        "total_messages": messages.count(),
        "total_unread": messages.filter(is_read=False).count(),
        "last_received": messages.aggregate(latest=models.Max("received_at"))["latest"],
        "recent_messages": messages.select_related("mailbox")[:8],
        "recent_mailboxes": mailboxes.order_by("-created_at")[:8],
        "is_admin": administrator,
    }
    if administrator:
        context.update(
            {
                "ingestion": ServiceHeartbeat.objects.filter(service_name="maildir_ingestion").first(),
                "mail_storage_ok": _storage_ok(settings.MAIL_STORAGE_ROOT),
                "database_ok": _database_ok(),
            }
        )
    return render(request, "dashboard/index.html", context)


@login_required
def system_update_page(request):
    if not is_admin(request.user):
        return render(request, "dashboard/403.html", status=403)

    current_version = "Unknown"
    pyproject_file = Path(settings.BASE_DIR) / "pyproject.toml"
    version_file = Path(settings.BASE_DIR).parent / "VERSION"

    if pyproject_file.exists():
        import re
        content = pyproject_file.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            current_version = match.group(1)
    elif version_file.exists():
        current_version = version_file.read_text(encoding="utf-8").strip()

    context = {
        "current_version": current_version,
    }
    return render(request, "dashboard/system_update.html", context)


@login_required
@require_GET
def check_update(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "MailStack-Updater"})  # nosec B310 # noqa: S310
        with urllib.request.urlopen(req, timeout=15) as response:  # nosec B310 # noqa: S310
            releases = json.loads(response.read().decode())
            data = releases

        if not data.get("tag_name") or data.get("draft") or data.get("prerelease"):
            return JsonResponse({"error": "Latest stable release is unavailable."}, status=404)

        assets = data.get("assets", [])
        archive_url = None
        checksum_url = None
        for asset in assets:
            asset_name = asset.get("name", "")
            if asset_name.endswith("-source.zip"):
                archive_url = asset["browser_download_url"]
            elif asset_name.endswith("-source.zip.sha256"):
                checksum_url = asset["browser_download_url"]

        version = data.get("tag_name", "").lstrip("v")
        return JsonResponse({
            "latest_version": version,
            "release_notes": data.get("body", ""),
            "archive_url": archive_url,
            "checksum_url": checksum_url,
            "published_at": data.get("published_at", ""),
        })
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JsonResponse({"error": "No releases found."}, status=404)
        logger.exception("Failed to check for updates HTTPError")
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        logger.exception("Failed to check for updates")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_POST
def start_update(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        body = json.loads(request.body)
        archive_url = body.get("archive_url")
        checksum_url = body.get("checksum_url")

        if not archive_url or not checksum_url:
            return JsonResponse({"error": "Missing URLs"}, status=400)

        allowed_prefix = f"https://github.com/{GITHUB_REPO}/releases/download/"
        if not archive_url.startswith(allowed_prefix) or not checksum_url.startswith(allowed_prefix):
            return JsonResponse(
                {"error": "Invalid update URL origin. Must be from official repository."},
                status=400,
            )

        if UPDATE_STATUS_PATH.exists():
            try:
                current_status = json.loads(UPDATE_STATUS_PATH.read_text(encoding="utf-8"))
                if current_status.get("step") not in (None, "idle", "error") and current_status.get(
                    "progress", 0
                ) != 100:
                    return JsonResponse({"error": "An update is already in progress."}, status=409)
            except (OSError, ValueError):
                pass

        UPDATE_STATUS_PATH.write_text(
            json.dumps({"step": "init", "message": "Downloading update archive...", "progress": 0}),
            encoding="utf-8",
        )

        def _run_update(a_url, c_url):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tf_arch:
                    archive_path = tf_arch.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip.sha256") as tf_check:
                    checksum_path = tf_check.name

                urllib.request.urlretrieve(a_url, archive_path)  # nosec B310 # noqa: S310
                UPDATE_STATUS_PATH.write_text(
                    json.dumps({
                        "step": "download",
                        "message": "Downloading checksum...",
                        "progress": 5,
                    }),
                    encoding="utf-8",
                )
                urllib.request.urlretrieve(c_url, checksum_path)  # nosec B310 # noqa: S310

                # Make them readable by root (they are created by vmail)
                os.chmod(archive_path, 0o644)
                os.chmod(checksum_path, 0o644)

                UPDATE_STATUS_PATH.write_text(
                    json.dumps({
                        "step": "execute",
                        "message": "Starting upgrade script...",
                        "progress": 8,
                    }),
                    encoding="utf-8",
                )

                cmd = [
                    "sudo", "-n", "/opt/vibmail/app/scripts/upgrade.sh",
                    "--archive", archive_path,
                    "--checksum", checksum_path,
                    "--confirm-upgrade",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603 # noqa: S603

                # Cleanup temp files after script finishes
                try:
                    os.remove(archive_path)
                    os.remove(checksum_path)
                except OSError:
                    pass

                if result.returncode != 0:
                    # Check if the script itself wrote an error status
                    try:
                        current_status = json.loads(UPDATE_STATUS_PATH.read_text(encoding="utf-8"))
                        if current_status.get("step") != "error":
                            error_msg = result.stderr.strip() or "Upgrade script failed to start or crashed."
                            UPDATE_STATUS_PATH.write_text(
                                json.dumps({"step": "error", "message": error_msg, "progress": -1}),
                                encoding="utf-8",
                            )
                    except Exception:
                        UPDATE_STATUS_PATH.write_text(
                            json.dumps({
                                "step": "error",
                                "message": "Upgrade script failed unexpectedly.",
                                "progress": -1,
                            }),
                            encoding="utf-8",
                        )
            except Exception as exc:
                UPDATE_STATUS_PATH.write_text(
                    json.dumps({
                        "step": "error",
                        "message": f"Update failed to start: {str(exc)}",
                        "progress": -1,
                    }),
                    encoding="utf-8",
                )

        t = threading.Thread(target=_run_update, args=(archive_url, checksum_url))
        t.daemon = True
        t.start()

        return JsonResponse({"status": "started"})
    except Exception as e:
        logger.exception("Failed to start update")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_GET
def update_status(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)

    try:
        if UPDATE_STATUS_PATH.exists():
            data = json.loads(UPDATE_STATUS_PATH.read_text(encoding="utf-8"))
            return JsonResponse(data)
        return JsonResponse({"step": "idle", "message": "No update in progress", "progress": 0})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
