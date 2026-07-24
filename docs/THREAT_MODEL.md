# Threat model

Protected assets include mailbox content, attachments, user sessions, credentials, database data, TLS keys, audit records, and recipient privacy.

Primary threats are unauthorized mailbox access, cross-mailbox object references, stored/reflected XSS, unsafe HTML email, path traversal, malicious attachments, duplicate ingestion, database injection, open relay, credential disclosure, insecure backup handling, service compromise, and configuration drift.

Controls include object-scoped query services, CSRF protection, secure cookies, CSP and other response headers, HTML sanitization, path confinement, randomized attachment storage names, idempotent ingestion, parameterized values, validated SQL identifiers, Postfix recipient maps, disabled submission/IMAP/POP3, least-privilege database users, systemd sandboxing, private environment files, and fail-closed installer checks.

Residual risks include VPS compromise, malicious administrators, unpatched dependencies, provider port restrictions, DNS compromise, unavailable external delivery, and operational mistakes. Production operators must monitor, patch, back up, and periodically test recovery.
