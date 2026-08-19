---
document_id: ui-implementation-status
title: MailStack UI Implementation Status
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.4-rc.2
last_reviewed: 2026-08-18
---

# MailStack UI implementation status

## Purpose

Track design intake, foundation, page implementation, integration, and live acceptance without
misstating incomplete work as delivered.

## Scope

This record covers the 25-image design intake and the page-by-page workflow. It does not replace
phase records, CI evidence, or staging acceptance.

## Approved baseline

| Work item | Status | Evidence |
|---|---|---|
| Design archive integrity | Verified | 25 PNG files, CRC PASS, safe paths, no exact duplicates |
| Original design preservation | Complete | `design/intake/original/` and SHA-256 manifest |
| Screen classification | Complete | Current, planned, future-review, and brand references |
| Shared UI foundation specification | Frozen | `MAILSTACK-UI-FOUNDATION-001` |
| Shared runtime tokens and compatibility aliases | Implemented locally | `static/css/foundation.css` and contract tests |
| Authenticated application shell | Implemented locally | Responsive sidebar, top bar, account menu, active route |
| Unauthenticated sign-in shell | Implemented locally | Local branding and private-navigation isolation |
| Local logo and icon assets | Implemented locally | Canonical logo copy and validated SVG sprite |
| Responsive shell | Implemented locally | Desktop collapse, tablet/mobile drawer, compact mobile shell |
| Released RC4 dependency-backed qualification | Verified in GitHub CI | 198 passed, 0 failed, 95.00% coverage; main and tag CI passed |
| Inbox/message page redesign | Implemented locally in PHASE-005A | Compact inbox and unified message reader; remote CI and live acceptance pending |
| Secure message-reader presentation | Implemented locally in PHASE-005A | Existing sanitizer, CSP, sandbox, and no-referrer isolation preserved |
| Future feature implementation | Not started | Separate architecture phases required |
| PHASE-005A integrated regression audit | In progress | Structural/local gates run before GitHub dependency-backed qualification |
| Staging/live UI acceptance | Not started | Runs after integrated CI qualification |

## Change control

Each page phase updates this record, the matching screen entry where applicable, the phase document,
affected user guides, changelog, tests, and forensic inventory. A page becomes verified only after
functional, visual, responsive, accessibility, security, regression, GitHub CI, and staging evidence
passes. Local structural PASS is not represented as production acceptance.
