<div align="center">

<img src="assets/mailstack-logo.svg" width="104" height="104" alt="MailStack logo">

# MailStack

### Open-source self-hosted mail server and shared team inbox for secure business email

[![CI](https://github.com/vibtools/MailStack/actions/workflows/ci.yml/badge.svg)](https://github.com/vibtools/MailStack/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/vibtools/MailStack?include_prereleases&sort=semver)](https://github.com/vibtools/MailStack/releases)
[![License](https://img.shields.io/github/license/vibtools/MailStack)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](mailbox-app/pyproject.toml)
[![Django](https://img.shields.io/badge/Django-5.2-0C4B33?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu_Server-24.04-E95420?logo=ubuntu&logoColor=white)](docs/INSTALLATION.md)
[![Stars](https://img.shields.io/github/stars/vibtools/MailStack?style=flat)](https://github.com/vibtools/MailStack/stargazers)
[![Forks](https://img.shields.io/github/forks/vibtools/MailStack?style=flat)](https://github.com/vibtools/MailStack/forks)
[![Issues](https://img.shields.io/github/issues/vibtools/MailStack)](https://github.com/vibtools/MailStack/issues)

**Postfix · Dovecot LMTP · Django · MariaDB · Maildir · Nginx · Ubuntu 24.04**

[Quick start](#quick-start) · [Architecture](#architecture) · [Documentation](#documentation) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md)

</div>

## Overview

**MailStack** is an open-source, self-hosted mail server and shared team inbox for organizations that need controlled, receive-only business email on infrastructure they manage.

It combines **Postfix**, **Dovecot LMTP**, **Django**, **MariaDB**, **Maildir**, **Gunicorn**, and **Nginx** in a hardened single-node reference deployment. MailStack provides a private browser-based inbox, administrator-managed users, object-level mailbox access, safe email rendering, protected attachments, live inbox updates, operational audit logs, backup and restore tooling, a public website, and an isolated contact service.

> **Release status:** `v1.3.0-rc.1` remains a release candidate. Source, test, security, template, and release tooling are present, but clean Ubuntu 24.04 VPS acceptance and real external SMTP/LMTP verification are required before stable promotion.

## Why MailStack

MailStack is designed for teams that need:

- self-hosted business inboxes without public mailbox registration;
- shared mailbox access with per-user authorization;
- a receive-only mail security model;
- durable Maildir storage and recoverable indexing;
- protected attachment delivery and sanitized HTML email;
- auditable administration and operational recovery;
- reproducible installation and release tooling.

MailStack is **not** intended to be a complete replacement for Gmail, Microsoft 365, or a general-purpose outbound email marketing platform.

## Key features

### Shared team inbox

- Administrator and ordinary-user accounts
- Object-level mailbox isolation
- Shared mailbox memberships
- Mailbox create, enable, disable, and soft-delete lifecycle
- Search, pagination, read/unread state, and attachment filters
- Live inbox polling and browser notification support

### Receive-only mail stack

- Postfix virtual recipient validation
- Dovecot LMTP delivery
- Maildir as the authoritative received-message source
- Unknown-recipient and disabled-mailbox rejection
- No public SMTP submission, IMAP, POP3, or open relay in the reference deployment

### Secure message processing

- Idempotent Maildir ingestion
- Duplicate-delivery protection
- Restart-safe ingestion worker
- MIME parsing with malformed-message recovery
- Allowlist-based HTML sanitization
- Remote and active content blocking
- Confined, protected attachment storage
- Authorized attachment download routes

### Operations and release engineering

- Ubuntu Server 24.04 installer
- MariaDB, Postfix, Dovecot, Nginx, Gunicorn, and systemd templates
- Health and readiness endpoints
- Structured security audit logging
- Backup, restore, rollback, and verification tooling
- Deterministic source ZIP and SHA-256 generation
- CI quality, security, test, and release gates

## Architecture

```text
Internet email
    │
    ▼
Postfix — receive-only SMTP and recipient validation
    │
    ▼
Dovecot LMTP
    │
    ▼
/var/vmail/<domain>/<mailbox>/Maildir
    │
    ▼
Maildir ingestion worker
    │
    ├──► MariaDB message metadata
    └──► Protected attachment storage
             │
             ▼
Browser ──HTTPS──► Nginx ──Unix socket──► Gunicorn / Django
                  ├──────────────────────► Protected files
                  └──────────────────────► Public site and contact service
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component responsibilities, trust boundaries, and data flow.

## Supported deployment model

The reference deployment is:

- single-node;
- receive-only for hosted team mailboxes;
- designed for a clean Ubuntu Server 24.04 LTS VPS;
- dependent on public DNS and reachable ports `25`, `80`, and `443`;
- built around MariaDB, Postfix, Dovecot LMTP, Maildir, Nginx, and systemd.

The reference deployment intentionally excludes:

- IMAP and POP3;
- remote SMTP submission;
- public user registration;
- outbound campaigns;
- multi-node or high-availability deployment;
- a public administrative API.

Any expansion of those trust boundaries requires a separate architecture and security review.

## Quick start

### Requirements

- Clean Ubuntu Server 24.04 LTS VPS
- Root or `sudo` access
- Public IPv4 or IPv6 address
- DNS records for the public, application, and mail hostnames
- Reachable inbound ports `25`, `80`, and `443`
- A provider that permits inbound SMTP on port `25`

### Validate the installation plan

```bash
chmod +x install.sh

./install.sh \
  --domain example.com \
  --admin-email admin@example.com \
  --server-ip 203.0.113.10 \
  --non-interactive \
  --plan
```

The `--plan` mode validates inputs and shows the intended deployment without modifying the server.

### Install

```bash
sudo ./install.sh \
  --domain example.com \
  --admin-email admin@example.com \
  --server-ip 203.0.113.10 \
  --non-interactive
```

The installer provisions the mail stack, application services, TLS configuration, public site, contact service, strong generated credentials, and required system mailboxes.

Read [docs/INSTALLATION.md](docs/INSTALLATION.md), [docs/QUICKSTART.md](docs/QUICKSTART.md), and [docs/DNS_AND_DELIVERABILITY.md](docs/DNS_AND_DELIVERABILITY.md) before internet-facing deployment.

## Development

```bash
cd mailbox-app

python3.12 -m venv .venv
. .venv/bin/activate

python -m pip install -r requirements/development.txt

pytest --cov=apps --cov-report=term-missing --cov-fail-under=85
ruff check .
bandit -c .bandit -q -r apps config
```

Synchronize and validate user documentation before the complete repository gate:

```bash
python scripts/manage_documents.py sync
python scripts/manage_documents.py check
python scripts/test_documents.py
python scripts/check_documentation_policy.py --base HEAD^ --head HEAD
```

Run the complete repository gate from the project root:

```bash
python scripts/manage_designs.py --root . check
python scripts/test_designs.py
python scripts/test_ui_foundation.py
python scripts/forensic_audit.py --root . --full
```

Build and verify a deterministic source release:

```bash
python scripts/build_release.py --root .
python scripts/verify_release.py \
  dist/mailstack-1.3.0-rc.1-source.zip \
  --checksum dist/mailstack-1.3.0-rc.1-source.zip.sha256
```

## Security

MailStack uses a receive-only reference architecture with layered controls:

- object-scoped mailbox and message authorization;
- CSRF protection and secure production cookies;
- Argon2 password hashing;
- login throttling;
- safe redirect validation;
- HTML sanitization and restricted content security policy;
- attachment path confinement;
- least-privilege database access;
- Postfix recipient maps with no remote relay;
- systemd service confinement;
- protected environment files;
- fail-closed installer, backup, restore, and release checks.

Do not publish credentials, database dumps, Maildir data, attachments, logs, backups, certificates, or private keys. Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md).

## Screenshots

The repository does not include screenshots containing real mailbox data, production domains, credentials, or user information. Publish only sanitized screenshots created with synthetic fixtures.

See [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) for the approved screenshot set and sanitization rules.

## Documentation

| Area | Document |
|---|---|
| User documentation | [documents/README.md](documents/README.md) |
| User manual | [documents/USER_MANUAL.md](documents/USER_MANUAL.md) |
| How to use | [documents/HOW_TO_USE.md](documents/HOW_TO_USE.md) |
| Administrator guide | [documents/ADMIN_GUIDE.md](documents/ADMIN_GUIDE.md) |
| Quick start | [docs/QUICKSTART.md](docs/QUICKSTART.md) |
| Installation | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| Configuration | [docs/CONFIGURATION.md](docs/CONFIGURATION.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Operations | [docs/OPERATIONS.md](docs/OPERATIONS.md) |
| Backup and restore | [docs/BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md) |
| DNS and deliverability | [docs/DNS_AND_DELIVERABILITY.md](docs/DNS_AND_DELIVERABILITY.md) |
| Security review | [docs/SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md) |
| Threat model | [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) |
| API and routes | [docs/API_REFERENCE.md](docs/API_REFERENCE.md) |
| Troubleshooting | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Release process | [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) |
| Branding | [docs/BRANDING.md](docs/BRANDING.md) |
| Rebrand compatibility | [docs/REBRAND_COMPATIBILITY.md](docs/REBRAND_COMPATIBILITY.md) |
| Bootstrap audit | [docs/MAILSTACK_BOOTSTRAP_AUDIT.md](docs/MAILSTACK_BOOTSTRAP_AUDIT.md) |
| GitHub metadata | [docs/GITHUB_REPOSITORY_METADATA.md](docs/GITHUB_REPOSITORY_METADATA.md) |
| First commit from Windows | [docs/FIRST_COMMIT_WINDOWS.md](docs/FIRST_COMMIT_WINDOWS.md) |
| UI design intake | [design/README.md](design/README.md) |
| UI foundation | [documents/design/UI_FOUNDATION.md](documents/design/UI_FOUNDATION.md) |
| UI screen catalog | [documents/design/SCREEN_CATALOG.md](documents/design/SCREEN_CATALOG.md) |

## Roadmap

Current priorities are release-candidate qualification, clean Ubuntu 24.04 acceptance, external SMTP/LMTP verification, dependency advisory checks, reproducible release provenance, operator observability, and long-running reliability tests.

See [ROADMAP.md](ROADMAP.md) for the maintained roadmap and compatibility rules.

## Compatibility policy

The MailStack repository bootstrap changes public product identity and canonical repository metadata without renaming established runtime contracts.

The following identifiers remain temporarily unchanged for backward compatibility:

- `VIBMAIL_*` environment variables;
- `vibmail-*` systemd service names;
- `/etc/vibmail` and related runtime paths;
- established database and deployment identifiers;
- the `vibmail.my` legacy deployment contract.

See [docs/REBRAND_COMPATIBILITY.md](docs/REBRAND_COMPATIBILITY.md). Any runtime identifier migration must be handled as a separately tested, reversible migration rather than a search-and-replace rename.

## Project identity

- **Project:** MailStack
- **Publisher:** Vib Tools
- **Canonical repository:** `vibtools/MailStack`
- **Source:** https://github.com/vibtools/MailStack
- **Open-source hub:** https://dev.vib.tools/
- **Company:** https://vib.tools/
- **Optional free subdomain service:** https://ygit.net/

## Contributing

Contributions must preserve existing features, migrations, deployment compatibility, data integrity, and authorization boundaries unless a breaking change is explicitly designed and approved.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SUPPORT.md](SUPPORT.md) before opening an issue or pull request.

## License

MailStack source code is licensed under the **GNU Affero General Public License v3.0 or later** (`AGPL-3.0-or-later`). The complete license text is in [LICENSE](LICENSE).

Third-party components remain under their respective licenses. Product names, logos, and visual identity are not automatically licensed as trademarks by the AGPL; see [NOTICE.md](NOTICE.md) and [docs/BRANDING.md](docs/BRANDING.md).

Copyright © 2026 Vib Tools and MailStack contributors.
