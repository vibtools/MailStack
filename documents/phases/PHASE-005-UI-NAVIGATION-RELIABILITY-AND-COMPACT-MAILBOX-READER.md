---
document_id: phase-005-ui-navigation-reliability-and-compact-mailbox-reader
title: UI Navigation Reliability and Compact Mailbox Reader
document_type: phase
audience: users-operators-designers-and-maintainers
status: active
version: 1.3.2
last_reviewed: 2026-08-18
phase_id: PHASE-005
---

# PHASE-005A: UI navigation reliability and compact mailbox reader

## Objective

Remove the user-visible raw-JSON navigation failure mode and replace the split plain-text/HTML
message-detail presentation with a compact receive-only mailbox and unified safe message reader.
The immutable implementation input is published MailStack `v1.3.1`, commit
`039a6e6eea6e198b4b15612db9d2f208b6305a16`, tree
`9437ba2ebac2033a229accd190268b8711d5b26e`, deterministic source SHA-256
`517778967ca491974f315d231dfd43b3dba85fe86b47dcfc63e4c7051d1010bd`.

## Scope

PHASE-005A is limited to mailbox/message UI presentation, the browser-side live polling request, and
the narrow server-side presentation guard needed to prevent the live JSON endpoint from being used
as a top-level document. Inbox rows gain compact sender/subject/preview metadata and live-inserted
rows use the same presentation contract. Message detail automatically chooses the already-sanitized
HTML body when present and otherwise renders the existing plain-text body as a unified fallback.

The message preview is derived only from already-indexed `text_body` or sanitized HTML text. No new
message field, migration, parser behavior, persistence contract, or mail flow is introduced.

## User-facing changes

Authenticated direct navigation to the live-update endpoint no longer displays raw JSON; normal
browser navigation is redirected to the dashboard, while MailStack's explicit background request
continues to receive JSON. Mailbox inboxes use a denser webmail-style layout with integrated filters,
unread emphasis, previews, attachment indication, and responsive compact rows.

The message reader no longer exposes separate `Plain text` and `Safe HTML` tabs. Sanitized HTML is
shown automatically inside the existing sandboxed/no-referrer isolation, and plain-only messages use
a single readable fallback. Sender, routing details, actions, warnings, and attachments are arranged
as one compact reader rather than several disconnected panels.

## How to use

Open a mailbox from **Mailboxes**, search or filter in the compact toolbar, and select a message row.
The message opens in one reader automatically; users do not select a body format. Use **Mark unread**
or the permission-gated **Delete** action from the reader header. Expand the recipient summary when
full routing, timestamp, size, or parse-status metadata is needed. Attachments remain explicit
downloads and remain marked as not antivirus scanned.

## Compatibility

PHASE-005A preserves receive-only operation, authentication, object authorization, mailbox
membership, message read/unread semantics, deletion permissions, attachment authorization, parser
and sanitizer rules, CSP and iframe sandboxing, database models/migrations, Postfix/Dovecot LMTP,
Maildir, MariaDB, public-site/contact behavior, deployment templates, installer, backup/restore, and
PHASE-004 upgrade/rollback semantics. No compose, reply, forward, sent, draft, IMAP, POP3, or public
registration capability is added.

The version-specific CI/release artifact paths are synchronized from `1.3.1` to the approved `1.3.2`
target so the existing release workflow verifies and publishes the correct deterministic artifact
and release-note file. This is version metadata synchronization, not a release-workflow behavior
redesign.

## Verification

Blocking verification includes direct-navigation and background-live-request regression tests,
compact inbox rendering, live/server row parity, HTML-to-text preview fallback, unified HTML reader,
plain-only fallback, retained sandbox/no-referrer security controls, search/filter/pagination,
responsive CSS, existing live authorization and query-bound tests, the complete Django test suite,
Ruff, Bandit, dependency audit, Django/migration checks, documentation/design/inventory gates, full
forensic audit, and deterministic source build/release verification. Local artifact qualification is
not represented as live-VPS acceptance; the first existing-server update remains deferred until the
1.3.2 release line is remotely qualified.

## Documentation impact

This phase updates the root and application changelogs, README release status/build examples, user
manual/how-to message-reading guidance, baseline record, UI implementation status, API/security and
feature documentation, 1.3.2 release notes, build/publishing/release-process examples, generated
documentation/design/forensic inventories, and this phase record. Historical `v1.3.1` release notes
and immutable release artifacts are retained unchanged.
