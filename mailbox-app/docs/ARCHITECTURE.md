# Architecture

## Fixed production data flow

```text
Internet -> Postfix -> Dovecot LMTP -> /var/vmail/vibmail.my/<local>/Maildir
                         ^
                         |
                 MariaDB vibmail
          (existing mail-server source of truth)

Browser -> Nginx -> Gunicorn/Django -> MariaDB vibmail_app
                                      -> cross-schema controlled writes to vibmail.mailboxes
                                      -> read-only Maildir ingestion
```

The existing `vibmail` database and its Postfix/Dovecot views are owned by the mail-server stack. Django migrations operate only inside `vibmail_app`. Mailbox create and status changes use the same MariaDB connection and transaction to update both the application mirror and `vibmail.mailboxes`. Existing mailboxes are imported with `sync_mailserver_mailboxes --strict`.
