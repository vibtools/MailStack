# Security policy

MailStack is a private receive-only mailbox reader. Report suspected vulnerabilities privately to the system owner. Do not include passwords, private keys, raw emails, attachments, session cookies, or database dumps in reports.

Security boundaries:

- All application pages and attachment endpoints require administrator authentication.
- Incoming HTML is sanitized and rendered in a sandboxed, remote-content-blocked view.
- Attachments are stored outside the public web root and downloaded with non-sniffing attachment headers.
- Maildir and attachment paths are confined to fixed roots.
- The existing MariaDB `vibmail` mail-server schema is authoritative for Postfix/Dovecot.
- The Django account has DDL rights only on `vibmail_app`; access to `vibmail` is restricted to required SELECT/INSERT/UPDATE operations.
- Django migrations never create, replace, or drop existing Postfix/Dovecot views.
- There is no outbound email, Compose, Reply, Forward, campaign, or SMTP client feature.
