from __future__ import annotations

import ipaddress
import logging
from typing import Any

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpRequest

from .models import AuditLog

logger = logging.getLogger(__name__)
SENSITIVE_KEY_PARTS = {
    "password",
    "secret",
    "token",
    "cookie",
    "session",
    "authorization",
    "credential",
    "private_key",
}


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _is_sensitive_key(key) else _sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


def _validated_ip(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",", 1)[0]
        validated = _validated_ip(forwarded)
        if validated:
            return validated
    return _validated_ip(request.META.get("REMOTE_ADDR"))


def record_audit(
    action: str,
    *,
    request: HttpRequest | None = None,
    actor=None,
    target_type: str = "",
    target_identifier: str = "",
    details: dict[str, Any] | None = None,
) -> AuditLog | None:
    if (
        actor is None
        and request is not None
        and getattr(request, "user", None)
        and request.user.is_authenticated
    ):
        actor = request.user
    try:
        return AuditLog.objects.create(
            actor=actor,
            action=action[:80],
            target_type=target_type[:80],
            target_identifier=target_identifier[:255],
            ip_address=client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:500] if request else ""),
            details=_sanitize(details or {}),
        )
    except DatabaseError:
        logger.exception(
            "Audit event persistence failed",
            extra={"event": "audit_persistence_failed", "audit_action": action[:80]},
        )
        return None
