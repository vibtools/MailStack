# Quick start

## 1. Prepare DNS

Create direct DNS records before installation:

- `A/AAAA` for the public hostname
- `A/AAAA` for the application hostname
- `A/AAAA` for the mail hostname
- `MX` for the mail domain pointing to the mail hostname

Do not proxy the mail hostname through an HTTP CDN. Confirm that inbound TCP ports 25, 80, and 443 reach the VPS.

## 2. Use a clean server

The automated installer targets Ubuntu Server 24.04 LTS. It deliberately refuses unsupported operating systems and an existing marked MailStack installation. Review any existing Postfix, Dovecot, MariaDB, or Nginx workload before using the installer.

## 3. Validate the plan

```bash
./install.sh --domain example.com --admin-email admin@example.com \
  --server-ip 203.0.113.10 --non-interactive --plan
```

## 4. Install

For an SSH/PuTTY session, create a resilient terminal first:

```bash
tmux new -s mailstack-install
```

Run the installer inside it:

```bash
sudo ./install.sh --domain example.com --admin-email admin@example.com \
  --server-ip 203.0.113.10 --non-interactive
```

The initial administrator credential is written to a root-only file immediately after the account is created. Sign in, store the password in an approved password manager, change it immediately, then securely delete the file. A reviewed `--repair` preserves an already-valid administrator instead of resetting its password.

## 5. Verify external delivery

Send a message from an unrelated provider to `postmaster@example.com`. Confirm that Postfix accepts it, Dovecot writes it to Maildir, the ingestion service indexes it, and it appears in the application.

See `docs/OPERATIONS.md` for service and log commands.
