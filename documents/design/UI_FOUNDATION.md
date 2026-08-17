---
document_id: ui-foundation
title: MailStack UI Foundation
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.4
last_reviewed: 2026-08-17
---

# MailStack UI foundation

## Purpose

Freeze and implement the shared visual and interaction language that all current and future
MailStack screens must follow. The baseline remains `MAILSTACK-UI-FOUNDATION-001` and is derived
from the complete 25-image intake rather than any single page.

## Scope

The foundation governs the application shell, navigation, spacing, color, typography, shared
controls, responsive behavior, focus treatment, and local brand/icon assets. PHASE-002 implements
that shared runtime layer in `base.html`, `foundation.css`, the preserved `VibMail` JavaScript
module, and self-hosted SVG assets.

It does not redesign individual dashboard, mailbox, user, inbox, or message page content. It does
not add routes, models, permissions, mail protocols, outbound sending, public registration, or
other unsupported behavior.

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

Runtime CSS exposes these values through `--ui-*` custom properties and maps the prior `--bg`,
`--surface`, `--text`, `--muted`, `--line`, `--brand`, and related variables to the frozen tokens.
That alias layer preserves existing page styles while page-by-page redesign remains pending.

### Typography and spacing

The runtime uses a system-safe sans-serif stack with no external font request. Body text begins at
16 px, compact metadata uses 13–14 px, and page headings use a responsive 32–40 px scale. Layout
uses a 4 px base unit with common steps of 4, 8, 12, 16, 24, 32, and 48 px. Primary interactive
controls target a minimum 44 px height.

### Application shell

Authenticated pages use a persistent desktop sidebar, sticky top bar, account menu, current-route
indicator, receive-only status card, bounded content region, and shared footer. Desktop users may
collapse the sidebar; the browser stores only that local presentation preference. Below 1200 px,
the sidebar becomes a drawer with a backdrop, Escape handling, focus movement, and focus return.

Unauthenticated pages use a separate sign-in shell and do not render private navigation or the live
updates endpoint. Administrator-only navigation remains guarded by the existing context-level
authorization decision.

### Shared assets and behavior

The runtime logo is byte-identical to `assets/mailstack-logo.svg`. Navigation icons are served from
a local SVG symbol sprite. No CDN, external font, framework, or new JavaScript package is introduced.
Existing live polling, notifications, copy controls, tabs, confirmations, and the `VibMail`
namespace remain in place.

### Secure message reader

The current plain-text and safe-HTML tabs are not changed in this phase. The approved future
direction remains a normalized reading view by default, a secondary plain-text view, and an
optional isolated original-layout view. That work requires a dedicated security-focused page phase.

## Change control

Foundation changes require a new phase record, updated design references and user guides,
changelog, accessibility and responsive review, dependency-free contract tests, Django functional
tests, deterministic inventory synchronization, full CI, and rollback notes. Page patches may
consume this foundation but may not silently redefine global tokens or activate controls whose
backend behavior is absent.
