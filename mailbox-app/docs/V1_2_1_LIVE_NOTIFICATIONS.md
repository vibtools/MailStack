# Live inbox and notification behavior

The browser polls the authenticated live endpoint approximately every five seconds while visible and less frequently while hidden. Requests never overlap and failures use exponential backoff.

The first request is a bootstrap and does not notify for historical email. Later responses use a database message-ID cursor. Payloads are bounded and contain no message body or attachment data.

Notifications are deduplicated across tabs with browser storage and `BroadcastChannel` when supported. All email-controlled values are inserted with `textContent`.
