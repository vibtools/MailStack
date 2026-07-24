# Known limitations

- The automated installer supports clean Ubuntu Server 24.04 LTS only.
- The reference deployment is single-node; high availability is not included.
- Port 25 must be reachable, and some VPS providers block it.
- The system is receive-only for team mailboxes. IMAP, POP3, user SMTP submission, outbound campaigns, and public account registration are intentionally absent.
- Changing the configured mail domain after mailbox creation requires a planned data migration.
- The installer requires working public DNS to obtain Let's Encrypt certificates.
- The public contact notification depends on local Postfix delivery and the recipient provider accepting the message.
