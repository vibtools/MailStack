# MailStack Public Website Deployment

## Architecture

- Static public website served directly by Nginx.
- Dedicated Python WSGI contact service.
- Gunicorn bound to a Unix socket.
- Contact submissions stored in SQLite before notification delivery.
- Fixed admin recipient.
- Existing `app.vibmail.my` and mail services remain separate.

## Deployment order

1. Create the dedicated service account.
2. Install the versioned release and static files.
3. Generate the protected environment secret.
4. Install and start the contact service.
5. Install the HTTP bootstrap Nginx virtual host.
6. Obtain the `vibmail.my` and `www.vibmail.my` certificate.
7. Replace bootstrap config with the final HTTPS config.
8. Run automated and manual acceptance tests.

## Rollback

- Restore the previous Nginx site configuration.
- Restore the previous `/var/www/vibmail.my` tree or symlink.
- Restore the previous `/opt/vibmail-public-site/current` link.
- Disable and remove the public contact service only if the release must be fully withdrawn.
- Existing `app.vibmail.my`, Postfix, Dovecot and MariaDB are not part of this release.
