# Security review — MailStack 1.3.0

## Security posture

The reference deployment is receive-only for hosted team mailboxes. It does not expose IMAP, POP3, SMTP submission, public registration, or mailbox-password login. The public contact service may submit a fixed notification through local Postfix, but remote clients are not granted relay or submission access.

## Controls verified

### Secrets and release hygiene

- No real production identifier, secret, private key, database, Maildir, attachment, log, backup, or generated credential is permitted in source releases.
- Installer secrets and environment files are generated with root-restricted permissions.
- Source and ZIP verifiers fail closed on unsafe paths, private-key material, disallowed email domains/global IP literals, and blocked file types.

### Authentication and authorization

- Django administrator/ordinary-user roles are preserved.
- Mailbox access is object-scoped through memberships.
- Deletion permissions are separately controlled and audited.
- Argon2 is the preferred password hasher, with Django password validation and login lockout controls.
- Public account registration is absent.

### Mail and database boundary

- Postfix uses loopback-only MariaDB maps.
- Mail-server values are SQL parameters; only strictly validated schema/table/view identifiers are interpolated.
- `SQL SECURITY INVOKER` view users receive exact underlying columns.
- Postfix receives no stored secret column, write, or DDL privilege.
- The application receives only required mail-schema reads, mailbox insertion columns, and active-state updates.
- Dovecot is LMTP-only and runs delivery as UID/GID 5000 (`vmail`).
- SMTP AUTH/submission services are disabled by the installer.

### Web and file handling

- Production host, origin, path, secret, IP, and SQL identifier settings fail closed.
- Secure cookies, CSRF, HSTS, frame denial, content-type protection, and referrer policy are configured.
- Nginx protects attachments through an internal route.
- Maildir and attachment paths are confined; symlinks and traversal attempts are tested.
- HTML is sanitized; remote/active content and unsafe attachment names are covered by tests.
- The contact service uses one-time CSRF tokens, secure SameSite cookies, a honeypot, minimum form timing, size limits, rate limits, hashed abuse identifiers, header validation, a local operator-configured sendmail path, and deterministic SQLite connection closure.

### Service confinement

- systemd units use dedicated identities, restrictive umasks, `NoNewPrivileges`, filesystem protection, capability removal, address-family restrictions where applicable, bounded shutdown, and restart policies.

## Reviewed static-analysis exception

Bandit B608 is disabled only at repository configuration level because the mail integration must interpolate configured SQL identifiers. Ruff S608 remains enabled and the specific module has an explicit reviewed exception. The identifiers pass `^[A-Za-z0-9_]+$`, are backtick-quoted, and all data values remain parameterized. Unit tests reject unsafe identifiers.
The standalone contact service invokes the operator-configured local sendmail executable with a
fixed argument vector, byte input, `shell=False` semantics, bounded timeout, and captured output.
Narrow B404/B603 exceptions document that reviewed boundary; user-controlled form data cannot alter
the executable or argument list. Ruff and Bandit now scan this module in the full forensic gate and
GitHub Actions.

## Remaining external risks

- VPS provider port-25 policy, DNS/rDNS, firewall, TLS issuance, OS package advisories, and mail reputation are deployment responsibilities.
- SPF, DKIM, and DMARC are not automatically provisioned by the receive-only base installer; they are recommended for contact/system-mail deliverability.
- A blocking online dependency advisory audit must pass in CI.
- Copyright ownership and third-party license compatibility require release-owner confirmation.

## PHASE-002 shared-shell review

- The shell adds no external script, stylesheet, font, image, or CDN dependency.
- The runtime logo is a byte-identical local copy of the canonical repository SVG; navigation icons
  use a local SVG symbol sprite with unique IDs.
- Administrator navigation remains controlled by the existing authorization context.
- Logout remains a CSRF-protected POST form.
- Hidden mobile navigation is marked inert and `aria-hidden`; opening and closing the drawer manages
  focus without changing authorization or route behavior.
- The unauthenticated shell does not render private navigation or the authenticated live-update URL.
- No settings, logs, teams, domains, public signup, outbound sending, reply, forward, IMAP, or POP3
  control is activated.
- JavaScript contract tests block `eval`, `new Function`, `innerHTML`, and `document.write` in the
  maintained application script.

The shared shell does not change the existing message HTML sanitizer or sandbox. Message-reader
hardening and redesign remain a separate security-focused phase.
