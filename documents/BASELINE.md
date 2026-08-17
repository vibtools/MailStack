---
document_id: baseline
title: MailStack Baseline
document_type: baseline
audience: maintainers-and-operators
status: active
version: 1.3.0-rc.2
last_reviewed: 2026-08-17
baseline_id: MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001
source_commit: 1e1737edea2e6c922265a15d8584b56671820c65
---

# MailStack baseline

## Baseline identity

This documentation baseline is anchored to MailStack `1.3.0-rc.1` and the CI-qualified,
clean-clone-qualified source commit `1e1737edea2e6c922265a15d8584b56671820c65`. The baseline
identifier is `MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001`.

## Qualification status

The baseline has passed source safety, dependency vulnerability, Ruff, Bandit, automated test,
coverage, Django, shell syntax, full forensic, deterministic release-build, release-verification,
and clean-clone gates. Clean Ubuntu 24.04 VPS installation, real inbound SMTP/LMTP delivery,
backup/restore acceptance, and stable release promotion remain pending.

## Preserved architecture

The baseline preserves the receive-only Postfix and Dovecot LMTP flow, Maildir storage, Django
shared inbox, MariaDB data contracts, Nginx and Gunicorn deployment, systemd services, public site,
contact service, backup/restore tooling, and established legacy runtime identifiers. It does not
add SMTP submission, IMAP, POP3, public registration, outbound campaigns, or multi-node operation.

## Change control

The design-governance layer is anchored to commit `068097056cecdd18f39fd304d579563b7b43c491` through
`MAILSTACK-UI-DESIGN-INTAKE-001` and `MAILSTACK-UI-FOUNDATION-001`. This does not replace the runtime source anchor above.

Every future maintained phase must add or update a phase record under `documents/phases/`, update
the affected user-facing guide when behavior changes, update `CHANGELOG.md`, synchronize the
documentation index and manifest, and pass the documentation policy in CI. Existing features,
data contracts, authorization boundaries, and deployment compatibility remain protected unless a
separately approved migration explicitly changes them.
