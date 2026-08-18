---
document_id: baseline
title: MailStack Baseline
document_type: baseline
audience: maintainers-and-operators
status: active
version: 1.3.0-rc.5
last_reviewed: 2026-08-17
baseline_id: MAILSTACK-1.3.0-RC4-OFFICIAL-SOURCE-BASELINE-001
source_commit: 896dbcc2ed1f38d9c618bf0b712efe5923f92e56
---

# MailStack baseline

## Baseline identity

The current official source baseline is `MAILSTACK-1.3.0-RC4-OFFICIAL-SOURCE-BASELINE-001`. It is
anchored to published tag `v1.3.0-rc.4`, commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56`, and Git tree
`0d845b3d975949894c24581e6834aff7b33c30b4`. The deterministic source archive is
`mailstack-1.3.0-rc.4-source.zip` with SHA-256
`58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`.

The earlier `MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001`, anchored to commit
`1e1737edea2e6c922265a15d8584b56671820c65`, remains historical documentation provenance. It no
longer represents the current canonical source anchor. The repository development version is
`1.3.0-rc.5`; that identity begins PHASE-004 and does not rewrite the frozen RC4 tag or archive.

## Qualification status

The RC4 baseline passed source safety, documentation and design gates, installer and operations
contracts, dependency vulnerability audit, Ruff, Bandit, Django checks, migration-drift checks, 198
application tests at 95.00 percent coverage, full forensic audit, deterministic release build, and
release verification. The post-merge `main` CI run `32071701530`, tag CI run `32072699991`, and
release-artifact workflow `32072699830` all completed successfully.

PHASE-003 staging also demonstrated real external Gmail delivery through Postfix and Dovecot LMTP
into Maildir, ingestion, and browser visibility after the accepted fixes. An exact RC4 clean-host
reinstall is deferred until a fresh VPS is available. Backup/restore acceptance, restart/reboot
recovery, final ownership/license review, and stable promotion remain outstanding operational or
human gates.

## Preserved architecture

The baseline preserves the receive-only Postfix and Dovecot LMTP flow, Maildir storage, Django
shared inbox, MariaDB data contracts, Nginx and Gunicorn deployment, systemd services, public site,
contact service, backup/restore tooling, and established legacy runtime identifiers. It does not
add SMTP submission, IMAP, POP3, public registration, outbound campaigns, or multi-node operation.

PHASE-004A changes documentation, version/release metadata, and generated manifests only. It does
not alter application runtime behavior, database schema, migrations, routes, permissions, UI, mail
flow, installer behavior, deployment templates, or service configuration.

## Change control

The design-governance layer remains anchored to commit
`068097056cecdd18f39fd304d579563b7b43c491` through `MAILSTACK-UI-DESIGN-INTAKE-001` and
`MAILSTACK-UI-FOUNDATION-001`; it does not replace the current source anchor above.

Every future maintained phase must add or update a phase record under `documents/phases/`, update
the affected user-facing guide when behavior changes, update `CHANGELOG.md`, synchronize the
documentation/design/forensic manifests required by repository policy, and pass the blocking CI
gates. Existing features, data contracts, authorization boundaries, receive-only scope, and
deployment compatibility remain protected unless a separately approved migration explicitly
changes them.
