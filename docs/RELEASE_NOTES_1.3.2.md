# MailStack 1.3.2 PHASE-005A notes

## Scope

MailStack 1.3.2 is the PHASE-005A UI-navigation reliability and compact mailbox-reader update built
from the immutable published `v1.3.1` source baseline. It changes the mailbox/message presentation
layer and the narrow live-update request contract only. It does not add outbound mail, alter mailbox
permissions, change models or migrations, relax HTML sanitization, change Postfix/Dovecot delivery,
or modify Maildir, MariaDB, DNS, TLS, installer, backup, upgrade, or rollback semantics.

## Navigation reliability

The authenticated live-update JSON endpoint now requires an explicit background-request header from
MailStack JavaScript. A normal authenticated document navigation to `/messages/live/` is redirected
to the application dashboard rather than rendering the JSON payload as a browser page. The live
poller sends the required header and retains same-origin credentials, private no-store responses,
bounded payloads, authorization filtering, polling backoff, and notification behavior.

## Compact inbox

Mailbox inbox pages now use a denser webmail-style surface with a compact mailbox header, integrated
search/read/attachment filters, tighter sender/subject rows, unread emphasis, short message preview,
attachment/size metadata, and responsive desktop/mobile layout. Live-inserted rows use the same
presentation contract as server-rendered rows.

## Unified message reader

The visible `Plain text` / `Safe HTML` tabs are removed. When sanitized HTML exists, the message is
shown automatically in the existing sandboxed, no-referrer safe frame. Plain-only messages are shown
as a readable unified fallback. The reader uses a compact subject/sender/action header, expandable
routing metadata, integrated protected-rendering notice, and compact attachment section. Sanitizer
rules, CSP isolation, object authorization, mark-unread, delete permissions, and attachment download
controls remain unchanged.

## Qualification boundary

The replace-ready PHASE-005A delta must pass the repository structural gates locally and the complete
Python 3.12 dependency-backed GitHub CI suite before merge or release. Existing-live-VPS deployment is
intentionally deferred until the 1.3.2 branch, PR, main, tag, and release checks are complete.
