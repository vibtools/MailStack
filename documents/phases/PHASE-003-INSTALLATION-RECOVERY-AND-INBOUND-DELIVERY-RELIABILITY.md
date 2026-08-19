---
document_id: phase-003-installation-recovery-and-inbound-delivery-reliability
title: Installation, Recovery and Inbound Delivery Reliability
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.4-rc.2
last_reviewed: 2026-08-18
phase_id: PHASE-003
---

# PHASE-003: Installation, recovery and inbound delivery reliability

## Objective

Harden the existing Ubuntu 24.04 installation, partial-install recovery, official verification, and
Postfix-to-Dovecot inbound-delivery path using failures reproduced during the first live staging
acceptance campaign, without changing MailStack product features or UI behavior.

## Scope

This phase is restricted to the ten installation and setup issues reproduced during live staging:
global `/var/log` permission mutation, inherited shell-environment contamination, missing mailbox
provisioning runtime directories, non-idempotent partial-install bootstrap recovery, delayed initial
administrator credential persistence, Dovecot static-userdb LMTP lookup failure, the official
verification script conflicting with the live ingestion lock, SSH/PuTTY session-resilience guidance,
qualified MariaDB compatibility warnings, and source/staging hotfix drift.

No application page, URL, permission model, mailbox/message workflow, public-site feature, outbound
mail capability, database migration, dependency, service name, or legacy runtime identifier is
added, removed, renamed, or redesigned.

## User-facing changes

There are no UI changes. Operators receive a safer clean/repair installer, a repair path that can
preserve already-valid bootstrap objects while creating missing ones, earlier root-only persistence
of newly created administrator credentials, reliable LMTP delivery for Postfix-validated recipients,
and an application verifier that can run beside the live ingestion worker.

## How to use

Run mutating installation or repair commands inside `tmux` or `screen` when connected through SSH.
Use the normal clean installer only on an unmarked target. After a reviewed interrupted or partial
installation, rerun the same source and parameters with `--repair`; valid existing administrator and
system-mailbox bootstrap objects are preserved and only missing objects are created. The installer
never silently resets an existing administrator password.

After installation, run `/opt/vibmail/app/scripts/health_check.sh` followed by
`/opt/vibmail/app/scripts/verify_application.sh` while the normal ingestion service remains active.
Complete acceptance with a real external message to an active mailbox and confirm Postfix acceptance,
Dovecot LMTP delivery, Maildir persistence, ingestion, and browser visibility.

## Compatibility

All baseline application behavior remains unchanged. The Postfix SQL mailbox table remains the
authoritative recipient gate; Dovecot's static userdb now trusts recipients already validated by
Postfix and therefore does not introduce catch-all delivery. Existing administrator passwords are
preserved during repair. Existing strict duplicate behavior remains the default for management
commands; idempotent preservation is available only through the explicit repair option.

No database migration is introduced. MariaDB continues to use the configured
`utf8mb4_unicode_ci` application-database collation, and existing unique columns remain unchanged.
The two conservative Django/MariaDB warnings qualified by that deployment contract are silenced only
in production settings. Rollback is the baseline `1.3.0-rc.1` source plus the previously documented
manual staging workarounds; existing data does not require migration or rollback transformation.

## Verification

Regression coverage verifies that the installer does not change global `/var/log` permissions,
least-privilege Django commands run from a sanitized environment, runtime provisioning directories
exist before bootstrap, repair preserves valid existing administrator/system mailboxes, initial
credentials are persisted immediately after administrator creation, the Dovecot template includes
the static-userdb LMTP fix, and MariaDB collation/warning qualification remains narrow.

Django tests verify strict default bootstrap behavior, explicit `--if-missing` recovery, inconsistent
repair-state rejection, exclusive locking for real ingestion, concurrent one-shot dry-run verification,
and zero ServiceHeartbeat mutation during dry-run. Qualification also requires documentation,
template, installer, operations, Ruff, Bandit, Django, forensic, deterministic-release, and full CI
gates plus clean Ubuntu 24.04 external SMTP/LMTP acceptance before stable promotion.

## Documentation impact

Updated the root and application changelogs, README release status, installation, quick-start,
operations, troubleshooting, release-process/build/publishing references, security/citation metadata,
roadmap qualification notes, release notes, administrator guidance, versioned managed-document
metadata, generated documentation/design/forensic manifests, and this PHASE-003 record.
