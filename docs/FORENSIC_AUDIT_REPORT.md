# Forensic audit report — MailStack 1.3.0 RC3

**PHASE-003 audit date:** 2026-08-17
**Release version:** `1.3.0-rc.4`
**Target runtime:** Ubuntu Server 24.04 LTS and CPython 3.12
**Release classification:** locally structurally qualified release candidate; dependency-backed RC3 CI requalification pending

## Executive disposition

| Gate | Status |
|---|---|
| Baseline feature preservation | PASS |
| Repository structure and public documentation | PASS |
| User manual, how-to, admin guide and phase-document baseline | PASS |
| UI design intake, immutable-source manifest and design contract tests | PASS in GitHub Actions run `30165905840` |
| PHASE-002 shared UI foundation structural contracts | PASS locally — 8 tests |
| PHASE-002 local Django, coverage and mailbox lint qualification | PASS — 195 passed, 1 skipped, 94.99% coverage |
| Deterministic documentation index, manifest and change policy | PASS |
| Complete AGPL-3.0 license text | PASS |
| Source secret/private-data safety gate | PASS |
| Python, JSON, YAML and shell syntax | PASS |
| Django application tests and coverage | PASS |
| Ruff and Bandit | PASS for mailbox application; standalone contact-service gates added to final verifier and CI |
| Django checks and migration drift | PASS |
| Public contact-service tests | PASS |
| Installer and operations contract tests | PASS |
| Template rendering and placeholder validation | PASS |
| Forensic file/symbol inventory | PASS |
| Deterministic release ZIP, manifest and checksum | PENDING RC4 CI; deterministic local build/verification required before patch handoff |
| Online dependency advisory query | PENDING RC4 rerun — RC2 run `32053931714` failed on sqlparse 0.5.5; RC3/RC4 pin 0.6.0 |
| Clean Ubuntu 24.04 RC3 full-stack acceptance | PENDING exact-RC3 clean VPS requalification |
| Real inbound SMTP/LMTP acceptance | PASS in staging after equivalent PHASE-003 LMTP hotfix; exact-RC3 clean requalification pending |
| Copyright ownership/license confirmation | PENDING release owner |

**OPEN_SOURCE_RELEASE_CANDIDATE:** PENDING RC4 CI
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
13. A root `documents/` baseline now provides maintained user, administrator and phase documentation.
14. Deterministic synchronization, draft blocking and diff-based CI policy prevent maintained feature changes from merging without substantive documentation.
15. The complete 25-image UI and logo archive is preserved with stable IDs, SHA-256 hashes, PNG structural validation, scope classification, and CI enforcement.
16. PHASE-002 adds the frozen runtime design tokens, responsive authenticated and sign-in shells, local SVG assets, accessible navigation behavior, and focused UI contract gates without changing page business logic.
17. Cross-platform verification now closes contact-service SQLite handles deterministically, preserves POSIX-only permission assertions, and subjects the standalone contact service to Ruff and Bandit in both the full forensic gate and CI.
18. RC3 updates the vulnerable transitive sqlparse 0.5.5 lock to upstream 0.6.0 after the blocking PHASE-003 CI advisory scan identified four 2026 CVEs; no advisory suppression or application behavior change is introduced.

## Automated evidence

- Last completed pre-RC3 Django suite: **195 passed, 1 capability-based skip, 0 failed**; RC3 full rerun pending
- Application coverage: **94.99%**; minimum: **85%**
- Ruff: **PASS**
- Bandit: **PASS**
- Django system check: **PASS**
- Migration drift: **none**
- Contact-service test program: **PASS**, including deterministic connection-close regression coverage
- Deployment templates rendered: **13**, unresolved tokens: **0**
- Installer plans: **2 valid and 9 invalid cases**, all passed
- Backup/restore/health contracts: **PASS**
- Shell syntax: **13 files PASS**
- Source forensic gate: **PASS with zero blocking findings**
- Engineering documentation gate: **PASS**
- User-document synchronization, manifest and policy tests: **PASS**
- Python environment consistency (`pip check`): **PASS**

The authoritative repository qualification is GitHub Actions run `30133728843` on Ubuntu 24.04 with Python 3.12 at commit `1e1737edea2e6c922265a15d8584b56671820c65`. Local isolated audit environments remain useful for non-networked structural checks but do not replace CI.

## Security review

Verified controls include root-only generated secrets, strict configuration validation, Argon2 password hashing, CSRF and secure-cookie controls, login throttling, object-level mailbox authorization, safe HTML sanitization, protected attachments, receive-only SMTP, no public registration, no IMAP/POP3/submission in the reference deployment, MariaDB least privilege, systemd sandboxing, safe archive extraction, checksum verification and fail-closed CI/release gates.

The historical pre-PHASE-003 `pip-audit` gate passed in GitHub Actions run `30133728843`.
For the current PHASE-003 branch, run `32053931714` failed at the blocking advisory step because
`sqlparse==0.5.5` was newly reported for CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and
CVE-2026-54284. RC3 pins upstream sqlparse 0.6.0, which contains those security fixes. The RC3
dependency audit, `pip check`, and all downstream CI gates remain mandatory; no vulnerability is
ignored or waived.

## Performance review

Web requests and Maildir ingestion remain separate services. Gunicorn worker/thread counts are bounded, database connections are reused, mailbox/message fields are indexed, list views are paginated, live-update scopes are bounded, attachments remain file-backed and Nginx serves static/protected files. Backup/restore performs controlled service quiescing and restores the exact prior active state.

## GitHub/open-source readiness

The repository includes an SEO-oriented README, logo asset, release/download/license/platform/language/community badges, GitHub topics and description guidance, full license, notice, security policy, contribution guide, code of conduct, support policy, roadmap, issue/PR templates, CODEOWNERS, Dependabot, CI, release workflow, installation/build/development/operations/security documentation and Vib Tools ecosystem links.


## PHASE-002 audit boundary

The phase changes only the shared base template, shared static foundation assets and JavaScript,
focused tests, the contact-service connection-lifecycle helper, CI/audit tooling, generated
inventories, and required documentation. It contains no model, migration, URL, form, permission,
mail-flow, ingestion schema, deployment-template, or package change. Local dependency-backed tests
and coverage passed; the final overwrite verifier must pass before commit, and GitHub Actions must
pass before remote qualification.

## PHASE-003 audit boundary

PHASE-003 changes only installer/recovery behavior, the Dovecot LMTP static-userdb template,
one-shot ingestion verification semantics, narrowly qualified production MariaDB warnings, focused
management-command/test contracts, release metadata, and required documentation. It adds no database
migration, dependency, UI page, URL, permission model, outbound mail path, or data transformation.

The structural forensic gate passes with zero blocking findings after regenerating the deterministic
file inventory. RC4 additionally centralizes verified Bash runtime discovery for repository-level
installer, operations, and forensic tooling: Windows prefers Git for Windows Bash over the WSL
launcher, while Linux keeps the system Bash contract. This prevents an unavailable WSL/Docker
Desktop backing disk from being reported as multiple MailStack shell syntax defects. A subsequent
Windows run proved Git Bash selection was correct but exposed a second host-compatibility edge: the
Windows Python installation provided `python` but no Git-Bash-visible `python3` command. The RC4
audit harness now uses a process-local `BASH_ENV` bridge to map `python3` to the exact interpreter
running the test harness on Windows only; `install.sh` and Ubuntu's production `python3` behavior
remain unchanged. Dependency-free documentation, design, UI-foundation, template, installer,
operations, Python compile, and shell-syntax gates pass locally. Dependency-backed
Django/Ruff/Bandit/coverage and full-forensic qualification remain blocking in GitHub Actions because
the local artifact builder does not contain or have network access to the pinned development
environment.

## External acceptance gates

Before stable promotion:

1. Confirm source ownership and third-party license compatibility.
2. Preserve the successful GitHub CI baseline and require every subsequent release commit to pass all blocking gates.
3. Install on a clean isolated Ubuntu Server 24.04 VPS.
4. Verify DNS, MX, PTR/rDNS, TLS, firewall, unknown-recipient rejection, LMTP delivery, ingestion, authorization, contact delivery, backup, restore and restart recovery.
5. Publish `v1.3.0-rc.4` only after its blocking CI gates pass; promote to stable only after the remaining acceptance gates pass.

## Final classification

The repository remains a **MailStack 1.3.0 RC4 release candidate**, not yet a proven stable production release. PHASE-003 source qualification is complete only when its blocking GitHub Actions run passes.
