# Installation guide

## Supported target

The native installer supports a clean Ubuntu Server 24.04 LTS VPS with Python 3.12. The reference deployment is single-node and receive-only.

## Prerequisites

- root or sudo access
- public IPv4 or IPv6 address
- inbound ports 25, 80 and 443 allowed
- `A`/`AAAA` records for public, application and mail hostnames
- `MX` record for the mail domain pointing to the mail hostname
- provider support for inbound SMTP on port 25
- PTR/rDNS review for the mail hostname

## DNS example

| Type | Name | Value |
|---|---|---|
| A/AAAA | `example.com` | server address |
| A/AAAA | `app.example.com` | server address |
| A/AAAA | `mail.example.com` | server address |
| MX | `example.com` | `10 mail.example.com.` |

## Plan mode

Plan mode validates arguments and prints the intended layout without changing the server:

```bash
./install.sh --domain example.com --admin-email admin@example.com \
  --server-ip 203.0.113.10 --non-interactive --plan
```

## Installation

When installing over SSH, start a resilient terminal session first so a PuTTY/network disconnect does not terminate the foreground installer:

```bash
tmux new -s mailstack-install
```

Then run the installer inside that session:

```bash
chmod +x install.sh
sudo ./install.sh --domain example.com --admin-email admin@example.com \
  --server-ip 203.0.113.10 --non-interactive
```

Optional flags include custom application/mail/public hostnames, `--www`, a password environment variable, `--repair`, and `--skip-dns-check`. Use `./install.sh --help` for the authoritative list. The installer warns, but does not abort, when a mutating run starts over SSH outside `tmux`/`screen`.

## Installer phases

1. Argument and operating-system validation
2. DNS and port preflight
3. Package installation
4. Service identities and filesystem permissions
5. Secret generation and database bootstrap
6. Application and public-site deployment
7. Postfix, Dovecot, Nginx and systemd configuration
8. TLS certificate issuance
9. Database migration, static collection and resumable administrator/system-mailbox provisioning
10. Acceptance checks and installation marker

## Reviewed repair after a partial installation

If a clean installation stops after secrets or bootstrap data have been created, inspect the failure, preserve the generated state, and rerun the same release and parameters with `--repair`. Repair preserves a valid existing administrator and valid `postmaster`/`abuse` mailboxes, creates only missing bootstrap objects, and fails closed on inconsistent state. It never silently changes an existing administrator password. If repair must create the administrator, a new root-only initial-credentials file is written immediately after creation.

Do not source `/etc/vibmail/vibmail.env` into the parent root shell before installation/repair. Installer-launched Django commands use an isolated least-privilege environment so stale exported database credentials cannot override the rendered production environment.

## After installation

- Store `/etc/vibmail/installer-secrets.env` securely.
- Sign in at the configured application hostname.
- Confirm `postmaster@DOMAIN` and `abuse@DOMAIN`.
- Send an external test message and verify LMTP delivery and ingestion.
- Run the health and verification scripts.
- Create and test a backup before onboarding users.

## Production warning

Do not run the clean installer over an unreviewed existing mail stack. Use the documented upgrade/repair process and take a verified backup first.
