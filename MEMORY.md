# MailStack Permanent Project Memory

This file is the permanent project memory for MailStack. It should be reviewed at the start of each AI-assisted session and updated whenever meaningful architecture, workflow, feature, or operational changes occur.

## 1) Project Summary

MailStack is an open-source, self-hosted receive-only mail server and shared team inbox platform designed for organizations that control their own infrastructure. It combines Postfix, Dovecot LMTP, Django, MariaDB, Maildir, Nginx, and systemd into a single-node production deployment for secure business email intake.

The project is currently aligned to a versioned release workflow with a Python/Django application in `mailbox-app/`, provisioning automation in `install.sh`, service templates in `deployment/templates/`, a public site in `public-site/`, and supporting docs under `docs/` and `documents/`.

## 2) Tech Stack & Dependencies

### Core runtime stack

- Operating system: Ubuntu Server 24.04 LTS
- Primary language: Python 3.12+
- Web framework: Django 5.2.x
- Process manager: Gunicorn
- Web server / reverse proxy: Nginx
- Mail transfer agent: Postfix
- Mail storage / delivery: Dovecot LMTP with Maildir storage
- Database: MariaDB
- Authentication / hashing: Django + Argon2 (`argon2-cffi`)
- TLS / certificates: Let's Encrypt / Certbot
- Runtime packaging: systemd service definitions and shell automation

### Project dependencies (from `mailbox-app/pyproject.toml`)

- Django==5.2.17
- argon2-cffi==25.1.0
- bleach==6.4.0
- tinycss2==1.5.1
- filelock==3.20.3
- gunicorn==25.1.0
- mysqlclient==2.2.7
- python-dotenv==1.2.2
- whitenoise==6.11.0

### Supporting tooling and automation

- Bash installer and deployment scripts (`install.sh`, `scripts/*.py`)
- Python scripts for template rendering, docs management, forensic inventory, release gates, and audits
- GitHub Actions workflows for CI, release automation, and repository validation
- Container-less single-server deployment model rather than Docker-based app packaging

## 3) Architecture & Folder Structure Overview

### Root-level layout

- `install.sh`: primary server installer and configuration bootstrap
- `deployment/templates/`: rendered config templates for Postfix, Nginx, Dovecot, systemd, etc.
- `mailbox-app/`: Django application code and Python project config
- `public-site/`: public-facing marketing/site assets and frontend content
- `scripts/`: release, audit, inventory, docs, and verification tooling
- `docs/`: technical project documentation, architecture, operations, security, setup docs
- `documents/`: end-user/admin documentation bundle
- `assets/`: shared project graphics and branding assets
- `.github/`: repository automation and GitHub workflow configuration

### Django app structure

- `mailbox-app/config/`: settings package and runtime configuration
- `mailbox-app/apps/`: application modules such as:
    - `accounts/`: user/account management
    - `audit/`: operational and security audit trails
    - `dashboard/`: admin and dashboard views / status pages
    - `ingestion/`: mail ingestion and processing
    - `mailboxes/`: mailbox, alias, and mail server entity logic
    - `messages/`: message retrieval, display, sanitization, attachments
    - `core/`: common foundation logic
- `mailbox-app/static/`: CSS/JS/images for the app UI
- `mailbox-app/templates/`: Django HTML templates and base layouts
- `mailbox-app/tests/`: project tests
- `mailbox-app/requirements/`: dependency requirement files

### Deployment model

- Single-node Ubuntu VPS with public DNS, inbound SMTP on port 25, and HTTPS
- Postfix receives email and validates recipients
- Dovecot LMTP delivers mail to Maildir directories under `/var/vmail/`
- Django/Gunicorn serves application logic through Nginx
- Runtime socket usually under `/run/vibmail/`
- Installer provisions system users, database access, TLS, and mail stack components without Docker

## 4) Key Business Logic, Features, and Active Modules

### Receive-only mail server workflow

MailStack is deliberately a receive-only mail system. It does not act as a public outbound email marketing platform. The operational model is built around:

- Postfix as the SMTP ingress and recipient validation layer
- Dovecot LMTP for local message delivery
- Maildir as the authoritative message store
- mail ingestion workers to parse, normalize, and index incoming messages
- recipient and mailbox-level authorization enforcement

### Shared team inbox and mailbox model

- Administrator and ordinary-user account support
- Shared mailbox membership and object-level access control
- Mailbox lifecycle features: create, enable, disable, soft-delete
- Message read/unread state, pagination, and search behavior
- Attachment-aware message reading and protected download routes

### Secure message processing

- Idempotent ingestion and duplicate-delivery protection
- Restart-safe ingestion workflow
- MIME parsing with malformed-message recovery
- HTML sanitization and inline content restrictions
- Attachment confinement and host-side storage controls
- Active-content blocking and safe rendering of messages in the web UI

### Admin and operations features

- Safe release and update automation
- health/readiness and audit logging
- backup/restore and rollback support
- deterministic source release packaging with checksums
- CI and forensic repository validation gates

### Current project emphasis

The active repository direction is a hardened, operationally auditable self-hosted mail platform with a compact UI and production-safe installation pipeline. Recent work has focused on:

- system update and release workflow stability
- forensic inventory / audit gate compliance
- design token and UI consistency updates
- secure architecture and deployment hygiene

## 5) Coding Conventions and Project Rules

### General engineering conventions

- Favor the smallest correct change over broad refactors
- Reuse existing app services, helpers, and patterns before adding new code
- Respect the Django application structure, naming conventions, and deployment assumptions
- Do not introduce new architecture layers or frameworks unless strictly required
- Preserve existing operational and deployment contracts, especially for installer templates and release artifacts

### Python conventions

- Target Python 3.12
- Maintain `ruff`-friendly code style and import hygiene
- Keep SQL values parameterized and avoid unsafe string interpolation for user-controlled values
- Follow project-specific config and test patterns under `mailbox-app/config/` and `mailbox-app/tests/`

### Frontend conventions

- Django templates are used for rendered HTML
- Static assets are organized under `mailbox-app/static/`
- UI changes should preserve existing design-system tokens and layouts unless explicitly requested
- Template contract requirements are strict; e.g. HTML head ordering and Django template comments must not be broken

### Operational and repository rules

- When files change in the repo, the forensic inventory and audit workflow must be refreshed and validated
- Always preserve the integrity of critical deployment contracts, installer behavior, and release readiness checks
- The project has explicit long-term memory and audit expectations; AI agents should keep architecture knowledge current rather than relying on repeated codebase audits

## 6) Current AI Memory Rule

CRITICAL RULE: Whenever a change, update, bug fix, or new feature is implemented in this project during our conversation, you (the AI) must automatically prompt me to update the `MEMORY.md` file, or directly write/suggest the exact markdown updates needed to keep the project memory 100% up-to-date in real-time.

This repository expects AI agents to maintain durable context across sessions rather than re-discovering project facts repeatedly.

## 7) Known Reality Checks

- Release version currently tracked in project metadata: `1.3.5.1` (four-component revision releases are supported alongside legacy three-component versions)
- Deployment is designed for Ubuntu 24.04 with native package installation, not Docker-first packaging
- The application is intentionally receive-only and not a general outbound marketing mail platform
- Security and audit compliance are treated as first-class project constraints
- The repo is expected to maintain a synchronized `docs/FORENSIC_FILE_INVENTORY.json` and pass forensic audit validation after meaningful edits

## 8) Maintenance Notes

This memory file should be treated as the canonical context snapshot for future AI-assisted work in this repository. If the project direction, deployment architecture, or feature set materially changes, update this document immediately.

### [2026-09-17] System Update production-readiness scope

- Fixed the System Update page CSP mismatch by adding a per-response nonce to the page's inline script and existing inline styles.
- Changed release discovery to GitHub's `/releases/latest` stable endpoint and restricted artifact matching to `-source.zip` plus its matching `.sha256` file.
- Added active-job protection so concurrent update requests return HTTP 409 instead of starting competing upgrades.
- Moved update progress state from `/tmp` to the installer-created `/run/vibmail/update_status.json` runtime path and preserved `vmail` write access after root upgrade execution.
- Removed the dashboard's automatic `--allow-migrations` bypass so migration approval remains an explicit upgrader contract.
- Added focused System Update regression tests covering CSP/button markup, stable release assets, and active-job rejection.
- Validation evidence: focused update/security tests passed, Django system checks passed, forensic audit passed with `BLOCKING_FINDINGS=0`, upgrade contracts passed, and UI foundation tests passed.
- Follow-up audit fix: scoped the inline-style CSP exception to `/system-update/` only, and changed updater log rendering to `textContent` to prevent status messages from becoming admin-browser HTML.
- Follow-up validation: System Update/security tests passed with 19 tests, and Django test-settings checks passed with no issues.

### [2026-09-17] Version 1.3.5.1 revision release support

- Promoted the canonical root and Django package version to `1.3.5.1`.
- Extended release-gate, source-upgrade archive, and production upgrade-wrapper validation to accept optional four-component revision versions while preserving legacy `major.minor.patch` and RC formats.
- Added release identity, normalization, ordering, and workflow coverage for `1.3.5.1`; added `docs/RELEASE_NOTES_1.3.5.1.md` and synchronized the release workflow artifact and notes paths.
- Validation evidence: release workflow tests passed (7), upgrade contract tests passed, and diagnostics reported no errors in the touched Python files.

### [2026-09-17] Compact UI typography correction

- Reduced shared application emphasis to the compact `500` weight by changing the UI bold token and normalizing semantic `strong`/`b` content, card/page headings, table values, Dashboard recent-message titles, User names, and System Update metrics/modal headings.
- Preserved intentional brand, avatar, unread-state, navigation, and control emphasis weights.
- Validation evidence: UI foundation checks passed (8), System Update functional tests passed (4), Django checks passed, release and upgrade contracts passed, forensic audit passed with `BLOCKING_FINDINGS=0`, and `git diff --check` passed.

### [2026-09-17] CI stale documentation-contract correction

### [2026-09-17] CI inventory freshness follow-up

- GitHub Action run `35252391632` failed because a later `AGENTS.md` edit was pushed without regenerating `docs/FORENSIC_FILE_INVENTORY.json`; the forensic gate reported `INVENTORY_OUT_OF_DATE` with one blocking finding.
- Strengthened the post-update contract to require inventory regeneration/check after the final file edit with no subsequent tracked-file edits before commit or push.
- GitHub Action run `35253574019` reproduced the failure on commit `6deac14`: `.github/copilot-instructions.md` was hashed as 2301-byte CRLF content in the Windows-generated inventory, while GitHub's LF checkout was 2300 bytes. The inventory gate therefore failed despite a clean local check.
- Fixed the root cause in `scripts/generate_inventory.py` by canonicalizing UTF-8 text line endings to LF before calculating hashes and sizes; binary files remain byte-for-byte hashed.
- Fresh-checkout verification of `98c80aa` exposed the remaining aggregate mismatch: `summary.total_bytes` still counted raw CRLF bytes. Updated the generator to total the same canonical LF bytes used for text-file entries.

- GitHub Action run `35251723880` failed in `python scripts/forensic_audit.py --root .` because `documents/DOCUMENTATION_MANIFEST.json` was stale; the dependent forensic inventory was also stale, producing three blocking findings.
- Added a mandatory post-update rule to `AGENTS.md`: synchronize and check managed documentation, regenerate and check the forensic inventory, run forensic audit and relevant tests, and block commit/push until all generated contracts pass.

### [2026-09-17] CI Ruff lint correction

- GitHub Action run `35255798358` failed in `ruff check .` with UP032 in `mailbox-app/apps/core/middleware.py` and E501 in `mailbox-app/scripts/verify_upgrade_archive.py`.
- Replaced the CSP nonce `.format()` call with an f-string and wrapped the long `normalized_version` signature; the exact CI Ruff command now passes.
