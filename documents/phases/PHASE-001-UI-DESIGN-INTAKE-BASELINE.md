---
document_id: phase-001-ui-design-intake-baseline
title: UI Design Intake Baseline
document_type: phase
audience: users-operators-designers-and-maintainers
status: active
version: 1.3.0-rc.5
last_reviewed: 2026-08-17
phase_id: PHASE-001
---

# PHASE-001: UI design intake baseline

## Objective

Import, verify, classify, and freeze the complete MailStack UI and logo design archive before any
page implementation begins.

## Scope

This phase preserves 25 original PNG files byte-for-byte under `design/intake/original/`, assigns
stable screen IDs, adds a deterministic manifest, freezes the shared UI foundation, catalogs
current and future screens, defines component, responsive, accessibility, roadmap, and status
specifications, and adds automated design-integrity checks to CI and the forensic audit.

No Django template, application static asset, model, migration, route, permission, mail-flow,
installer, or live user behavior is changed.

## User-facing changes

There is no runtime user-interface change in this phase. Users continue to use the verified
MailStack `1.3.0-rc.1` interface until individual page redesign phases are implemented and tested.

## How to use

Maintainers review `documents/design/UI_FOUNDATION.md` and
`documents/design/SCREEN_CATALOG.md`, then validate the intake with:

```bash
python scripts/manage_designs.py --root . check
python scripts/test_designs.py
```

A future page phase selects one current-screen reference, maps every visible control to existing
behavior, updates shared components without redefining the foundation, and delivers one
replacement-ready patch.

## Compatibility

The receive-only Postfix and Dovecot LMTP architecture, Maildir storage, Django routes, MariaDB
contracts, object-level authorization, safe message handling, existing forms, legacy runtime
identifiers, installer, backup and restore behavior remain unchanged. Planned and future-review
controls remain inactive.

## Verification

The intake passed archive CRC, safe-path, PNG decoding, dimension, transparency, exact-duplicate,
hash, naming, visual-consistency, and architecture-scope review. Repository validation adds PNG
chunk and compressed-data checks, manifest synchronization, duplicate-ID blocking, source-tamper
blocking, extra-asset blocking, documentation checks, forensic inventory, full CI, deterministic
release build, and release verification.

## Documentation impact

Added `design/`, seven maintained design-reference documents, this phase record,
`scripts/manage_designs.py`, and `scripts/test_designs.py`. Updated the documentation system, CI,
forensic audit, contribution policy, screen guidance, roadmap, release notes, test evidence, and
changelog to make the design intake immutable and future page work traceable.
