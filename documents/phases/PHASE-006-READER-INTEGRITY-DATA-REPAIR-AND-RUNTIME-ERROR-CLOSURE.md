---
document_id: phase-006-reader-integrity-data-repair-and-runtime-error-closure
title: Reader Integrity, Data Repair and Runtime Error Closure
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.4-rc.2
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

The RC1 sanitizer removes active/non-display blocks before Bleach allowlist cleaning, removes blocked
remote image nodes instead of leaving broken-image residue, denies scripts, event handlers and unsafe
URLs, and retains safe data-image handling. RC2 narrows the remaining reader-fidelity defect by
preserving presentation-only CSS through an explicit property/function allowlist while continuing to
block CSS resource loading, active behavior, remote tracking and unsafe at-rules. Safe inline style
attributes and bounded sanitized `<style>` rules may survive; external CSS/images/fonts remain denied.

## User-facing changes

Style-heavy HTML emails no longer expose raw CSS text as message body content. RC2 additionally
preserves a bounded, sanitized subset of sender presentation CSS so typography, spacing, sizing,
colors, tables and responsive `@media` rules can render more faithfully without re-enabling remote
resources or active content. Blocked remote images still leave no broken-image residue. The permanent
protected-rendering banner remains absent while sandbox, no-referrer isolation, sanitization and
active-content restrictions remain in force.

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

RC1 local focused qualification on Python 3.12 completed with 60 PHASE-006 tests passing. Targeted
Ruff, Bandit, Django system checks and migration-drift checks passed. Implementation commit
`90175b7a4549cb67d874692081bd5b0484eddccc` passed GitHub Actions CI run `32183300485`; the
qualified work was later squash-merged through PR #12 to `main` at
`212ccaf7fab94e1b42ef2a57afb7bdfee673667e` and tagged `v1.3.4-rc.1`. Controlled RC1 reader
acceptance retained the security correction but exposed insufficient original HTML/CSS presentation
fidelity, so PHASE-006 remains open for the narrowly scoped RC2 continuation.

RC2 qualification closure also advances the pinned Django 5.2 LTS runtime from 5.2.16 to 5.2.17 after the local `pip-audit` gate identified the upstream advisory, synchronizes the active exact-version deployment/security-test contracts, and removes Bandit B105 false positives through a semantics-only CSS parser local-variable rename rather than suppressing the security rule. No reader, mail-flow, schema, authorization, iframe/CSP, installer, or deployment-flow behavior is changed by that maintenance step.

The combined RC2 implementation/dependency candidate passed local qualification on Python 3.12.8 before release-identity promotion: focused reader/repair/security/auth/deployment suites PASS; full suite `223 passed, 1 skipped`; coverage `93.03%`; Ruff and Bandit PASS; Django system check PASS; migration drift NONE; dependency consistency PASS; `pip-audit` reported no known vulnerabilities; documentation/design/installer/operations/release/upgrade gates PASS; and standard/full forensic audits reported zero blocking findings. The owner-approved release identity is now `1.3.4-rc.2`; post-promotion local requalification, GitHub branch/main CI and controlled live acceptance remain pending. Acceptance must verify
representative inline-style, style-block, table-layout and responsive HTML, malicious/remote CSS
rejection, plain-text fallback, dry-run and bounded existing-message repair, health/service status,
and continued absence of the previously observed repeated Gunicorn control-server filesystem finding.

## Documentation impact

This RC2 release-identity candidate synchronizes the canonical version, CI artifact identity, current release/publishing guidance, managed-document versions, design/documentation metadata and forensic inventory with the already qualified scoped parser/dependency/tests. It does not claim PHASE-006 completion, GitHub CI success, tag publication or live acceptance. Final completion status is recorded only after post-promotion qualification, GitHub CI and controlled live acceptance gates pass.
