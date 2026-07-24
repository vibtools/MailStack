# Architecture

```text
Internet SMTP
    -> Postfix recipient validation (MariaDB read-only maps)
    -> Dovecot LMTP
    -> /var/vmail/<domain>/<local>/Maildir
    -> MailStack ingestion worker
    -> Django application database + protected attachment storage
    -> Nginx/Gunicorn private team UI

HTTPS visitor
    -> Nginx static public website
    -> isolated Unix-socket contact service
    -> local sendmail notification
```

The application and mail-server data use separate MariaDB schemas. The application account owns the Django schema and receives only the cross-schema privileges needed to read domains/aliases and create or update mailbox rows. Postfix uses a separate SELECT-only account.

The raw Maildir remains the authoritative received-message source. Indexed message metadata and extracted attachments can be rebuilt from Maildir. Mailbox and message deletion in the UI is deliberately non-destructive unless an operator performs a separate retention action.
