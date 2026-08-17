# Security policy

## Supported versions

Security fixes are applied to the latest tagged release candidate or stable release. Operators must keep Ubuntu, Python dependencies, MariaDB, Postfix, Dovecot, Nginx and Certbot patched.

| Version | Support status |
|---|---|
| 1.3.0-rc.2 | Supported release candidate |
| 1.3.0-rc.1 | Superseded release candidate |
| 1.2.x | Legacy deployment assets retained; security support is best-effort |
| Older versions | Unsupported |

## Reporting a vulnerability

Use GitHub's **private security advisory** feature for the repository. Do not open a public issue containing an exploit, production hostname or IP address, private key, password, mailbox content, user data, database dump or generated credential.

Include:

- affected version and component
- minimal sanitized reproduction steps
- expected and observed behavior
- security impact and realistic attack preconditions
- suggested mitigation, when available

Maintainers will acknowledge receipt when practical, validate the report, coordinate a fix and agree on disclosure timing. Response or fix deadlines are not guaranteed.

## Deployment security rules

- Use a dedicated or carefully reviewed Ubuntu 24.04 VPS.
- Keep `/etc/vibmail`, `/etc/vibmail-public-contact`, Postfix map files, database dumps, Maildir data and Let's Encrypt private keys private.
- Do not enable SMTP submission, IMAP, POP3 or public registration without a separate design and audit.
- Run the release verifier before installation.
- Review `docs/THREAT_MODEL.md`, `docs/SECURITY_REVIEW.md` and `mailbox-app/docs/SECURITY_OPERATIONS.md`.

## Scope

The project accepts reports about the Django application, contact service, installer, deployment templates, backup/restore tooling and release pipeline. Vulnerabilities in third-party packages should also be reported upstream when appropriate.
