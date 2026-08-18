---
document_id: ui-accessibility-specification
title: MailStack Accessibility Specification
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.2
last_reviewed: 2026-08-18
---

# MailStack accessibility specification

## Purpose

Set a WCAG 2.2 AA implementation target for the redesigned MailStack interface.

## Scope

The specification applies to authenticated application screens, sign-in pages, forms, navigation,
data tables, dialogs, notifications, message content views, and future administration screens.
PHASE-002 applies these requirements to the shared application shell.

## Approved baseline

- The skip link targets a single `main` landmark on authenticated and unauthenticated pages.
- Primary navigation is labelled and exposes `aria-current="page"` for the active route.
- The mobile drawer publishes expanded state, removes the hidden sidebar from interaction, supports
  Escape and backdrop close, and restores focus to the trigger.
- The desktop collapse control publishes pressed state and retains accessible labels when visual
  labels are clipped.
- The account menu has an accessible identity label, supports Escape close, and uses a normal POST
  form with CSRF protection for logout.
- Decorative icons are hidden from assistive technology; meaningful controls carry text or labels.
- Every interactive control remains keyboard reachable and has a visible focus indicator.
- Primary controls target 44 px; status is communicated with text in addition to color.
- Motion respects `prefers-reduced-motion`.
- Live updates use restrained accessible announcements and do not steal focus.
- Sign-in pages do not expose authenticated navigation or live-update endpoints.
- Sanitized message content remains isolated from application accessibility semantics and cannot
  alter the parent document.

## Change control

Every implemented page requires keyboard, focus, contrast, zoom, and screen-reader-oriented review.
Accessibility regressions block completion even when visual comparison passes. Automated shell
contracts supplement but do not replace browser and assistive-technology acceptance testing.
