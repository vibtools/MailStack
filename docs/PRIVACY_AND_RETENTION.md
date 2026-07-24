# Privacy and retention

MailStack stores account data, mailbox assignments, audit events, received-message metadata, message bodies, attachments, and raw Maildir content. Operators are responsible for defining lawful retention periods, access policies, incident response, backup retention, and deletion procedures for their jurisdiction and organization.

UI mailbox deletion is deliberately non-destructive: it disables delivery and preserves Maildir and indexed content. This protects against accidental loss but is not a legal erasure workflow. A reviewed operator procedure is required to remove retained message data, backups, and audit records.

Do not use real mailbox content in bug reports, public issues, test fixtures, screenshots, or telemetry. The application does not require third-party analytics.
