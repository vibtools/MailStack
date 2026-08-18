---
document_id: ui-screen-catalog
title: MailStack UI Screen Catalog
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.4-rc.1
last_reviewed: 2026-08-18
---

# MailStack UI screen catalog

## Purpose

Provide the authoritative mapping between immutable source PNG files, stable screen IDs, current
runtime capability, planned work, and architecture-review boundaries.

## Scope

The catalog covers all 25 imported PNG files. It records current redesign references, planned
feature references, future architecture reviews, and brand references. It does not mark any page
as implemented.

## Approved baseline

| ID | Screen | Original file | Lifecycle | Architecture review |
|---|---|---|---|---|
| UI-001 | Backup | `Backup.png` | Planned feature reference | No |
| UI-002 | Connect Your Mail Accounts | `Connect Your Mail Accounts.png` | Future architecture review | Yes |
| UI-003 | Create Mailbox | `Create-mailbox.png` | Current redesign reference | No |
| UI-004 | Create Team | `Create-Teams.png` | Planned feature reference | No |
| UI-005 | Create User | `Create-User.png` | Current redesign reference | No |
| UI-006 | Future Dashboard | `dashboard-Future.png` | Future architecture review | Yes |
| UI-007 | Dashboard | `Dashboard.png` | Current redesign reference | No |
| UI-008 | Domain and DNS | `Domain & DNS.png` | Planned feature reference | No |
| UI-009 | Domains | `Domain.png` | Planned feature reference | No |
| UI-010 | Public Homepage | `Homepage.png` | Current redesign reference | No |
| UI-011 | Inbox | `Inbox.png` | Current redesign reference | No |
| UI-012 | Primary Logo Reference | `Logo.png` | Brand reference | No |
| UI-013 | Logs | `Logs.png` | Planned feature reference | No |
| UI-014 | Mailboxes | `Mailboxes.png` | Current redesign reference | No |
| UI-015 | Profile | `profile.png` | Planned feature reference | No |
| UI-016 | Roles and Permissions | `Role & Permisson.png` | Planned feature reference | No |
| UI-017 | Services Overview | `Services Overview.png` | Planned feature reference | No |
| UI-018 | Settings | `Settings.png` | Planned feature reference | No |
| UI-019 | Setup and Install Welcome | `Setup & Install - Welcome page.png` | Planned feature reference | Yes |
| UI-020 | Teams | `Teams.png` | Planned feature reference | No |
| UI-021 | User Login Option A | `User-Login-1.png` | Current redesign reference | No |
| UI-022 | User Login Option B | `User-login-2.png` | Current redesign reference | No |
| UI-023 | User Management | `User-managments.png` | Current redesign reference | No |
| UI-024 | User Signup | `User-signup.png` | Future architecture review | Yes |
| UI-025 | Web Logo Reference | `Web-Logo.png` | Brand reference | No |

The machine-readable authority is `design/DESIGN_MANIFEST.json`. Original misspellings and mixed
capitalization remain only in immutable source filenames; display names and stable IDs are
corrected in the catalog.

PHASE-005A applies the current `UI-011` Inbox reference to a compact receive-only inbox and unified
message reader. This does not activate any planned/future feature or outbound-mail control.

## Change control

New or replaced designs must retain source provenance, receive a unique screen ID, pass PNG and
hash validation, receive a current/planned/future classification, update implementation status,
and be included in a phase and changelog. A visual control does not authorize new business logic.
