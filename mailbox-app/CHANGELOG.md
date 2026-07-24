# Changelog

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
