# Backup and restore

The application scripts support both the original `vibmail.my` deployment and the configurable open-source installer layout.

## Backup

Run as root:

```bash
BACKUP_ROOT=/var/backups/vibmail /opt/vibmail/app/scripts/backup.sh
```

The script loads the protected application environment, validates database identifiers and required paths, records active service state, then briefly stops contact delivery, Postfix, Dovecot LMTP, ingestion, and Gunicorn. It creates a transaction-consistent dump of the configured application and mail schemas, ownership-preserving Maildir/attachment/contact-state archives, a configuration archive, metadata, and SHA-256 checksums. An exit trap restores only services that were active before the backup.

MariaDB root socket authentication is used by default. Set `DB_BACKUP_DEFAULTS_FILE` to a root-only client defaults file when the local database policy requires a dedicated backup account.

## Restore

Install the compatible source release before restoring, then run:

```bash
/opt/vibmail/app/scripts/restore.sh \
  --backup /absolute/backup/path \
  --confirm-restore
```

The script verifies every checksum, validates gzip/tar integrity, rejects path traversal and unsafe archive members, restores the databases and state, repairs permissions, applies migrations, reconciles mail-server mailboxes, rebuilds counters and static files, verifies Maildir and Postfix contracts, validates service configuration, and restores the prior service state.

The restore format remains compatible with v1.2 backups that do not contain the optional contact-state archive.
