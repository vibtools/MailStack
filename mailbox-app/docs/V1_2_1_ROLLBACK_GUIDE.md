# MailStack 1.2.1 rollback guide

A source-only rollback to 1.1.2 is not sufficient after the 1.2.0 authorization migrations because old code does not understand mailbox memberships or deleted states.

## Required coordinated rollback

1. Stop Gunicorn and ingestion.
2. Preserve a separate copy/inventory of Maildir files received after the pre-upgrade backup.
3. Restore the pre-upgrade application source archive.
4. Restore the pre-upgrade `vibmail_app` database from the coordinated backup.
5. Restore the previous Nginx app-site configuration and validate with `nginx -t`.
6. Do not overwrite newer Maildir files. Maildir remains the raw source of truth.
7. Start Gunicorn and ingestion.
8. Run ingestion so messages received during the deployment window are indexed again.
9. Verify counts, login, mailbox receive flow, Postfix/Dovecot, HTTPS, and logs.

Do not use the generic full restore command blindly if it would overwrite Maildir files created after the backup.
