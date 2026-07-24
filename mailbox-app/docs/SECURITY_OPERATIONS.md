# Security operations

- Patch Ubuntu, Python, Django, MariaDB, Nginx, Postfix, Dovecot, and Python dependencies using staged verification.
- Keep MariaDB bound to loopback and restrict both application and mail lookup accounts by host and grant.
- Keep `/etc/vibmail/vibmail.env` mode `0640` and backup defaults files mode `0600`.
- Review authentication failures, mailbox provisioning failures, ingestion errors, Postfix queue state, disk use, and TLS expiry.
- Verify backups through periodic isolated restore tests.
- Never expose raw Maildir or attachment storage through Nginx.
- After web-panel acceptance, disable public submission/IMAP ports if the platform is required to remain panel-only and receive-only.
