# MailStack 1.3.0 RC2 release notes

## Purpose

Version 1.3.0 RC2 is a reliability-hardening release candidate built from the frozen 1.3.0 RC1
baseline. It incorporates only the installation, partial-recovery, official-verification, MariaDB
qualification, and inbound SMTP/LMTP fixes reproduced during the first live Ubuntu 24.04 staging
acceptance campaign. Existing MailStack product features, UI/UX, routes, data model, receive-only
scope, and deployment identifiers remain preserved.

## Fixed in RC2

- The installer no longer changes the host-wide `/var/log` mode; it validates the dedicated MailStack
  log path from the `vmail` runtime instead.
- Installer-launched Django commands now run from a clean least-privilege environment instead of
  inheriting stale database/Django variables from the parent shell.
- `/run/vibmail/mailbox-provision-locks` is prepared before bootstrap mailbox creation.
- Reviewed `--repair` can preserve a valid existing initial administrator and valid system mailboxes
  while creating only missing bootstrap objects; inconsistent partial state fails closed.
- Newly created initial-administrator credentials are persisted immediately to the root-only
  credential file, before later TLS/mail-stack phases can fail.
- Dovecot's static LMTP userdb includes `allow_all_users=yes`; Postfix SQL virtual-mailbox lookup
  remains the authoritative recipient gate, so unknown recipients are still rejected.
- One-shot `ingest_maildir --dry-run` verification no longer takes the live worker's exclusive lock
  and no longer updates `ServiceHeartbeat`, allowing the official application verifier to run beside
  the live ingestion service.
- Conservative Django MariaDB uniqueness warnings are qualified only in production against the
  existing `utf8mb4_unicode_ci` database and unique-column deployment contract; no migration or
  schema change is introduced.
- SSH/PuTTY installation guidance now recommends `tmux`/`screen`, with a non-blocking warning when a
  mutating installer is launched over SSH outside a resilient terminal.

## Compatibility

- No database migration.
- No dependency upgrade or new dependency.
- No route, template, CSS, JavaScript, UI page, authorization, mailbox, message, public-site, or
  contact-workflow redesign.
- No SMTP submission, IMAP, POP3, reply, forward, sent, draft, or public-registration feature.
- Existing `VIBMAIL_*` settings, `vibmail-*` services, `/etc/vibmail` paths, databases, Maildir
  layout, and receive-only architecture remain unchanged.
- Strict duplicate rejection remains the default for bootstrap management commands; preservation is
  available only through the explicit repair option.

## Staging evidence that motivated RC2

The live campaign reproduced and isolated failures in `/var/log` traversal, inherited installer
credentials, mailbox provisioning runtime locks, partial bootstrap recovery, delayed initial
credential persistence, Dovecot static-userdb LMTP lookup, and live verification locking. After the
LMTP correction, deferred Gmail messages were accepted by Dovecot, saved to INBOX, removed from the
Postfix queue, ingested, and displayed by the application.

## Release qualification

RC2 must pass the full documentation, installer, operations, template, Ruff, Bandit, Django,
coverage, forensic, deterministic-release, and CI gates. Clean Ubuntu 24.04 installation and real
external SMTP/LMTP acceptance are required. Stable promotion remains blocked until backup/restore,
restart-recovery, final security/legal, and release-owner acceptance are complete.

## RC1 foundation preserved

RC1 established the configurable Ubuntu 24.04 installer, MariaDB/Postfix/Dovecot/Nginx/systemd
templates, reproducible source packaging, public governance/security documentation, Django 5.2.16
security pin, protected user/documentation baseline, UI design intake, and shared application shell.
RC2 does not replace or redesign those foundations; it hardens the operational paths exercised by
staging acceptance.
