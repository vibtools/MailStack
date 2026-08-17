# MailStack 1.3.0 RC4 release notes

## Purpose

Version 1.3.0 RC4 is a cross-platform audit-tooling maintenance successor to RC3. It preserves the
frozen 1.3.0 RC1 product baseline, all approved RC2 installation/recovery/inbound-delivery fixes, and
the RC3 `sqlparse` 0.6.0 security update. RC4 changes only repository-level Bash runtime discovery
used by installer, operations, and forensic contract tooling so Windows validation does not blindly
invoke a broken WSL `bash.exe` launcher when Git Bash is available. Existing MailStack product
features, UI/UX, routes, data model, receive-only scope, runtime dependencies, and deployment
identifiers remain preserved.

## Local Windows audit fix in RC4

A Windows CMD qualification run showed documentation, design, UI-foundation, inventory, and template
gates passing, while installer/operations shell checks failed before any MailStack shell code ran.
The `bash` command resolved to the Windows WSL launcher, which failed to attach Docker Desktop's WSL2
`ext4.vhdx` with `E_ACCESSDENIED`. The forensic audit then repeated the same environment failure for
every shell syntax check, creating 16 cascading findings from one unusable Bash runtime.

RC4 introduces verified Bash discovery for repository tooling. On Windows it prefers Git for Windows
Bash, supports an explicit `BASH_EXECUTABLE` override, probes candidates before use, and passes
repository-relative POSIX script paths. Linux/GitHub Actions continue to use the normal system Bash.
If no usable Bash exists, the tools fail once with an actionable runtime diagnostic instead of
misclassifying WSL startup failure as multiple MailStack shell syntax defects.

## Security fix carried from RC3

GitHub Actions run `32053931714` passed the source forensic audit, documentation, design, inventory,
deployment-template, installer, and operations gates, then stopped at the blocking online dependency
audit. `pip-audit` reported four vulnerabilities in `sqlparse==0.5.5`: CVE-2026-71491,
CVE-2026-59894, CVE-2026-59893, and CVE-2026-54284, with 0.6.0 as the fixed version.

RC3 introduced, and RC4 preserves, the existing transitive runtime pin to `sqlparse==0.6.0` in both the production lock and
constraints. Django remains 5.2.16 and declares `sqlparse>=0.3.1`; sqlparse 0.6.0 requires Python
3.10+, while MailStack remains fixed to Python 3.12. No new dependency is introduced.

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
- One existing transitive dependency is security-upgraded: `sqlparse` 0.5.5 → 0.6.0; no new dependency is introduced.
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

RC4 must pass the full documentation, installer, operations, template, Ruff, Bandit, Django,
coverage, forensic, deterministic-release, and CI gates. Clean Ubuntu 24.04 installation and real
external SMTP/LMTP acceptance are required. Stable promotion remains blocked until backup/restore,
restart-recovery, final security/legal, and release-owner acceptance are complete.

## RC1 foundation preserved

RC1 established the configurable Ubuntu 24.04 installer, MariaDB/Postfix/Dovecot/Nginx/systemd
templates, reproducible source packaging, public governance/security documentation, Django 5.2.16
security pin, protected user/documentation baseline, UI design intake, and shared application shell.
RC4 does not replace or redesign those foundations; it preserves the RC2 operational hardening and RC3 dependency-security fix while hardening only cross-platform repository audit execution.
