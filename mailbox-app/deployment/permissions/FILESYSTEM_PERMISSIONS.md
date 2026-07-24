# Filesystem Permissions

Recommended identities:

- Postfix virtual delivery and Django/Gunicorn/ingestion identity: UID/GID `5000` (`vmail:vmail`).
- Application code `/opt/vibmail/app`: `root:vmail`, directories `0750`, files `0640`.
- Virtual environment `/opt/vibmail/venv`: `root:vmail`, not writable by the service identity.
- Environment `/etc/vibmail/vibmail.env`: `root:vmail`, mode `0640`.
- Mail root `/var/vmail` and `/var/vmail/vibmail.my`: `vmail:vmail`, mode `0750`; provisioned Maildir directories `0700`.
- Attachments `/var/lib/vibmail/attachments`: `vmail:vmail`, mode `0700`; files `0600`.
- Logs `/var/log/vibmail`: `vmail:adm`, mode `0750`.
- Backups `/var/backups/vibmail`: `root:root`, mode `0700`.

Using the same dedicated, non-login `vmail` identity for virtual delivery and the application avoids privileged ownership changes while keeping Maildir inaccessible to unrelated accounts. The ingestion worker receives read-only access to Maildir through its systemd sandbox; Gunicorn receives write access because mailbox provisioning is an authenticated administrator operation.

`USE_X_ACCEL_REDIRECT` defaults to `false`, so authenticated downloads use Django streaming and Nginx does not require attachment filesystem access. Enable X-Accel only after creating a dedicated attachment-read group, adding the Nginx worker to it, and applying setgid group-readable permissions without granting Nginx access to `/var/vmail`.

Gunicorn uses `/run/vibmail`; ingestion uses `/run/vibmail-ingestion`. Separate systemd runtime directories prevent one service restart from deleting or changing ownership of the other service's runtime files.
