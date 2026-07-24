from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def _path_check(path: Path) -> dict[str, object]:
    try:
        if not path.is_dir():
            return {"ok": False}
        test_path = path / ".vibmail-healthcheck"
        test_path.write_text("ok", encoding="utf-8")
        test_path.unlink()
        return {"ok": True}
    except OSError:
        return {"ok": False}


@require_GET
def live(_request):
    return JsonResponse({"status": "live"})


@require_GET
def ready(_request):
    checks: dict[str, object] = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = {"ok": True}
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        checks["migrations"] = {"ok": not bool(pending)}
    except Exception:
        checks["database"] = {"ok": False}
        checks["migrations"] = {"ok": False}
    checks["mail_storage"] = _path_check(settings.MAIL_STORAGE_ROOT)
    checks["attachment_storage"] = _path_check(settings.ATTACHMENT_STORAGE_ROOT)
    checks["configuration"] = {
        "ok": bool(settings.MAIL_DOMAIN)
        and bool(settings.APP_HOSTNAME)
        and bool(settings.SECRET_KEY)
        and not settings.DEBUG
    }
    ok = all(bool(value.get("ok")) for value in checks.values() if isinstance(value, dict))
    return JsonResponse(
        {"status": "ready" if ok else "not_ready", "checks": checks}, status=200 if ok else 503
    )


def error_404(request, exception):
    from django.shortcuts import render

    return render(request, "errors/404.html", status=404)


def error_500(request):
    from django.shortcuts import render

    return render(request, "errors/500.html", status=500)
