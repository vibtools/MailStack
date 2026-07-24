# Maintenance guide

## Routine tasks

- Apply Ubuntu security updates and reboot when required.
- Review MariaDB, Postfix, Dovecot, Nginx, Certbot and Python dependency advisories.
- Verify certificate renewal and service health.
- Monitor disk usage under `/var/vmail`, `/var/lib/vibmail`, `/var/log/vibmail` and backup storage.
- Test backup restoration on an isolated system.
- Review audit logs and failed login activity.

## Application verification

```bash
sudo /opt/vibmail/app/scripts/health_check.sh
sudo /opt/vibmail/app/scripts/verify_application.sh
```

## Dependency maintenance

Update pinned dependencies only through a reviewed pull request. Run the online vulnerability audit, full tests, lint, Bandit, Django checks, template tests and deterministic release verification before merging.

## Change control

- Back up before deployment or configuration changes.
- Record the release version and configuration delta.
- Use maintenance windows for database/mail-flow changes.
- Verify inbound delivery, ingestion, authorization and backup after changes.
- Retain a tested rollback path.
