# MailStack v1.2.1 Performance Audit Report

## Result

**PASS for the release architecture and local acceptance workload**

## Verified design

- Existing Gunicorn threaded worker model preserved
- Mail ingestion remains independent of browser activity
- Polling defaults to approximately five seconds and reduces while the tab is hidden
- Overlapping live requests are prevented
- Live requests have a 12-second abort timeout and exponential backoff up to 60 seconds
- New-message responses and mailbox-counter responses are bounded
- Visible mailbox UUIDs are supplied so paginated rows beyond the global counter limit still update
- Message bodies and attachments are excluded from live payloads
- Dashboard, inbox, mailbox list, and user list use bounded pagination
- Authorization querysets use related-object selection and indexed membership lookups
- Query-count tests remain bounded with increasing mailbox/user fixture counts
- Counter updates use transactions and row locks
- Browser acceptance showed no UI overflow or runtime error

## Production observation required

After installation, observe Gunicorn response times, MariaDB slow-query logging, ingestion cycle duration, and process memory under the real mailbox volume before increasing polling frequency or worker counts.
