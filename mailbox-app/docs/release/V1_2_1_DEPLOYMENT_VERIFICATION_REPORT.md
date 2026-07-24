# MailStack v1.2.1 Deployment Verification Report

## Baseline matched

The release preserves the verified production contract:

- `app.vibmail.my` and `mail.vibmail.my`
- MariaDB 10.11-compatible dual-schema design
- `/opt/vibmail/app`, `/opt/vibmail/venv`, `/var/vmail`, `/var/lib/vibmail/attachments`, and `/var/lib/vibmail/static`
- `vmail` least-privilege runtime
- Gunicorn, ingestion, Nginx, Postfix, Dovecot, and MariaDB services
- Existing certificate paths and receive-only mail flow
- Live Nginx proxy-header, listener, ACME, redirect, and dotfile hotfixes

## Security-hotfix release assets

- `scripts/audit_dependencies_v1_2_1.sh`
- `scripts/preflight_v1_2_1.sh`
- `scripts/upgrade_v1_2_1.sh`
- `scripts/verify_v1_2_1.sh`
- `scripts/verify_release_manifest.py`

## Exact dependency contract

- Django 5.2.15
- Bleach 6.4.0
- python-dotenv 1.2.2

Preflight validates source pins. Deployment and post-deployment verification validate installed distributions.

## Rollback model

The upgrade captures current source, Nginx, systemd, and logrotate state before cutover. On failure it restores source/configuration/static state and restarts services. Additive database migrations remain forward-compatible to avoid loss of messages received during deployment. The complete backup/restore workflow remains available for coordinated database restoration.

## Status

- Release-side test and deployment-asset validation: PASS
- Full live VPS installation: NOT YET EXECUTED
- Final production acceptance requires supervised hash verification, dependency audit, preflight, backup, install, real inbound test, user-isolation test, and log audit.
