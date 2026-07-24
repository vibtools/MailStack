from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith("/messages/html/"):
            response["Content-Security-Policy"] = (
                "default-src 'none'; img-src data:; style-src 'unsafe-inline'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'self'; navigate-to 'none'"
            )
            response["X-Frame-Options"] = "SAMEORIGIN"
        else:
            response["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
                "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'self'"
            )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        return response
