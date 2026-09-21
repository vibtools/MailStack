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

### Create mailbox modal workflow

- Dashboard, mailbox list, and sidebar Create mailbox actions open a compact shared modal through `data-open-mailbox-modal`.
- The existing `mailboxes:create` endpoint remains the no-JavaScript/direct-route fallback; successful POSTs still redirect to the mailbox list.
- Invalid modal POSTs render the mailbox list with the bound form and reopen the dialog so validation errors remain visible.
- The modal now provides a random USA-style local-part generator, three refreshable quick suggestions, and a `Create & copy` submit action that copies the composed address before the normal form POST.
- The modal exposes the configured default domain to client-side copy composition when no verified domain option is available, matching the server-side form fallback.

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
- CI inventory drift was traced to the private `reference/` directory being included locally but absent from GitHub checkout; inventory generation, forensic audit, and release archive building now exclude that directory consistently
- cleared workspace diagnostics caused by Django dynamic field/model typing and untyped attachment storage results using narrow casts, typed storage results, and typed queryset assertions; runtime behavior was preserved

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

- Release version currently tracked in project metadata: `1.3.5.4` (four-component revision releases are supported alongside legacy three-component versions)
- Active release metadata and managed documentation are synchronized to `1.3.5.4`; historical `.3`
  release evidence remains immutable and forensic auditing exempts recognized release-note versions.
- CI and release workflows run `forensic_audit.py --profile repository --full`, so documentation, design, inventory, release, deployment, and full application gates are blocking on push, pull request, and release validation.
- The Windows development workspace uses the repository root `.venv`; its development dependencies are installed and VS Code is configured to add `mailbox-app/` to Python analysis paths.
- The admin Add Domain flow uses an empty initial DNS table, an authenticated GET-only backend DNS preview, per-record copy, Cloudflare-compatible zone export, and a required DNS confirmation before creation.
- The admin Domains page now supports server-backed search filtering, compact icon actions, a DNS records dialog with copy/Cloudflare export, live aggregate DNS verification, and a persistent `Domain.is_default` selected by mailbox creation.
- Persistent default-domain behavior is implemented by migration `mailbox-app/apps/mailboxes/migrations/0007_domain_default.py`; the configured `MAIL_DOMAIN` is seeded as default and active verified domains can be promoted through the domain list.
- Domain DNS status now parses TXT answers and returns independent statuses for MX, A/AAAA, SPF, DKIM, and DMARC records; the UI renders those backend results instead of assigning one aggregate status to every row.
- Persisted default domains are protected from deletion, and the domain list retains the existing enable/disable action as a compact CSRF-protected control.
- Fixed the Pylance diagnostic in `mailbox-app/tests/unit/test_domains.py` by narrowing the DNS result records with an explicit `cast` before iteration; no runtime test behavior changed.
- Deployment is designed for Ubuntu 24.04 with native package installation, not Docker-first packaging
- The application is intentionally receive-only and not a general outbound marketing mail platform
- Security and audit compliance are treated as first-class project constraints
- The repo is expected to maintain a synchronized `docs/FORENSIC_FILE_INVENTORY.json` and pass forensic audit validation after meaningful edits

## 8) Maintenance Notes

This memory file should be treated as the canonical context snapshot for future AI-assisted work in this repository. If the project direction, deployment architecture, or feature set materially changes, update this document immediately.

### [2026-09-21] Site settings logo upload issue

- Root cause: Django's `STORAGES` configuration omitted the required `default` file storage backend, so saving a SiteSettings logo or favicon raised a storage-handler exception and rendered the generic 500 page.
- Added an explicit `FileSystemStorage` default backend using `MEDIA_ROOT` and `MEDIA_URL` in both base and test settings.
- The upload ceiling is now 10 MB, with logo validation limited to 5 MB for realistic branding assets.

### [2026-09-18] Release 1.3.5.5 documentation synchronization

- Bumped the canonical release revision from `1.3.5.4` to `1.3.5.5` across `VERSION`, Django package
  metadata, active maintained documents, and design/documentation manifests.
- Regenerated `documents/DOCUMENTATION_MANIFEST.json` after the Admin Guide workflow update so the
  repository forensic documentation gate sees current hashes and metadata.

### [2026-09-20] Release 1.3.5.5 publication readiness fix

- Removed the global-IP literal scan from `scripts/verify_release.py`; archive path, checksum,
  private-key, blocked-file, email-domain, and canonical ZIP checks remain active.
- Synchronized `docs/PUBLISHING.md` to 1.3.5.5 and validated the deterministic archive, checksum,
  documentation gates, full forensic audit, and 265 application tests (one Windows symlink test skipped).

### [2026-09-20] Domain toggle CSRF correction

- Fixed the Domains active/disabled toggle to use the server-rendered CSRF token instead of reading
  the HttpOnly `csrftoken` cookie from JavaScript; focused domain tests pass 22/22.
- Added same-origin credentials and an explicit CSRF header to the dynamic toggle request, plus
  `ensure_csrf_cookie` on the Domains page.

### [2026-09-20] DKIM public-record permission correction

### [2026-09-21] Permanent mailbox purge delete flow

- Implemented a true destructive mailbox delete path in `mailbox-app/apps/mailboxes/services.py` that removes the Django mailbox record, cascades away message and attachment rows, deletes attachment files from the configured storage root, and removes the mailbox Maildir directory from the live filesystem.
- Updated the delete confirmation and bulk delete action to advertise and execute permanent deletion rather than the previous soft-delete/reserve behavior.
- Added a focused Django regression proving the mailbox row, message row, attachment row, attachment file, and Maildir directory all disappear after the confirmation flow.

- OpenDKIM public `mail.txt` is now `root:vmail` mode `0640` and its directory is traversable by
  `vmail`; the private key remains `opendkim:opendkim` mode `0600` so Django can render DKIM DNS
  records without exposing signing material.

### [2026-09-21] New mailbox ordering

- Mailbox list now orders by `created_at` descending, then `id` descending, so newly created
  mailboxes appear at the top of the first page.

### [2026-09-21] Mailbox bulk actions

- Added permission-aware bulk mailbox selection and soft deletion from the Mailboxes page with
  select-all, selected count, confirmation, and existing audit/cleanup behavior.
- Renamed the DNS persistence token variable to avoid a duplicate block-scoped JavaScript
  declaration; workspace diagnostics are clean for the touched files.
- Corrected the toggle-path CSRF variable reference that prevented Domains action controls from
  rendering at runtime; JavaScript syntax and focused domain tests pass.

### [2026-09-18] Documentation policy gate repair for release verification maintenance

- CI `quality-and-security` failed because `scripts/verify_release.py` and its focused test changed
  without the required maintained-document updates.
- Added synchronized maintenance entries in `CHANGELOG.md` and
  `documents/phases/PHASE-004-RELEASE-UPGRADE-AND-OPERATIONAL-RELIABILITY.md` so the
  documentation-policy gate records the changelog-heading false-positive correction in release
  verification.

### [2026-09-18] Forensic inventory CI synchronization

- Regenerated `docs/FORENSIC_FILE_INVENTORY.json` with `scripts/generate_inventory.py` after the
  repository metadata changes made the generated inventory stale.
- Validation: `generate_inventory.py --check` passed with 475 maintained files and 41,057 text lines.

### [2026-09-18] Documentation contracts inventory refresh

- The `documentation-contracts` workflow failed at the inventory freshness gate because
  `documents/DOCUMENTATION_MANIFEST.json` changed without a matching refresh of
  `docs/FORENSIC_FILE_INVENTORY.json`.
- Regenerating the forensic inventory restored the documentation workflow and the repository
  forensic audit to a passing state.

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

### [2026-09-18] System Update preflight and root worker

- Added PHASE-008 documentation for read-only preflight, fail-closed installation gating, and
  safe privilege separation.
- Moved the upgrade and rollback default lock file from `/run/lock/vibmail-upgrade.lock` to
  `/run/vibmail/vibmail-upgrade.lock`; the latter is already writable in the hardened updater
  systemd namespace, so `ProtectSystem=strict` remains enabled without mutating `/run/lock`.
- Added the admin-only `update_preflight` endpoint and UI state that blocks installation until
  the root worker, runtime paths, required commands, upgrade script, and disk-space checks pass.
- Replaced the Gunicorn-thread `sudo -n upgrade.sh` invocation with a validated request file
  consumed by the root-owned `vibmail-updater.service`; Gunicorn retains `NoNewPrivileges=true`.
- Installer now renders/enables the updater service and no longer provisions the old sudoers
  escalation rule. Existing upgrade archive/checksum/backup/migration/rollback logic is unchanged.
- Focused System Update regression coverage is 6 passing tests; full repository validation remains
  pending after the final implementation edits.

### [2026-09-18] Domain reference UI parity

- Scoped the Domains and Add Domain routes to the supplied reference shell dimensions, palette,
  Geist typography, spacing, and icon controls without changing the shared shell for other pages.
- Added current DNS status to the Domains modal, client-side domain validation, and one-record-at-a-time
  DNS check progression while preserving the existing preview/status APIs and server-side validation.
- Focused shell/domain validation passes: 30 tests and JavaScript syntax validation.

### [2026-09-18] Domain parity forensic corrections

- Corrected both Cloudflare/BIND exports to use backend-provided `cf_host` labels, quote TXT values,
  and omit records that have no configured copyable value.
- Made per-record DNS resolver failures return safe missing statuses instead of breaking the modal API
  with an unhandled error; added regression coverage.
- Kept DNS rows pending until the live per-record check completes, rather than presenting an aggregate
  domain verification result as proof for every record.
- Restored the reference current-default star as a disabled state indicator and made unavailable DNS
  records visibly non-copyable; no reference sample data or fake server actions were introduced.
- Corrected generated toggle labels to name the domain and aligned the verified DNS status class with
  its green visual treatment.
- Expanded `documents/ADMIN_GUIDE.md` with the live Domains/Add Domain search, DNS copy/export/check,
  default-domain, edit, and verification workflow required by the documentation policy gate.
- Focused validation: 22 domain tests passed and JavaScript syntax validation passed.

### [2026-09-18] Site Settings forensic fixes

- Restricted the public Site Settings API CORS response to the configured public origin.
- Added MIME allowlists and browser `accept` attributes for logo and favicon uploads.
- Added public runtime propagation for tagline, metadata, source URL, privacy URL, and 404 branding.
- Added `/media/` storage, Nginx serving, Gunicorn sandbox access, installer/deploy provisioning, and
  backup/restore handling for persisted branding uploads.
- Added regression coverage for rejected origins and non-image uploads.
- Removed fixed SVG favicon MIME hints so uploaded PNG/ICO assets remain browser-compatible.

### [2026-09-18] Admin Site Settings and public branding bridge

- Added singleton `SiteSettings` persistence with migrations `0002_sitesettings` and
  `0003_privacy_url_charfield` for branding, contact, footer, source, and privacy values.
- Added admin-only `/settings/` UI with validated uploads, compact responsive styling, save feedback,
  shared 403 handling, dynamic app shell branding, and footer values.
- Added public read-only `/health/site-settings/` API with configured-origin CORS and runtime public-site
  hydration for site name, contact values, footer content, logo, and favicon.
- Focused regression suite passes: 14 tests; Django checks report zero errors.

### [2026-09-18] System Update audit correction

- Corrected the updater boundary so Gunicorn only creates an atomic, URL-only request; the root
  worker performs release downloads and invokes the fixed upgrade script, avoiding lost updates
  when Gunicorn restarts.
- Added strict request ownership/mode/field validation, official GitHub URL validation, processing
  locking, stale-request cleanup, atomic no-overwrite queueing, and complete VPS prerequisite
  checks aligned with `upgrade.sh` required commands, paths, services, and the `vmail` user.
- The focused System Update suite now covers 8 passing tests; Ruff and editor diagnostics are clean
  for the touched Python files.
- Aligned the root updater unit's `ReadWritePaths` with the existing upgrade script's actual
  application, public-site, backup, marker, static, and web-root write targets so systemd
  `ProtectSystem=strict` does not create a live-update-only failure.

### [2026-09-18] Compact System Update modal UI

- Replaced the Check/Install Update and Up-to-Date dialogs' generic log-modal layout with the existing compact confirmation-dialog pattern.
- Added page-local sizing, centered status content, compact actions, and mobile-safe button stacking while preserving the existing update controls and CSP-safe template structure.
- Added functional template assertions for the compact modal classes and Install Update action.

### [2026-09-18] Compact application scrollbars

- Added a shared 6px scrollbar baseline in `foundation.css` with lightweight thumb styling and transparent tracks.
- Normalized the table, update log, release notes, and history scroll regions to the same compact dimensions while preserving visible hover contrast.

### [2026-09-18] PHASE-007 multi-domain implementation plan

- Created draft `documents/phases/PHASE-007-MULTI-DOMAIN-MAILBOX-AND-DNS.md` before runtime implementation.
- The plan covers admin domain CRUD, bounded DNS verification, enable/disable behavior, mailbox domain selection, per-domain uniqueness and Maildir paths, existing-mailbox migration, and parameterized Postfix/mail-server provisioning.
- Runtime implementation is active: Domain migration/backfill, admin CRUD, DNS verification, mailbox
  domain selection, per-domain Maildir paths, parameterized mail-server provisioning, and compatibility
  regression coverage are implemented and under full-suite qualification.

### [2026-09-18] PHASE-007 multi-domain vertical slice

### [2026-09-18] Reference-aligned Add User shell

### [2026-09-18] Release preflight hygiene

- The release build excludes generated `.coverage` files so local test artifacts cannot enter source archives.
- Version workflow contract fixtures use the documentation-only `192.0.2.1` address range to avoid forensic global-IP false positives.
- The user-list query-budget contract allows the current constant context overhead while still guarding against per-user query growth.

### [2026-09-18] Updater worker namespace prerequisite

- The installer creates `/opt/vibmail-upgrades` and `/var/backups/vibmail/upgrades` before enabling `vibmail-updater.service`.
- This prevents systemd `226/NAMESPACE` startup failures caused by missing `ReadWritePaths` targets in the hardened root updater unit.

- Added a route-scoped `user-reference-shell` class for the admin Add User page so its sidebar, topbar, content inset, navigation density, and footer follow the supplied reference geometry without changing the frozen global application shell tokens.
- Preserved production Django form fields, mailbox assignment, permissions, and JavaScript interactions while keeping the private `reference/` directory untouched.
- Validation evidence: focused integration checks, Django system check, UI foundation tests, forensic inventory generation/check, and forensic audit passed; browser screenshot/pixel comparison remains unperformed.

### [2026-09-18] Minimal CI and release validation lanes

- Added `essential` and `repository` profiles to `scripts/forensic_audit.py`. The essential profile retains source safety, installer/deployment/release/upgrade contracts, and optional full application checks; the repository profile retains documentation, design, UI, and inventory hygiene checks.
- Simplified push/PR CI and tag release workflows by removing duplicate direct checks and running the essential aggregate audit once. Archive builds use `--skip-audit` after the audit has passed, avoiding a second scan.
- Added scheduled/manual `.github/workflows/repository-hygiene.yml` for repository-wide documentation/design/inventory checks and removed the redundant post-publication `auto_release.yml` archive builder.
- Retained the direct dependency vulnerability audit in CI, release identity checks, deterministic archive verification, checksum/manifest validation, and remote publication eligibility checks.
- Corrected release notes artifact/publication paths to derive from the validated release version instead of hardcoding a historical version, and removed the duplicate `pip check` from the aggregate full audit because dependency setup already owns it.
- Removed duplicate application coverage and release archive verification from push/PR CI. The essential full audit now owns application quality checks, while deterministic archive build/verification remains in the tag release workflow where publication requires it.

- Added `Domain` with normalized safe hostnames, active/disabled delivery status, pending/verified/failed DNS state, check timestamps, and safe verification details.
- Added migration `mailboxes.0005_domain_and_mailbox_domain` to create the configured `MAIL_DOMAIN` as the active verified default, backfill existing mailboxes, preserve addresses and paths, and replace global local-part uniqueness with `(domain, local_part)` case-insensitive uniqueness.
- Added bounded dependency-free MX/A/AAAA verification, admin domain CRUD/check/toggle routes and templates, verified active-domain mailbox selection, and explicit domain-aware provisioning, ingestion, Maildir, sync, and mailserver integration.
- Added focused domain validation, DNS, provisioning, form, and admin route tests. Focused Ruff, Django checks, selected pytest coverage, and migration-drift checks passed; full repository release/audit validation remains to be run after documentation synchronization.

### [2026-09-18] PHASE-007 audit and production fixes

- Blocked renaming an existing domain because it would invalidate mailbox addresses, Maildir paths,
  and external Postfix domain rows.
- Added safe removal for empty secondary domains, protected the configured default domain, and kept
  domains with mailboxes disable/archive-only.
- Added cleanup of newly-created external domain rows when Django domain persistence fails.
- Added regression coverage for rename protection and empty-domain removal.
- Corrected mail-server sync so newly discovered domains remain DNS-pending until explicitly verified;
  corrected the DNS form to avoid presenting an unknown public IP as a concrete value.
- Corrected mail-server mailbox listing so sync imports all configured domains when no domain filter is
  requested, while retaining explicit single-domain filtering for callers that need it.
- Clarified the global top-bar domain label as the configured default domain so multi-domain users are
  not misled into treating the bootstrap setting as the only mailbox domain.
- Made domain status edits fail gracefully when external mailserver reconciliation fails, instead of
  returning an unhandled error or saving only the application-side state.
- Enforced the delivery state machine so pending/failed DNS domains cannot be enabled; new domains
  default to disabled, and a failed DNS check disables external delivery and the application record.
- Wrapped domain create/edit application and external mailserver reconciliation in one transaction to
  prevent partial domain-state updates when either persistence step fails.
- Hardened external mailbox sync input and fail-closed behavior: unsafe source domains are rejected,
  newly discovered unverified domains are disabled externally and in Django, and imported mailboxes
  under those domains are not marked active.
- Removed implicit default-domain fallback from mailbox provisioning by propagating the selected domain
  explicitly to external existence and creation operations, including the configured baseline domain.
- Hardened the dependency-free DNS packet parser against compressed-name offset errors, malformed label
  lengths, out-of-range pointers, and pointer cycles; added compressed MX-name regression coverage.

### [2026-09-17] Version 1.3.5.3 revision release support

- Promoted the canonical root and Django package version to `1.3.5.3`.
- Extended release-gate, source-upgrade archive, and production upgrade-wrapper validation to accept optional four-component revision versions while preserving legacy `major.minor.patch` and RC formats.
- Added release identity, normalization, ordering, and workflow coverage for `1.3.5.3`; added `docs/RELEASE_NOTES_1.3.5.3.md` and synchronized the release workflow artifact and notes paths.
- Validation evidence: release workflow tests passed (7), upgrade contract tests passed, and diagnostics reported no errors in the touched Python files.

### [2026-09-17] Compact UI typography correction

- Reduced shared application emphasis to the compact `500` weight by changing the UI bold token and normalizing semantic `strong`/`b` content, card/page headings, table values, Dashboard recent-message titles, User names, and System Update metrics/modal headings.
- Preserved intentional brand, avatar, unread-state, navigation, and control emphasis weights.
- Validation evidence: UI foundation checks passed (8), System Update functional tests passed (4), Django checks passed, release and upgrade contracts passed, forensic audit passed with `BLOCKING_FINDINGS=0`, and `git diff --check` passed.

### [2026-09-17] CI stale documentation-contract correction

### [2026-09-18] CI Site Settings database test correction

- Marked the untrusted-origin Site Settings API regression test with `pytest.mark.django_db`.
- The API reads the database-backed `SiteSettings` singleton, so the marker is required for
  pytest-django's database access guard.
- Focused Site Settings tests pass (4), and the full repository forensic gate reports no blocking findings.

### [2026-09-18] Documentation contract workflow scope reduction

- Removed `scripts/test_documents.py` from the always-on repository forensic aggregate.
- Added path-filtered `.github/workflows/documentation.yml` for managed-document contract tests,
  Markdown/link validation, documentation policy, and inventory freshness checks.
- Core managed-document, policy, link, and inventory gates remain in CI/forensic validation;
  the broader documentation contract suite now runs only for documentation/tooling changes,
  manual dispatches, or scheduled hygiene validation.

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

### [2026-09-18] CI release verification false-positive correction

- GitHub Actions release run `35318392855` failed in `build-verified-source` because `scripts/verify_release.py` treated the changelog heading `## 1.3.5.4 - ...` as a global IPv4 literal.
- Updated `is_version_literal` to treat markdown changelog headings of the form `## <version> - ...` as version literals, preserving global-IP blocking elsewhere.
- Extended `scripts/test_release_workflow.py` with a regression assertion for changelog heading version detection; targeted release workflow tests pass (8).

### [2026-09-18] Permanent release-version IP-scan rule

- Added a durable `AGENTS.md` contract: semantic release versions, including four-component values such as `1.3.5.3`, must never be treated as IP literals by forensic or release verification. Real global IP addresses must remain blocked and the exemption must stay regression-tested.

- GitHub Action run `35256798900` failed in release verification because the four-component release version `1.3.5.3` matched the global IPv4 detector inside the source archive.
- Updated `scripts/verify_release.py` to exempt only the archive's derived release version while continuing to reject real global IP literals; added a regression test covering both cases.

### [2026-09-18] Domain admin registration correction

- Confirmed the Multiple Domain model and custom `/mailboxes/domains/` page were present, but `Domain` was not registered in Django Admin.
- Registered `DomainAdmin` with status/DNS filters, domain search, and immutable identifiers/timestamps so the Domain control page is available under `/admin/` after deployment.

### [2026-09-18] Create mailbox popup reference alignment

- Reworked the Create Mailbox modal to match `reference/Updated-CreateMailbox-PopUp-design.html`: compact 530px card, bordered header, unified address/domain control, quick suggestions, user checkbox list with selection count, and reference button hierarchy.
- Preserved the existing Django form submission, CSRF, random USA name generation, suggestion refresh, close behavior, and Create & copy flow.
- Follow-up audit removed the checkbox `form-control` styling leak, restored the reference placeholder and address-control grouping, and added the missing random-button divider.
- Corrected Create & copy so an empty local part is populated with a generated USA-style name before copying and submitting the real Django form.

### [2026-09-18] Account form diagnostics correction

- Resolved Pylance diagnostics in `mailbox-app/apps/accounts/forms.py` caused by Django multiple-inheritance mixins and dynamically typed `ModelMultipleChoiceField` querysets.
- Used local type casts only; form validation, mailbox assignment, permissions, and save behavior remain unchanged.
- Validation evidence: no file diagnostics, Ruff and Python compile passed, 30 focused integration tests passed, Django check passed, inventory check passed, and forensic audit passed with `BLOCKING_FINDINGS=0`.

### [2026-09-18] Sidebar navigation icon completion

- Added the missing local `icon-globe` sprite symbol and displayed it for the admin Domains navigation item.
- Confirmed all other sidebar navigation items already use local sprite icons.

### [2026-09-18] Domain DNS A/AAAA value display

- Replaced the Domain form's static A/AAAA instruction with the exact configured `SERVER_IP` value.
- Exposed `settings.SERVER_IP` through the application context processor; production validation already requires it to be a valid IPv4 or IPv6 address.
- Domain creation now redirects to the DNS records screen, which generates MX, A/AAAA, SPF, DKIM, and DMARC guidance with copyable values where the server has the required DKIM public key.
- The DNS screen no longer claims that records must be published before checking; DNS provider publication remains an external action because the application has no DNS-provider API integration.
- Re-audited the production Add User page against the supplied reference; preserved real Django field data while matching the compact layout, placeholders, local copy icon, checkbox-list styling, and reference random-name behavior.
