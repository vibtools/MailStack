# Phase 2 deployment handoff — MariaDB compatibility release 1.1.0

## Existing server contract that must be preserved

- MariaDB database: `vibmail`
- Domain table: `mail_domains`
- Mailbox table: `mailboxes`
- Alias table: `mail_aliases`
- Postfix view: `postfix_virtual_mailboxes(email, maildir)`
- Dovecot view: `dovecot_users`
- Mail root: `/var/vmail`
- Domain: `vibmail.my`
- Mailbox path: `vibmail.my/<local_part>/Maildir/`
- UID/GID: `5000:5000`

## New application database

Create `vibmail_app` and the restricted application account from:

`deployment/mariadb/create_vibmail_app_database.sql.template`

The app user receives full rights only on `vibmail_app`, plus narrowly scoped SELECT/INSERT/UPDATE privileges on the existing mail-server objects. It receives no DELETE or DDL rights on `vibmail`.

## Required order

1. Preserve the verified pre-deployment backup.
2. Create `vibmail_app` and the application DB account.
3. Install runtime dependencies.
4. Install `/etc/vibmail/vibmail.env` with mode 0640, owner root:vmail.
5. Deploy source and run migrations.
6. Run `verify_mailserver_schema`.
7. Run `sync_mailserver_mailboxes --strict` to import `team@example.com`.
8. Run `verify_mail_storage` and `verify_postfix_contract`.
9. Configure Gunicorn, ingestion, Nginx, and TLS for `app.vibmail.my`.
10. Start services and ingest the eight existing Maildir messages.
11. Perform live creation, receive, disable/reject, restart, and backup/restore tests.

Never replace the existing Postfix/Dovecot MariaDB views with Django migrations.
