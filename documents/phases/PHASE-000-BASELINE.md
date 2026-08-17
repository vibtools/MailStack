---
document_id: phase-000-baseline
title: Documentation and Feature Baseline
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.0-rc.2
last_reviewed: 2026-08-17
phase_id: PHASE-000
---

# PHASE-000: Documentation and feature baseline

## Objective

Freeze the CI-qualified and clean-clone-qualified MailStack `1.3.0-rc.1` behavior as the protected
starting point for future phases, and establish a mandatory user-documentation lifecycle.

## Scope

This phase adds the root `documents/` information architecture, complete initial user and
administrator guides, a baseline record, a documentation policy, a deterministic index and
manifest generator, a phase-record generator, documentation contract tests, and CI enforcement.
It does not change application runtime behavior, database migrations, mail flow, authorization,
deployment service names, or legacy compatibility identifiers.

## User-facing changes

Users and administrators receive a maintained user manual, task-based how-to guide, and
administrator guide describing the current supported interface and safety boundaries. The
application itself is unchanged.

## How to use

Read `documents/USER_MANUAL.md` for product behavior, `documents/HOW_TO_USE.md` for task workflows,
and `documents/ADMIN_GUIDE.md` for user, mailbox, and operational administration. Contributors use
`scripts/manage_documents.py new-phase` before implementing the next maintained phase, then run
`sync` and `check` after editing the affected guides.

## Compatibility

All existing MailStack `1.3.0-rc.1` features and deployment contracts remain preserved. The
baseline remains receive-only and single-node. The new enforcement applies to future repository
changes and does not rename `VIBMAIL_*`, `vibmail-*`, `/etc/vibmail`, database identifiers,
`vibmail.my`, or legacy protocol headers.

## Verification

The documentation framework is verified through deterministic synchronization, metadata and
section validation, draft blocking, change-policy classification tests, general link checking,
forensic inventory validation, full repository audit, CI, deterministic source build, and release
verification.

## Documentation impact

Added `documents/README.md`, `USER_MANUAL.md`, `HOW_TO_USE.md`, `ADMIN_GUIDE.md`, `BASELINE.md`,
`DOCUMENTATION_POLICY.md`, `DOCUMENTATION_MANIFEST.json`, and this phase record. Updated root
contribution, roadmap, release, structure, test, forensic, README, changelog, and pull-request
documentation to make the workflow mandatory.
