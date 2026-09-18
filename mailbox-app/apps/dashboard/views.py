from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess  # nosec B404 # noqa: S404
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from contextlib import suppress
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, models
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.access import accessible_mailboxes, accessible_messages, is_admin
from apps.core.models import ServiceHeartbeat
from apps.core.forms import SiteSettingsForm
from apps.core.models import SiteSettings
from apps.mailboxes.models import Mailbox

logger = logging.getLogger(__name__)
GITHUB_REPO = "vibtools/MailStack"
UPDATE_STATUS_PATH = Path("/run/vibmail/update_status.json")
UPDATE_REQUEST_PATH = Path("/run/vibmail/update_request.json")
UPDATE_PROCESSING_PATH = Path("/run/vibmail/update_request.processing.json")
UPDATER_UNIT_PATH = Path("/etc/systemd/system/vibmail-updater.service")
UPGRADE_SCRIPT_PATH = Path("/opt/vibmail/app/scripts/upgrade.sh")


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


def _is_official_release_url(value: object) -> bool:
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


def _update_preflight() -> dict:
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    check("runtime directory", UPDATE_STATUS_PATH.parent.is_dir(), str(UPDATE_STATUS_PATH.parent))
    check("status path writable", os.access(UPDATE_STATUS_PATH.parent, os.W_OK), str(UPDATE_STATUS_PATH))
    check("request queue available", not UPDATE_REQUEST_PATH.exists(), str(UPDATE_REQUEST_PATH))
    check("request processing clear", not UPDATE_PROCESSING_PATH.exists(), str(UPDATE_PROCESSING_PATH))
    check("updater worker installed", UPDATER_UNIT_PATH.is_file(), str(UPDATER_UNIT_PATH))
    check("upgrade script executable", os.access(UPGRADE_SCRIPT_PATH, os.X_OK), str(UPGRADE_SCRIPT_PATH))
    required_paths = (
        ("application root", Path("/opt/vibmail/app"), "directory", False),
        ("virtualenv python", Path("/opt/vibmail/venv/bin/python"), "file", True),
        ("virtualenv pip", Path("/opt/vibmail/venv/bin/pip"), "file", True),
        ("runtime environment", Path("/etc/vibmail/vibmail.env"), "file", False),
    )
    for name, path, path_type, executable in required_paths:
        exists = path.is_dir() if path_type == "directory" else path.is_file()
        check(name, exists and (not executable or os.access(path, os.X_OK)), str(path))

    required_commands = (
        "python3", "python3.12", "flock", "rsync", "tar", "sha256sum", "systemctl",
        "curl", "nginx", "postfix", "realpath", "readlink", "doveconf",
    )
    command_paths = {name: shutil.which(name) for name in required_commands}
    for name, path in command_paths.items():
        check(f"command: {name}", path is not None, name)

    systemctl_path = shutil.which("systemctl")
    if systemctl_path:
        service_result = subprocess.run(  # nosec B603 # noqa: S603
            [systemctl_path, "is-active", "--quiet", "vibmail-updater.service"],
            check=False,
        )
        check("updater worker active", service_result.returncode == 0, "vibmail-updater.service")
        for service_name in (
            "mariadb", "postfix", "dovecot", "nginx", "vibmail-gunicorn",
            "vibmail-ingestion", "vibmail-public-contact",
        ):
            service_result = subprocess.run(  # nosec B603 # noqa: S603
                [systemctl_path, "is-active", "--quiet", f"{service_name}.service"],
                check=False,
            )
            check(f"service: {service_name}", service_result.returncode == 0, service_name)
    id_path = shutil.which("id")
    if id_path:
        user_result = subprocess.run(  # nosec B603 # noqa: S603
            [id_path, "-u", "vmail"],
            check=False,
            capture_output=True,
        )
        check("vmail user", user_result.returncode == 0, "vmail")
    else:
        check("vmail user", False, "id")
    try:
        free_bytes = shutil.disk_usage(UPDATE_STATUS_PATH.parent).free
        check("runtime disk space", free_bytes >= 100 * 1024 * 1024, f"{free_bytes} bytes free")
    except OSError as exc:
        check("runtime disk space", False, str(exc))

    failed = [item for item in checks if not item["passed"]]
    return {
        "status": "ready" if not failed else "blocked",
        "checks": checks,
        "message": "Updater is ready." if not failed else failed[0]["detail"],
    }


def _queue_update_request(payload: dict) -> None:
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=UPDATE_REQUEST_PATH.parent,
            prefix=".update-request-",
            delete=False,
        ) as request_file:
            temp_path = Path(request_file.name)
            json.dump(payload, request_file)
        os.chmod(temp_path, 0o640)
        os.link(temp_path, UPDATE_REQUEST_PATH)
    finally:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink()


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
@require_http_methods(["GET", "POST"])
def site_settings(request):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    settings_object = SiteSettings.get_solo()
    form = SiteSettingsForm(request.POST or None, request.FILES or None, instance=settings_object)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Settings saved successfully.")
        return redirect("dashboard:site_settings")
    return render(request, "dashboard/site_settings.html", {"form": form, "site_settings": settings_object})


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
@require_GET
def update_preflight(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    return JsonResponse(_update_preflight())


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

        if not _is_official_release_url(archive_url) or not _is_official_release_url(checksum_url):
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

        preflight = _update_preflight()
        if preflight["status"] != "ready":
            return JsonResponse(
                {"error": "Update preflight is blocked.", "preflight": preflight},
                status=503,
            )

        request_payload = {
            "archive_url": archive_url,
            "checksum_url": checksum_url,
            "confirm_upgrade": True,
        }
        try:
            _queue_update_request(request_payload)
        except FileExistsError:
            return JsonResponse({"error": "An update is already queued or in progress."}, status=409)

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
