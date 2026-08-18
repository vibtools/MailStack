# Operations

## Services

```bash
systemctl status mariadb postfix dovecot nginx \
  vibmail-gunicorn vibmail-ingestion vibmail-public-contact
```

## Logs

```bash
journalctl -u vibmail-gunicorn -u vibmail-ingestion -u vibmail-public-contact --since today
journalctl -u postfix -u dovecot --since today
tail -f /var/log/vibmail/application.log
```

## Health and contract checks

Use the maintained scripts for the complete live/ready and application contract checks:

```bash
/opt/vibmail/app/scripts/health_check.sh
/opt/vibmail/app/scripts/verify_application.sh
```

The application verifier's Maildir scan is a one-shot dry run. It does not stop the live ingestion service, does not acquire the exclusive ingestion-worker lock, and does not update ingestion heartbeat state.

Targeted management checks remain available when diagnosing a specific layer:

```bash
sudo -u vmail env VIBMAIL_ENV_FILE=/etc/vibmail/vibmail.env \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py verify_mailserver_schema
```

## Repair

After reviewing the cause of a partial or damaged installation, re-run the same source release with the original parameters and `--repair`. The installer reuses root-only generated secrets, preserves a valid existing administrator and system mailboxes, and creates only missing bootstrap objects. Inconsistent bootstrap state fails closed. An existing administrator password is never changed automatically.
## Backup and restore

```bash
sudo BACKUP_ROOT=/var/backups/vibmail /opt/vibmail/app/scripts/backup.sh

sudo /opt/vibmail/app/scripts/restore.sh \
  --backup /var/backups/vibmail/TIMESTAMP \
  --confirm-restore
```

See `docs/BACKUP_RESTORE.md` before restoring production data.


## Controlled existing-server upgrade

PHASE-004C provides the generic source/runtime upgrade and rollback mechanism. It is source-qualified
only until the separate PHASE-004D real-VPS acceptance campaign. Review `docs/UPGRADE.md` before any
live use.

```bash
sudo /opt/vibmail/app/scripts/upgrade.sh \
  --archive /root/releases/mailstack-X.Y.Z-source.zip \
  --checksum /root/releases/mailstack-X.Y.Z-source.zip.sha256 \
  --confirm-upgrade
```

New migration files require `--allow-migrations` after review. Successful upgrades print the exact
rollback snapshot and nested consistent data-backup paths. For a no-schema-change source/runtime
rollback:

```bash
sudo /opt/vibmail/app/scripts/rollback_upgrade.sh \
  --snapshot /var/backups/vibmail/upgrades/TIMESTAMP-from-X-to-Y \
  --confirm-rollback
```

Do not treat that command as a database rollback. See `docs/UPGRADE.md` and
`docs/BACKUP_RESTORE.md` for migration-aware recovery rules.
