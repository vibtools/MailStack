# Threat model

## Protected assets

Administrator credentials/session, existing MariaDB mail eligibility records, Django metadata, raw Maildir, indexed message content, attachments, database credentials, logs, TLS material, and deployment configuration.

## Principal threats

- Malicious MIME/HTML and attachment filenames
- Stored or reflected XSS
- Path traversal and unauthorized downloads
- Authentication brute force or session theft
- Duplicate/partial mailbox provisioning
- Divergence between `vibmail_app` and `vibmail.mailboxes`
- Excessive database privileges or credential leakage
- Ingestion crashes, duplicate indexing, oversized messages, disk exhaustion
- Accidental replacement of existing Postfix/Dovecot views

## Controls

Mailbox creation and status changes use one MariaDB connection and transaction across both schemas. Django migrations are isolated to `vibmail_app`. Existing mail-server objects are accessed with fixed SQL identifiers and parameterized values. Mail content is sanitized, storage paths are confined, downloads are authenticated, and deployment scripts fail closed.
