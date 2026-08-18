# MailStack 1.3.4-rc.1 — PHASE-006 live-acceptance candidate

## Purpose

`1.3.4-rc.1` is the owner-approved PHASE-006 pre-release identity for controlled production
acceptance of the reader-integrity, existing-message repair, and Gunicorn runtime-finding fixes.
The frozen production baseline remains published/live-verified `v1.3.3`.

This pre-release does not mark PHASE-006 complete. Controlled upgrade, dry-run/backfill evidence,
reader acceptance, health checks, and bounded log observation remain blocking.

## Included corrections

- remove style/head/active block contents before allowlist sanitization so raw CSS is not visible;
- keep scripts, event handlers, unsafe URLs, style attributes and unrestricted remote assets blocked;
- remove blocked remote-image nodes instead of leaving broken-image residue;
- retain sandbox/no-referrer HTML isolation and plain-text fallback;
- remove the permanent protected-rendering notice while retaining the protections;
- add bounded, dry-run-first existing-message body repair from preserved Maildir source;
- preserve UUID/database identity, mailbox, read/deleted state, source identity and attachments;
- disable the unused Gunicorn control interface without weakening `ProtectSystem=strict`.

## Qualification evidence

PHASE-006 implementation commit `90175b7a4549cb67d874692081bd5b0484eddccc` passed GitHub Actions
CI run `32183300485`, including source safety, documentation/metadata, forensic inventory,
deployment/installer/backup/upgrade contracts, dependency audit, Ruff, Bandit, full tests+coverage,
Django checks, shell syntax, full forensic audit, deterministic build and release verification.

The release-identity delta must pass a new branch CI run, then PR/main CI and exact-main tag
publication before live deployment.

## Compatibility

No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization redesign, outbound
mail capability, or PHASE-007 broad UI redesign is included.

## Live acceptance sequence

Use the maintained upgrader with the official deterministic ZIP/checksum, verify services and health,
run repair dry-run first, review counters, run only the approved bounded mutation, verify previously
broken HTML plus plain-text/attachments/state preservation, demonstrate idempotence, and observe logs
for absence of the repeated Gunicorn control-server read-only-filesystem finding.
