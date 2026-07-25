---
document_id: ui-accessibility-specification
title: MailStack Accessibility Specification
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# MailStack accessibility specification

## Purpose

Set a WCAG 2.2 AA implementation target for the redesigned MailStack interface.

## Scope

The specification applies to authenticated application screens, public pages, forms, navigation,
data tables, dialogs, notifications, message content views, and future administration screens.

## Approved baseline

- Every interactive control is keyboard reachable and has a visible focus indicator.
- Icons have accessible names when meaningful and are hidden from assistive technology when decorative.
- Status is communicated with text or iconography in addition to color.
- Form labels, help text, validation errors, and recovery instructions are programmatically associated.
- Dialogs manage initial focus, trap focus while open, close with Escape where safe, and return focus.
- Tables use semantic headers; responsive card conversion preserves labels.
- Touch targets are at least 24 by 24 CSS pixels, with 44 px preferred for primary controls.
- Text and essential icons meet required contrast ratios.
- Motion is limited and respects reduced-motion preferences.
- Live updates use restrained accessible announcements and do not steal focus.
- Sanitized message content remains isolated from application accessibility semantics and cannot alter the parent document.

## Change control

Every implemented page requires keyboard, focus, contrast, zoom, and screen-reader-oriented review.
Accessibility regressions block completion even when visual comparison passes.
