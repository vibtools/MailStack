---
document_id: baseline
title: MailStack Baseline
document_type: baseline
audience: maintainers-and-operators
status: active
version: 1.3.2
last_reviewed: 2026-08-18
baseline_id: MAILSTACK-1.3.1-OFFICIAL-SOURCE-BASELINE-001
source_commit: 039a6e6eea6e198b4b15612db9d2f208b6305a16
---

# MailStack baseline

## Baseline identity

The current immutable official source/release baseline is
`MAILSTACK-1.3.1-OFFICIAL-SOURCE-BASELINE-001`, anchored to published tag `v1.3.1`, commit
`039a6e6eea6e198b4b15612db9d2f208b6305a16`, Git tree
`9437ba2ebac2033a229accd190268b8711d5b26e`, and deterministic source archive
`mailstack-1.3.1-source.zip` with SHA-256
`517778967ca491974f315d231dfd43b3dba85fe86b47dcfc63e4c7051d1010bd`.

The earlier published `v1.3.0-rc.4` baseline remains immutable historical release provenance. It is
not rewritten or retagged by the 1.3.1 freeze. PHASE-005A starts from the exact 1.3.1 source tree and
marks the approved development target as `1.3.2`; that working version does not replace this official
baseline until its branch, PR, main, tag, release, and owner acceptance gates complete.

## Qualification status

The 1.3.1 release line passed branch, pull-request, and post-merge `main` CI, including 198 Django
tests at 95.00 percent coverage, Ruff, Bandit, dependency vulnerability audit, Django and migration
drift checks, installer/operations/release/upgrade contracts, full forensic audit with zero blocking
findings, deterministic source build, and release verification. Tag `v1.3.1` points at the exact
qualified `main` merge commit and the automated GitHub Release workflow successfully published the
verified deterministic source ZIP and checksum.

The first real existing-VPS use of the PHASE-004 upgrade mechanism remains deferred. PHASE-005A is
being qualified before that live update so the server is upgraded once to the UI-corrected release
instead of receiving two consecutive application changes.

## Preserved architecture

The baseline preserves the receive-only Postfix and Dovecot LMTP flow, Maildir storage, Django shared
inbox, MariaDB data contracts, Gunicorn/Nginx deployment, systemd services, public site, contact
service, backup/restore tooling, object-scoped mailbox authorization, safe HTML sanitizer, protected
attachments, live polling, audit logging, and established runtime identifiers. It does not add SMTP
submission, outbound sending, IMAP, POP3, public registration, campaigns, or multi-node operation.

PHASE-005A is UI/presentation scoped. Its only server-side behavior exception is a narrow guard that
requires the explicit MailStack background-request header before returning the live-update JSON
payload. Models, migrations, parser/sanitizer policy, permissions, mail flow, deployment templates,
and operational upgrade/rollback semantics remain frozen.

## Change control

Every maintained phase must add or update a phase record under `documents/phases/`, update affected
user-facing guidance when behavior changes, update `CHANGELOG.md`, synchronize documentation/design/
forensic manifests, and pass blocking CI. The `v1.3.1` tag, commit, tree, deterministic archive, and
checksum are immutable inputs to PHASE-005A and must never be force-moved or overwritten.

Existing data contracts, authorization boundaries, receive-only scope, sanitizer/sandbox security,
and deployment compatibility remain protected unless a separately approved phase explicitly changes
them.
