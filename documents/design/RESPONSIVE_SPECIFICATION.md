---
document_id: ui-responsive-specification
title: MailStack Responsive Specification
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-25
---

# MailStack responsive specification

## Purpose

Define responsive behavior for the desktop-heavy design intake so implementation does not create
horizontal page overflow or unusable mobile controls.

## Scope

No dedicated mobile PNGs were supplied. These rules are approved derived behavior, not a claim of
mobile pixel matching. PHASE-002 implements the global shell breakpoints; page-content conversions
remain part of individual page phases.

## Approved baseline

```text
Mobile:   0–767 px
Tablet:   768–1199 px
Desktop:  1200 px and above
```

- At 1200 px and above, the sidebar is persistent and may collapse to an 80 px icon rail.
- Below 1200 px, the sidebar becomes an off-canvas drawer with a dimmed backdrop.
- Below 768 px, the top bar, content padding, account summary, footer, and page actions use compact
  single-column behavior.
- Drawer opening moves focus into navigation; backdrop, Escape, or route selection closes it and
  returns focus to the initiating control.
- Page headers stack title, supporting text, and primary action below 768 px.
- Existing table and form behavior remains preserved until each page-specific phase completes its
  responsive conversion.
- Future inbox work uses three panes on wide desktop, two panes on tablet, and one sequential pane
  on mobile.
- Message HTML must wrap long URLs and code, constrain images and tables, and never force page-wide
  horizontal scrolling.
- Navigation, filters, and actions must remain operable at 200 percent zoom.

## Change control

Each page patch must include desktop, tablet, and mobile verification at defined viewport widths.
A future dedicated mobile design may refine layout details through a new phase without weakening
accessibility, current functionality, or the PHASE-002 shell contract.
