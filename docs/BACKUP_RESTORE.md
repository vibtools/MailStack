# Backup and restore

## Built-in consistent data backup

The installed application provides a fail-closed backup command:

```bash
sudo BACKUP_ROOT=/var/backups/vibmail /opt/vibmail/app/scripts/backup.sh
```

It temporarily stops the public contact worker, Postfix, Dovecot LMTP, the ingestion worker, and Gunicorn; records which services were previously active; and restores that exact state through an exit trap. The backup contains:

- the configured application and mail MariaDB schemas;
- `/var/vmail` Maildir data;
- `/var/lib/vibmail/attachments`;
- public-contact SQLite state when present;
- generated application, contact, Postfix, Dovecot, Nginx, systemd, and logrotate configuration;
- metadata and SHA-256 checksums.

MariaDB root socket authentication is used by default. A root-only `DB_BACKUP_DEFAULTS_FILE` can be supplied for deployments that require an explicit backup account.

## Restore

Install the same or a compatible MailStack release on the target Ubuntu 24.04 server first, then run:

```bash
sudo /opt/vibmail/app/scripts/restore.sh \
  --backup /var/backups/vibmail/20260101T000000Z \
  --confirm-restore
```

The restore script verifies checksums, rejects unsafe tar members, restores the schemas and state, repairs ownership, applies migrations, rebuilds counters and static assets, verifies Maildir/Postfix contracts, validates Nginx/Postfix/Dovecot configuration, and restores the prior service state.

## Full disaster-recovery copy

The built-in application backup intentionally does not duplicate the release archive or Let's Encrypt private-key tree. For complete host disaster recovery, retain separately:

- the exact signed/checksummed MailStack source release;
- `/etc/letsencrypt` or a plan to reissue certificates;
- DNS, PTR/rDNS, firewall, provider, monitoring, and off-host backup configuration;
- an encrypted off-host copy of the built-in backup.

Backups contain credentials, user email, attachments, and message content. Restrict access, encrypt at rest and in transit, verify checksums after transfer, and test restoration on an isolated host.
