# Changelog

## 1.3.2 — PHASE-005A compact mailbox UI (development)

- Prevented authenticated top-level navigation to the live-update transport from rendering raw JSON; MailStack JavaScript now sends an explicit background-request header and ordinary document requests return to the dashboard UI.
- Rebuilt the inbox as a compact webmail-style list with short previews, unread emphasis, integrated filters, responsive rows, and live-row visual parity.
- Replaced separate plain-text and safe-HTML tabs with one unified message reader that automatically uses the existing sanitized HTML sandbox when available and a plain-text fallback otherwise.
- Preserved sanitizer/CSP/sandbox controls, models/migrations, authorization, mark-unread/delete semantics, attachment handling, ingestion, and receive-only mail flow.

## 1.3.1 — 2026-08-18

- PHASE-004C controlled existing-server upgrade tooling now verifies deterministic release ZIP/SHA assets, creates a coordinated data backup and source rollback snapshot before mutation, stages application/public-site source, converges Python dependencies, gates migrations explicitly, preserves mail-facing services during the source mutation window, and performs post-upgrade verification.
- Added a reviewed source/runtime rollback command that verifies snapshot checksums and refuses implicit database/Maildir restoration or unacknowledged forward-schema rollback.
- Corrected Ruff-only formatting/style findings in the PHASE-004C archive verifier; no upgrade/runtime semantics changed.


## 1.3.0-rc.5 — Forensic/docs baseline finalization (unreleased)

- Finalized RC4 qualification evidence and the official source-baseline record for PHASE-004A.
- No application model, migration, route, UI, mailbox, ingestion, LMTP, authorization, dependency, or runtime behavior changed.

## 1.3.0-rc.4 — Cross-platform audit tooling maintenance

- Added portable Bash runtime discovery for repository-level installer, operations, and forensic audit tooling on Windows while preserving Linux CI behavior.
- No application model, migration, route, UI, mailbox, ingestion, LMTP, authorization, or runtime dependency behavior changed.

## 1.3.0-rc.3 — Dependency security maintenance

- Upgraded the transitive runtime lock for `sqlparse` from 0.5.5 to 0.6.0 to resolve CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and CVE-2026-54284 reported by the blocking GitHub Actions `pip-audit` gate.
- No application model, migration, route, UI, mailbox, ingestion, LMTP, or authorization behavior changed.

## 1.3.0-rc.2 — Installation and inbound-delivery reliability

- Added explicit idempotent repair behavior for the initial administrator and reserved system-mailbox bootstrap commands while preserving strict default duplicate rejection.
- Made one-shot dry-run Maildir verification non-locking and non-mutating so it can run while the live ingestion worker holds the worker lock.
- Qualified deployment-specific MariaDB compatibility warnings without changing models or migrations.

## Unreleased — Django security maintenance

- Upgraded Django from 5.2.15 to 5.2.16 for the July 2026 security fixes.
- Updated production, lock, constraint, preflight, deployment, verification, test, documentation, and inventory contracts to the same exact version.

## 1.2.1 — Security dependency hotfix

- Upgraded Bleach to 6.4.0 for URI sanitization security fixes.
- Upgraded python-dotenv to 1.2.2 for symlink-safe environment-file handling.
- Explicitly disabled Bleach email-address linkification with `parse_email=False`.
- Added AST-enforced dependency-audit scoping for `GHSA-g75f-g53v-794x`.
- Added exact Bleach and python-dotenv version verification during preflight, deployment, and post-deployment verification.
- Rebuilt release scripts, documentation, manifest, and cryptographic package hashes as v1.2.1.

## 1.2.0 — Team access, live inbox, and branding

- Added administrator/ordinary-user separation without replacing Django's existing user model.
- Added user creation, editing, deletion, activation, mailbox assignment, and granular deletion policies.
- Added object-level authorization for dashboard, inbox, message detail, safe HTML, attachments, and live APIs.
- Removed all application password-change and password-reset routes.
- Added shared-mailbox memberships and automatic assignment for user-created mailboxes.
- Added soft message and mailbox deletion with preserved Maildir/data and permanent address reservation.
- Added live inbox, counters, recent-message updates, and accessible new-email notifications.
- Added automatic read-on-open and preserved mark-unread.
- Added click-to-copy email-address controls.
- Updated user-facing branding and footer to MailStack / vib.tools authorized-team-use wording.
- Permanently merged the verified live Nginx proxy-header, TLS-listener, ACME, and dotfile hardening fixes.
- Added v1.2.0 preflight, upgrade, post-deployment verification, rollback, and acceptance documentation.
- Pinned Django 5.2.15 and added exact-version deployment verification.
- Added inter-process duplicate-mailbox provisioning locks and visible-mailbox live counter scoping.
- Added polling timeout/backoff, cross-tab notification locking, and permanent mark-unread behavior.
- Forced restore/rollback commands to use production settings and rejected live-tree release sources.

## 1.1.2

- Normalize virtualenv ownership and group-read/traverse permissions after every pip operation.
- Guarantee the least-privilege `vmail` runtime can import Django and all pinned dependencies.
- Add deployment-asset regression coverage for the virtualenv permission contract.

## 1.1.1

- Force all deployment, administrator-creation, and verification management commands to use `/etc/vibmail/vibmail.env` and `config.settings.production`.
- Execute deployment management commands through an explicit least-privilege `vmail` runtime wrapper.
- Prevent accidental fallback to development settings during Phase 2 maintenance operations.

## 1.1.0 — MariaDB production integration

- Preserved the existing `vibmail` MariaDB Postfix/Dovecot schema as authoritative.
- Added separate `vibmail_app` Django database on the same MariaDB server.
- Added cross-schema transactional mailbox create and enable/disable synchronization.
- Added existing mailbox import and exact mail-server schema verification commands.
- Prevented Django migrations from modifying the live Postfix view on MariaDB.
- Replaced PostgreSQL runtime dependencies and deployment assets with MariaDB-compatible equivalents.
- Updated systemd, backup, documentation, and deployment contracts.

## 1.0.1

- Phase 1 acceptance hotfixes.
