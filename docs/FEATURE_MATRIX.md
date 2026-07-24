# Feature preservation matrix

The open-source work was performed as an additive and compatibility-preserving change. No application, mailbox, ingestion, access-control, message, public-site, or contact-service source file from the sanitized baseline was deleted.

| Capability | Preservation status | Verification |
|---|---|---|
| Administrator authentication and private admin surface | Preserved | Integration and security tests |
| Ordinary-user accounts and administrator-managed user lifecycle | Preserved | Authentication/user-management integration tests |
| Object-scoped mailbox memberships | Preserved | Access-control integration tests |
| Mailbox create, enable, disable, and soft-delete | Preserved | Mailbox service and integration tests |
| Reserved postmaster/abuse mailbox handling | Preserved | Validator/model and command tests |
| MariaDB-backed Postfix virtual-domain/mailbox/alias contract | Preserved and generalized | Mail-server adapter tests, template validation, installer contract |
| Dovecot LMTP delivery to Maildir | Preserved | Deployment template validation and rendered configuration checks |
| Maildir ingestion and restart-safe duplicate protection | Preserved | Reliability, parser/storage, and ingestion tests |
| Oversized-message handling | Preserved | Ingestion tests |
| Safe MIME parsing and HTML sanitization | Preserved | Parser and security tests |
| Attachment isolation and protected downloads | Preserved | Storage, authorization, and Nginx template checks |
| Search, pagination, counters, read/unread state | Preserved | Message and integration tests |
| Live inbox polling and new-message notification payloads | Preserved | Live-access integration tests |
| Audit trail and health endpoints | Preserved and hardened | Audit/service tests and production deploy checks |
| Public static website | Preserved and parameterized | Public-site renderer and template audit |
| CSRF-protected, rate-limited contact form | Preserved and parameterized | Contact-service test suite |
| Backup, restore, rollback, and operational verification | Preserved; backup/restore generalized | Operations contract tests and shell syntax gates |
| Existing `vibmail.my` deployment compatibility | Preserved | Legacy settings/defaults and legacy deployment assets retained |
| Custom-domain clean installation | Added | Domain configurability tests and installer plan tests |
| Automated public release build and verification | Added | Deterministic build, manifest, checksum, and archive verifier |
