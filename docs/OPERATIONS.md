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

