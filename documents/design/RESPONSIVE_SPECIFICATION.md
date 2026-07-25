---
document_id: ui-responsive-specification
title: MailStack Responsive Specification
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# MailStack responsive specification

## Purpose

Define responsive behavior for the desktop-heavy design intake so implementation does not create
horizontal page overflow or unusable mobile controls.

## Scope

No dedicated mobile PNGs were supplied. These rules are therefore the approved derived behavior,
not a claim of mobile pixel matching.

## Approved baseline

```text
Mobile:   0–767 px
Tablet:   768–1199 px
Desktop:  1200 px and above
```

- The desktop sidebar becomes a drawer on mobile and an icon rail or drawer on tablet.
- Page headers stack title, supporting text, and primary action below 768 px.
- Data tables convert to labelled list cards when essential columns cannot fit.
- Forms become single-column on mobile and preserve readable labels and validation messages.
- The inbox uses three panes on wide desktop, two panes on tablet, and one sequential pane on mobile.
- Message HTML must wrap long URLs and code, constrain images and tables, and never force page-wide horizontal scrolling.
- Dialogs use the viewport safely, while destructive actions remain reachable without precision pointing.
- Navigation, filters, and actions remain operable at 200 percent zoom.

## Change control

Each page patch must include desktop, tablet, and mobile verification at defined viewport widths.
A future dedicated mobile design may refine layout details through a new phase without weakening
accessibility or current functionality.
