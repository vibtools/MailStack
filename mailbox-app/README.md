# MailStack 1.3.0

Self-hosted, receive-only team mailbox platform. The default legacy domain remains compatible, while the public installer supports a configured domain.

This v1.2.1 package supersedes the rejected v1.2.0 archive and contains the dependency-security hotfixes documented in `docs/V1_2_1_SECURITY_HOTFIX.md`.

## Release scope

- Administrator and ordinary-user separation
- User create/edit/delete and mailbox assignment
- Per-user mailbox and message isolation
- Administrator-controlled message/mailbox deletion permissions
- Soft deletion that preserves Maildir and indexed data
- Live inbox/counter updates without page reload
- In-app and optional browser new-email notifications
- Automatic read state when a message is opened
- Click-to-copy mailbox and sender email addresses
- User-facing branding updated to **MailStack**

## Preserved production contract

- MariaDB `vibmail` remains the authoritative Postfix/Dovecot database.
- Django application data remains in `vibmail_app`.
- Maildir data under `/var/vmail/vibmail.my` remains the raw source of truth.
- The application remains receive-only; no outbound SMTP feature exists.
- Existing Postfix/Dovecot tables and views are never created or dropped by Django migrations.
- The least-privilege `vmail` runtime and virtualenv permission normalization remain mandatory.

## Production update order

Read these before deployment:

1. `docs/V1_2_1_SERVER_BASELINE.md`
2. `docs/V1_2_1_UPGRADE_GUIDE.md`
3. `docs/V1_2_1_ROLLBACK_GUIDE.md`
4. `docs/V1_2_1_ACCEPTANCE_CHECKLIST.md`

Run `scripts/audit_dependencies_v1_2_1.sh` and `scripts/preflight_v1_2_1.sh` before changing production. Run `scripts/verify_v1_2_1.sh` after deployment.


## Open-source installation

Use the repository-root `install.sh` and public documentation for clean Ubuntu 24.04 deployments. The application-level scripts in this directory remain available for backward-compatible maintenance of existing installations.
