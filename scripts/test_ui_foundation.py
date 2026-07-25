#!/usr/bin/env python3
"""Dependency-free contract tests for the MailStack shared UI foundation."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "mailbox-app/templates/base.html"
FOUNDATION = ROOT / "mailbox-app/static/css/foundation.css"
APP_JS = ROOT / "mailbox-app/static/js/app.js"
ROOT_LOGO = ROOT / "assets/mailstack-logo.svg"
STATIC_LOGO = ROOT / "mailbox-app/static/brand/mailstack-logo.svg"
ICONS = ROOT / "mailbox-app/static/icons/mailstack-icons.svg"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_files_exist() -> None:
    for path in (BASE, FOUNDATION, APP_JS, ROOT_LOGO, STATIC_LOGO, ICONS):
        assert path.is_file(), f"missing required UI foundation file: {path.relative_to(ROOT)}"


def test_shell_contract() -> None:
    base = read(BASE)
    required = (
        'class="skip-link"',
        'id="main-content"',
        'class="app-shell"',
        'data-app-sidebar',
        'class="app-topbar"',
        'aria-label="Primary"',
        'data-shell-toggle',
        'data-sidebar-collapse',
        'data-user-menu',
        'method="post"',
        "{% csrf_token %}",
        'data-enable-notifications',
        "Receive-only mode",
        "Outbound sending is disabled",
        'class="auth-shell"',
    )
    for marker in required:
        assert marker in base, f"missing shell marker: {marker}"
    assert base.count("{% block content %}") == 1
    assert base.count("{% endblock %}") >= 2  # title and content
    assert base.count('aria-current="page"') >= 4
    assert "is_vibmail_admin" in base
    assert base.index("css/app.css") < base.index("css/foundation.css")


def test_current_routes_only() -> None:
    base = read(BASE)
    required_routes = (
        "dashboard:index",
        "mailboxes:list",
        "mailboxes:create",
        "accounts:user_list",
        "accounts:logout",
        "messages:live_updates",
    )
    for route in required_routes:
        assert route in base, f"missing current route: {route}"
    prohibited_routes_or_controls = (
        "settings:",
        "logs:",
        "teams:",
        "domains:",
        "compose",
        "reply-all",
        ">Reply<",
        ">Forward<",
        ">Sent<",
        ">Drafts<",
        "IMAP",
        "POP3",
        "Sign up",
    )
    for marker in prohibited_routes_or_controls:
        assert marker not in base, f"unsupported future control activated: {marker}"


def test_frozen_tokens_and_responsive_contract() -> None:
    css = read(FOUNDATION)
    tokens = {
        "--ui-canvas": "#f7f9fc",
        "--ui-surface": "#ffffff",
        "--ui-primary": "#0b4ff5",
        "--ui-primary-tint": "#eef4ff",
        "--ui-text": "#0b1733",
        "--ui-text-muted": "#667085",
        "--ui-border": "#d9e1ee",
        "--ui-success": "#12a66a",
        "--ui-warning": "#f59e0b",
        "--ui-danger": "#dc2626",
        "--ui-secondary": "#7c3aed",
        "--ui-space-1": "4px",
        "--ui-space-4": "16px",
        "--ui-space-7": "48px",
        "--ui-control-height": "44px",
    }
    for name, value in tokens.items():
        assert f"{name}: {value};" in css, f"frozen token changed or missing: {name}"
    required = (
        "@media (min-width: 1200px)",
        "@media (max-width: 1199px)",
        "@media (max-width: 767px)",
        "@media (prefers-reduced-motion: reduce)",
        ":focus-visible",
        ".shell-backdrop",
        ".sidebar-collapsed",
        "min-height: 44px",
    )
    for marker in required:
        assert marker in css, f"missing UI foundation rule: {marker}"
    assert "@import" not in css
    assert not re.search(r"https?://", css, flags=re.IGNORECASE)


def test_javascript_preserves_runtime_and_adds_accessible_shell() -> None:
    javascript = read(APP_JS)
    required = (
        "const VibMail = (() =>",
        "setupAppShell()",
        "setupUserMenu()",
        "SIDEBAR_STORAGE_KEY",
        'window.matchMedia("(min-width: 1200px)")',
        "aria-expanded",
        "aria-hidden",
        "inert",
        "shellTabindex",
        'event.key === "Escape"',
        "document.body.dataset.liveUrl",
        "BroadcastChannel",
        "Notification.requestPermission",
        "document.addEventListener(\"DOMContentLoaded\", VibMail.init)",
    )
    for marker in required:
        assert marker in javascript, f"missing JavaScript contract: {marker}"
    prohibited = ("eval(", "new Function", ".innerHTML", "document.write(")
    for marker in prohibited:
        assert marker not in javascript, f"unsafe JavaScript construct found: {marker}"
    assert not re.search(r"https?://", javascript, flags=re.IGNORECASE)


def test_svg_assets_are_local_valid_and_complete() -> None:
    assert ROOT_LOGO.read_bytes() == STATIC_LOGO.read_bytes(), "runtime logo diverges from canonical logo"
    logo_root = ET.parse(STATIC_LOGO).getroot()
    icons_root = ET.parse(ICONS).getroot()
    assert logo_root.tag.endswith("svg")
    assert icons_root.tag.endswith("svg")

    icon_ids = [element.attrib["id"] for element in icons_root.iter() if "id" in element.attrib]
    assert len(icon_ids) == len(set(icon_ids)), "duplicate icon IDs"
    assert all(value.startswith("icon-") for value in icon_ids), "unexpected non-icon ID in sprite"

    base = read(BASE)
    referenced = set(re.findall(r"#(icon-[a-z0-9-]+)", base))
    available = set(icon_ids)
    assert referenced, "base template does not reference the icon sprite"
    assert referenced <= available, f"missing sprite icons: {sorted(referenced - available)}"
    assert "xlink:href" not in read(ICONS)


def test_template_control_flow_is_balanced() -> None:
    base = read(BASE)
    pairs = (
        (r"{%\s*if\b", r"{%\s*endif\s*%}"),
        (r"{%\s*for\b", r"{%\s*endfor\s*%}"),
        (r"{%\s*block\b", r"{%\s*endblock\s*%}"),
    )
    for opening, closing in pairs:
        assert len(re.findall(opening, base)) == len(re.findall(closing, base)), (
            f"unbalanced template tags: {opening} / {closing}"
        )
    assert "{% else %}" in base


def test_foundation_does_not_modify_business_contracts() -> None:
    changed_runtime_paths = {
        "mailbox-app/templates/base.html",
        "mailbox-app/static/css/foundation.css",
        "mailbox-app/static/js/app.js",
        "mailbox-app/static/brand/mailstack-logo.svg",
        "mailbox-app/static/icons/mailstack-icons.svg",
    }
    assert not any("migrations/" in path for path in changed_runtime_paths)
    assert not any("urls.py" in path for path in changed_runtime_paths)
    assert not any("models.py" in path for path in changed_runtime_paths)


def main() -> int:
    tests = (
        test_required_files_exist,
        test_shell_contract,
        test_current_routes_only,
        test_frozen_tokens_and_responsive_contract,
        test_javascript_preserves_runtime_and_adds_accessible_shell,
        test_svg_assets_are_local_valid_and_complete,
        test_template_control_flow_is_balanced,
        test_foundation_does_not_modify_business_contracts,
    )
    for test in tests:
        test()
        print(f"PASS={test.__name__}")
    print(f"UI_FOUNDATION_TESTS={len(tests)}")
    print("UI_FOUNDATION_TEST_SUITE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
