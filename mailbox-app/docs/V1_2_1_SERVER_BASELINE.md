# MailStack 1.2.1 server baseline

The update is based on the verified production state recorded on 27 June 2026.

## Verified services

- `nginx`: active
- `vibmail-gunicorn`: active
- `vibmail-ingestion`: active
- `postfix`: active
- `dovecot`: active
- `mariadb`: active

## Verified application behavior

- `https://app.vibmail.my/` returns `302` to the login page.
- `/accounts/login/` returns `200`.
- `/health/ready/` returns `200` locally.
- Static JavaScript returns `200`.
- `/.env` returns `404`.
- HTTP redirects to HTTPS.
- ACME challenge files are served from `/var/www/letsencrypt/.well-known/acme-challenge/`.
- The certificate SAN is `app.vibmail.my` and the observed expiry was 25 September 2026.
- Nginx, Gunicorn, and ingestion warning/error checks were clean.
- Eight Maildir messages were present at the freeze point.
- Browser login, mailbox creation, and real external inbound email were successful.

## Mandatory source reconciliation

The release Nginx file includes the live fixes that were not present in the raw 1.1.2 archive:

- no `include proxy_params;` duplication;
- exactly one `Host` header per proxied location;
- `listen 443 ssl;` and `listen [::]:443 ssl;` compatibility;
- ACME HTTP route;
- dotfile denial;
- HTTP-to-HTTPS redirect;
- existing certificate paths unchanged.

Production must be rechecked immediately before deployment because this document is a recorded baseline, not live SSH access.
