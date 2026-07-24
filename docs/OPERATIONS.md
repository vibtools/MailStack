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

```bash
sudo -u vmail env VIBMAIL_ENV_FILE=/etc/vibmail/vibmail.env \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py check --deploy

sudo -u vmail env VIBMAIL_ENV_FILE=/etc/vibmail/vibmail.env \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  /opt/vibmail/venv/bin/python /opt/vibmail/app/manage.py verify_mailserver_schema
```

## Repair

After reviewing the cause of a partial or damaged installation, re-run the same source release with the original parameters and `--repair`. The installer reuses root-only generated secrets and does not create another administrator.
## Backup and restore

```bash
sudo BACKUP_ROOT=/var/backups/vibmail /opt/vibmail/app/scripts/backup.sh

sudo /opt/vibmail/app/scripts/restore.sh \
  --backup /var/backups/vibmail/TIMESTAMP \
  --confirm-restore
```

See `docs/BACKUP_RESTORE.md` before restoring production data.

