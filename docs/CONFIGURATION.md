# Configuration

The installer writes two protected environment files:

- `/etc/vibmail/vibmail.env` (`root:vmail`, mode `0640`)
- `/etc/vibmail-public-contact/contact.env` (`root:root`, mode `0600`)

Primary settings include the mail/application hostnames, MariaDB credentials, storage paths, message and attachment limits, ingestion interval, session age, proxy trust, log location, and live-update bounds. The committed `.env.example` files contain placeholders only.

Production settings validate hostnames, IP addresses, absolute storage paths, SQL identifiers, the application origin, and minimum secret strength. Changing the mail domain after mailboxes exist is a migration project, not an environment-only change.
## HSTS

The reference installer emits a one-year HSTS policy with `includeSubDomains` and `preload`, and sets `SECURE_HSTS_PRELOAD=true` for the application. The `preload` token does not itself submit a domain to browser preload lists. Operators must review every subdomain before making any separate preload-list submission.

