# Installation overview

Target: Ubuntu Server 24.04 LTS, CPython 3.12, existing MariaDB 10.11+, Nginx, existing Postfix/Dovecot stack, and `vmail` UID/GID 5000.

1. Preserve the verified pre-deployment rollback archive.
2. Verify the existing `vibmail` schema and Postfix/Dovecot lookup contract.
3. Create the separate `vibmail_app` database and restricted account from the MariaDB SQL template.
4. Install runtime dependencies and create `/opt/vibmail/venv`.
5. Install `/etc/vibmail/vibmail.env` as `root:vmail` mode `0640`.
6. Deploy the release, migrate `vibmail_app`, verify the mail-server schema, and synchronize existing mailboxes.
7. Install systemd units and Nginx site for `app.vibmail.my`.
8. Obtain/verify TLS, start services, ingest existing Maildir messages, and execute live acceptance tests.

Do not reinstall or replace the working Postfix, Dovecot, MariaDB `vibmail` schema, or existing Maildir.


## Production management-command context

The bundled deployment, verification, and administrator scripts explicitly set `VIBMAIL_ENV_FILE=/etc/vibmail/vibmail.env` and `DJANGO_SETTINGS_MODULE=config.settings.production`. Do not run production management commands from a root-only staging directory as the `vmail` account; deploy the source to `/opt/vibmail/app` first.
