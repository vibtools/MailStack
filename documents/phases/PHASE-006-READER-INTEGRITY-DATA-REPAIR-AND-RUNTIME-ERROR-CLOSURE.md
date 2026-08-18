---
document_id: phase-006-reader-integrity-data-repair-and-runtime-error-closure
title: Reader Integrity, Data Repair and Runtime Error Closure
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.4-rc.1
last_reviewed: 2026-08-18
phase_id: PHASE-006
---

# PHASE-006: Reader integrity, data repair and runtime error closure

## Objective

Correct the production-blocking HTML email rendering defect without weakening MailStack's receive-only
security boundary, provide a controlled repair path for already-indexed affected messages, and close
the observed Gunicorn control-interface filesystem finding with a narrow source-level correction.

## Scope

PHASE-006 changes only the safe message-rendering path, existing-message body repair tooling, the
message-reader security notice presentation, focused regression coverage, and the unused Gunicorn
control-interface setting. It does not redesign the broader authenticated UI, change database schema,
alter Postfix/Dovecot/LMTP/Maildir routing, change mailbox authorization, or add outbound mail.

The sanitizer now removes non-body style/active blocks with their contents before Bleach allowlist
cleaning, removes blocked remote image nodes instead of leaving broken-image residue, preserves the
existing deny policy for scripts, event handlers, style attributes and unsafe URLs, and retains safe
data-image handling.

## User-facing changes

Style-heavy HTML emails no longer expose raw CSS text from stripped style blocks. Blocked remote
images no longer leave broken-image residue. The permanent protected-rendering banner is removed from
the normal message-reading surface while the sandbox, no-referrer isolation, sanitization and active
content restrictions remain in force.

Already-indexed messages are not silently rewritten during normal ingestion. Administrators receive
a separate controlled repair command so stored body fields can be regenerated from their verified
Maildir source without delete/re-ingest behavior.

## How to use

Normal mailbox users continue to open messages from the Inbox; no new user action is required.

For administrator-controlled repair after the corrected source is deployed, run a bounded dry-run
first:

```text
python manage.py repair_message_bodies --dry-run --limit 500
```

After reviewing the counters and errors, explicitly authorize the same bounded repair:

```text
python manage.py repair_message_bodies --confirm-repair --limit 500
```

Use `--mailbox <local-part>` or `--message <uuid>` to narrow the operation when needed.

## Compatibility

No database migration is introduced. The repair operation updates only parser-derived `text_body` and
`sanitized_html_body` fields and preserves message UUID, database identity, mailbox membership,
read/unread state, deletion state, source identity and attachment records.

Receive-only behavior, object authorization, attachment authorization, Postfix/Dovecot LMTP, Maildir,
MariaDB, installer, backup, upgrade and rollback contracts remain unchanged. The Gunicorn correction
disables the unused control interface through `gunicorn.conf.py`; it does not relax
`ProtectSystem=strict` or add broad writable filesystem access.

## Verification

Local focused qualification on Python 3.12 completed with 60 PHASE-006 tests passing. Targeted Ruff,
Bandit, Django system checks and migration-drift checks passed. Implementation commit
`90175b7a4549cb67d874692081bd5b0484eddccc` then passed GitHub Actions CI run `32183300485`.
The owner approved `1.3.4-rc.1` as the PHASE-006 live-acceptance pre-release identity. PR/main/tag
publication and controlled live acceptance remain required before PHASE-006 is complete.

Controlled live acceptance must verify representative style-heavy HTML, plain-text fallback, dry-run
and bounded existing-message repair, health/service status, and absence of the previously observed
repeated Gunicorn control-server read-only-filesystem finding.

## Documentation impact

PHASE-006 updates this phase record, the root changelog, user/admin guidance, the production-readiness
status ledger, generated documentation metadata and the forensic inventory. Final completion status
is recorded only after GitHub and controlled live acceptance gates pass.
