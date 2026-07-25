---
document_id: ui-foundation
title: MailStack UI Foundation
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# MailStack UI foundation

## Purpose

Freeze the shared visual and interaction language that all current and future MailStack screens
must follow. This foundation is identified as `MAILSTACK-UI-FOUNDATION-001` and is based on the complete
25-image intake rather than any single page.

## Scope

The foundation governs application shell, navigation, spacing, color, typography, cards, forms,
tables, status indicators, dialogs, drawers, responsive behavior, accessibility, and the secure
message-reading surface. It does not add routes, models, permissions, mail protocols, outbound
sending, public registration, or other unsupported behavior.

## Approved baseline

### Brand and color tokens

```text
Canvas          #F7F9FC
Surface         #FFFFFF
Primary blue    #0B4FF5
Primary tint    #EEF4FF
Navy text       #0B1733
Muted text      #667085
Border          #D9E1EE
Success         #12A66A
Warning         #F59E0B
Danger          #DC2626
Secondary       #7C3AED
```

The approved language uses a light enterprise-admin canvas, dark navy information hierarchy,
blue primary actions, rounded white surfaces, compact status badges, restrained shadows, and
clear green, amber, red, and purple semantic accents.

### Typography and spacing

Use a self-hosted or system-safe sans-serif stack. Body text begins at 16 px, compact metadata may
use 13–14 px, page headings use 32–40 px on desktop, and line height remains at least 1.45. Layout
uses a 4 px base unit with common spacing steps of 4, 8, 12, 16, 24, 32, and 48 px. Interactive
controls target a minimum 44 px height unless a compact data-density mode remains fully keyboard
accessible.

### Layout and components

Desktop pages use a persistent sidebar and compact top bar. Tablet pages collapse the sidebar to
an icon rail or drawer. Mobile pages use a single-column task flow. Shared components include
buttons, inputs, searchable selection, status badges, data tables, responsive list rows, cards,
menus, confirmation dialogs, drawers, alerts, pagination, empty states, loading states, and error
states.

### Secure message reader

The current plain-text and safe-HTML tabs are not the target experience. The approved direction is
a normalized reading view by default, a secondary plain-text view, and an optional isolated
original-layout view. Sanitized content must not inherit application styles or execute active
content. Remote resources, tracking pixels, forms, scripts, embedded frames, and unsafe URL or CSS
behaviors remain blocked.

## Change control

Foundation changes require a new phase record, updated affected design references, changelog and
documentation updates, accessibility review, responsive review, security review for message
content, deterministic manifest synchronization, full CI, and rollback notes. Page patches may
consume this foundation but may not silently redefine global tokens or activate controls whose
backend behavior is absent.
