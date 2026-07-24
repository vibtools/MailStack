# Forensic audit report — MailStack 1.3.0 RC1

**Audit date:** 2026-06-30  
**Release version:** `1.3.0-rc.1`  
**Target runtime:** Ubuntu Server 24.04 LTS and CPython 3.12  
**Release classification:** GitHub-ready open-source release candidate

## Executive disposition

| Gate | Status |
|---|---|
| Baseline feature preservation | PASS |
| Repository structure and public documentation | PASS |
| Complete AGPL-3.0 license text | PASS |
| Source secret/private-data safety gate | PASS |
| Python, JSON, YAML and shell syntax | PASS |
| Django application tests and coverage | PASS |
| Ruff and Bandit | PASS |
| Django checks and migration drift | PASS |
| Public contact-service tests | PASS |
| Installer and operations contract tests | PASS |
| Template rendering and placeholder validation | PASS |
| Forensic file/symbol inventory | PASS |
| Deterministic release ZIP, manifest and checksum | Required final build gate |
| Online dependency advisory query | PENDING — audit environment DNS unavailable |
| Clean Ubuntu 24.04 full-stack acceptance | PENDING external VPS |
| Real inbound SMTP/LMTP acceptance | PENDING external VPS |
| Copyright ownership/license confirmation | PENDING release owner |

**OPEN_SOURCE_RELEASE_CANDIDATE:** PASS  
**PRODUCTION_ACCEPTANCE:** PENDING

## Audited scope

The audit covers the complete maintained repository: Django application code, migrations, templates, static assets, tests, Postfix/Dovecot/MariaDB/Nginx/systemd templates, public website, contact service, installer, backup/restore/health scripts, CI workflows, release tooling, governance documents and repository metadata.

The deterministic machine-readable inventory at `docs/FORENSIC_FILE_INVENTORY.json` records every maintained file except itself and generated build/cache artifacts. It includes SHA-256, byte size, text-line count and Python/shell symbol information.

## Architecture

- Django 5.2.16 team mailbox application
- Gunicorn application service over a Unix socket
- MariaDB application schema and virtual-mail schema
- receive-only Postfix virtual mailbox delivery
- Dovecot LMTP delivery to Maildir
- durable Maildir ingestion worker
- safe MIME/HTML processing and protected attachment storage
- Nginx TLS reverse proxy and static/protected-file serving
- static public website and isolated rate-limited contact service
- systemd confinement
- backup, restore, rollback, health, verification, CI and deterministic release tooling

## Feature preservation

No functional application, migration, template, test, public-site or contact-service baseline file was deleted. The prior root `SOURCE_MANIFEST.sha256` was a generated snapshot and is deliberately regenerated inside every release archive rather than maintained as stale source metadata.

Preserved behavior includes:

- administrator and ordinary-user authentication
- administrator-managed user lifecycle
- object-scoped mailbox memberships
- mailbox create, enable, disable and soft-delete
- reserved postmaster/abuse handling
- receive-only Postfix/Dovecot delivery
- Maildir ingestion, duplicate protection and restart safety
- MIME parsing, HTML sanitization and attachment authorization
- search, pagination, counters and read/unread state
- live inbox updates
- security audit logging and health/readiness routes
- public website and protected contact workflow
- backup/restore/rollback and legacy `vibmail.my` compatibility

See `FEATURE_MATRIX.md` for the feature-by-feature verification record.

## Defects and release gaps remediated

1. Fixed-domain assumptions were generalized while retaining the legacy defaults.
2. Production settings now fail closed for invalid hostnames, paths, origins, secrets and SQL identifiers.
3. Source and release scanners block credentials, private keys, databases, Maildir, attachments, logs and archives.
4. MariaDB privileges and `SQL SECURITY INVOKER` views use least-privilege access.
5. Postfix has no mailbox-secret, write or DDL access.
6. Dovecot remains LMTP-only under the fixed virtual-mail identity.
7. Installer validation rejects hostname collisions and malformed arguments.
8. Backup/restore checksums, archive safety and exact prior service-state restoration were strengthened.
9. Repository documentation, governance, SEO metadata, community templates and release automation were completed.
10. The complete AGPL-3.0 license text and licensing rationale were added.
11. A deterministic file/symbol inventory and documentation consistency gate were added.
12. Local audit virtual environments are ignored without weakening generated-artifact release blocking.

## Automated evidence

- Django tests: **189 passed, 0 failed**
- Application coverage: **94.99%**; minimum: **85%**
- Ruff: **PASS**
- Bandit: **PASS**
- Django system check: **PASS**
- Migration drift: **none**
- Contact-service test program: **PASS**
- Deployment templates rendered: **13**, unresolved tokens: **0**
- Installer plans: **2 valid and 9 invalid cases**, all passed
- Backup/restore/health contracts: **PASS**
- Shell syntax: **13 files PASS**
- Source forensic gate: **PASS with zero blocking findings**
- Documentation gate: **23 required documents PASS**
- Python environment consistency (`pip check`): **PASS**

The tests ran locally with Python 3.13.5 because it is the available audit runtime. Package metadata and CI constrain production to Python 3.12 on Ubuntu 24.04.

## Security review

Verified controls include root-only generated secrets, strict configuration validation, Argon2 password hashing, CSRF and secure-cookie controls, login throttling, object-level mailbox authorization, safe HTML sanitization, protected attachments, receive-only SMTP, no public registration, no IMAP/POP3/submission in the reference deployment, MariaDB least privilege, systemd sandboxing, safe archive extraction, checksum verification and fail-closed CI/release gates.

The online `pip-audit` command was attempted but could not resolve `pypi.org` in the isolated environment. This is not a passing vulnerability result; the network-enabled CI step remains blocking.

## Performance review

Web requests and Maildir ingestion remain separate services. Gunicorn worker/thread counts are bounded, database connections are reused, mailbox/message fields are indexed, list views are paginated, live-update scopes are bounded, attachments remain file-backed and Nginx serves static/protected files. Backup/restore performs controlled service quiescing and restores the exact prior active state.

## GitHub/open-source readiness

The repository includes an SEO-oriented README, logo asset, release/download/license/platform/language/community badges, GitHub topics and description guidance, full license, notice, security policy, contribution guide, code of conduct, support policy, roadmap, issue/PR templates, CODEOWNERS, Dependabot, CI, release workflow, installation/build/development/operations/security documentation and Vib Tools ecosystem links.

## External acceptance gates

Before stable promotion:

1. Confirm source ownership and third-party license compatibility.
2. Require GitHub CI, including the online dependency advisory audit, to pass.
3. Install on a clean isolated Ubuntu Server 24.04 VPS.
4. Verify DNS, MX, PTR/rDNS, TLS, firewall, unknown-recipient rejection, LMTP delivery, ingestion, authorization, contact delivery, backup, restore and restart recovery.
5. Publish the first version as `v1.3.0-rc.1`; promote to stable only after acceptance.

## Final classification

The repository is approved for public publication as **MailStack 1.3.0 RC1**, not yet as a proven stable production release.
