---
document_id: future-ui-roadmap
title: MailStack Future UI Roadmap
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# MailStack future UI roadmap

## Purpose

Preserve future concepts without confusing visual approval with implementation approval.

## Scope

The roadmap includes backup administration, connected accounts, teams, roles and permissions,
domains and DNS, service overview, settings, profile, logs, browser setup, future dashboard,
public signup, and broader inbox actions.

## Approved baseline

### Planned after existing-screen redesign

- Backup administration
- Domain and DNS verification
- Domains
- Teams and team creation
- Roles and permissions
- Service overview
- Settings
- Profile
- Logs presentation

### Separate architecture review required

- External mail-account connection
- Browser-based privileged installation
- Public signup or invite onboarding
- Outbound sending, reply, reply-all, forward, sent, drafts, spam, and generalized folders
- Multi-domain delivery and authorization changes

The receive-only single-node baseline remains authoritative until a separately approved phase adds
and verifies a new capability.

## Change control

A future feature must begin with requirements, threat model, data and permission design, migration
and rollback plan, API and UI contract, automated tests, documentation, and staged acceptance. No
navigation item or inactive control is added solely because it appears in the design archive.
