# Troubleshooting

- **Login locked:** wait for the configured failure window, investigate the audit log, and verify client proxy addressing.
- **Mailbox creation fails:** check `/var/vmail` ownership/mode, database connectivity, and structured logs. An active row is not created before Maildir readiness.
- **Postfix lookup empty:** confirm mailbox status, migration/view existence, lowercase query, lookup-role privileges, and `postmap -q` configuration.
- **Worker will not start:** inspect the ingestion lock and running service; never remove a lock while a worker is active.
- **Message absent:** run `ingest_maildir --once --mailbox <local_part>`, inspect size limits and parse warnings, and confirm the file is under `new` or `cur`.
- **Attachment missing:** verify attachment root permissions and database/file consistency; no direct public URL is supported.
- **Readiness fails:** check database, migrations, mail/attachment root access, and fixed production configuration without exposing secrets.
