# Changelog

All notable repository-level changes are recorded here. Application history before the open-source conversion remains in `mailbox-app/CHANGELOG.md`.

## 1.3.0-rc.5 — Unreleased

### Documentation and forensic baseline

- Finalized the published RC4 evidence in the forensic and test reports using the successful `main`, tag-CI, and release-artifact workflow results instead of the pre-release RC3/RC4-pending wording.
- Established `MAILSTACK-1.3.0-RC4-OFFICIAL-SOURCE-BASELINE-001` as the current official source baseline, anchored to tag `v1.3.0-rc.4`, commit `896dbcc2ed1f38d9c618bf0b712efe5923f92e56`, tree `0d845b3d975949894c24581e6834aff7b33c30b4`, and deterministic source SHA-256 `58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`.
- Preserved the earlier RC1 documentation baseline as historical provenance instead of treating its source commit as the current release anchor.
- Added the PHASE-004 release, upgrade, and operational-reliability record; PHASE-004A changes documentation, release metadata, and generated manifests only.

### Release automation

- Added a fail-closed release gate that requires tag/version/package-version agreement, the exact current `main` head, successful `main` push CI for the tagged SHA, and absence of an existing GitHub Release before publication.
- Split tag release handling into a read-only verified-build job and a write-scoped publication job; manual `workflow_dispatch` remains validation/build-only.
- Automated GitHub Release creation with deterministic source ZIP and SHA-256 assets, RC pre-release classification, stable latest classification, and overwrite/clobber prevention.
- Added focused release-workflow contract tests and made them blocking in CI and the forensic audit.

### Existing-server upgrade and rollback

- Added a generic fail-closed existing-server upgrade driver that requires a deterministic source ZIP plus matching SHA-256, validates canonical archive/manifest/version integrity, stages outside the live tree, and rejects downgrade, same-version, removed-migration, or modified-migration targets.
- Added explicit migration acknowledgement, a non-blocking runtime lock, a verified pre-mutation consistent data backup, source/runtime rollback snapshots, application/public-site staged replacement, dependency convergence, post-upgrade contract checks, and installation-marker provenance.
- Preserved Postfix and Dovecot during the source mutation window after the consistent backup has completed, allowing accepted inbound mail to accumulate safely in Maildir while ingestion is paused.
- Added migration-aware fail-closed recovery: automatic source/runtime rollback is allowed only when no new schema migration has begun; migration-capable failures require reviewed schema/data reconciliation instead of an automatic database restore that could discard newly accepted mail.
- Added focused non-destructive upgrade/archive/rollback contract tests and made them blocking in CI and the full forensic audit.

### Compatibility

- PHASE-004C changes maintained operational tooling only; it does not add a database migration, application route, authorization/UI/mail-flow behavior, installer behavior, deployment-template rewrite, DNS/TLS change, or automatic host-configuration migration.
- `v1.3.0-rc.4` and its published source identity remain immutable; `1.3.0-rc.5` is the next development-candidate version and is not yet a published release.

## Unreleased — MailStack repository bootstrap

### Changed

- Implemented PHASE-002 shared UI foundation and application shell with frozen design tokens, responsive authenticated navigation, an isolated sign-in shell, local SVG brand/icon assets, accessible focus handling, and preserved page business logic.
- Added dependency-free UI foundation contract tests, Django shell functional tests, CI enforcement, forensic-audit integration, and synchronized user/design documentation.
- Hardened cross-platform verification by deterministically closing contact-service SQLite connections, limiting POSIX permission assertions to POSIX runtimes, extending Ruff/Bandit coverage to the standalone contact service, and canonicalizing source-release ZIP host metadata and storage so Windows and Linux produce byte-identical archives.
- Imported and verified the complete 25-image MailStack UI and logo reference archive as `MAILSTACK-UI-DESIGN-INTAKE-001`.
- Frozen `MAILSTACK-UI-FOUNDATION-001` with screen classification, component, responsive, accessibility, future-roadmap, and implementation-status specifications.
- Added immutable design-asset hashing, PNG integrity validation, deterministic manifest synchronization, contract tests, CI gates, and forensic-audit integration.
- Made deterministic source packaging independent of host ZIP metadata and zlib implementation by using canonical POSIX metadata, fixed timestamps, empty optional metadata, and stored entries for every release member.
- Adopted **MailStack** as the public open-source project name.
- Set `https://github.com/vibtools/MailStack` as the canonical repository.
- Rebuilt the root README with SEO-oriented positioning for a self-hosted mail server and shared team inbox.
- Updated public documentation, citation metadata, notices, badges, support links, and private security advisory routing.
- Added the MailStack product logo and Vib Tools-aligned branding guidance.
- Changed deterministic source release archive branding to `mailstack-<version>-source.zip`.
- Added a compatibility-safe repository bootstrap, first-commit guidance, and GitHub metadata/topics specification.
- Removed the stale root `SOURCE_MANIFEST.sha256`; verified release archives continue to generate their own manifest.
- Made forensic inventory and source-release ordering deterministic across Windows and Linux by sorting canonical POSIX repository-relative paths.
- Upgraded the pinned Django LTS runtime from 5.2.15 to 5.2.16 to resolve the July 2026 Django security advisories and kept exact-version deployment verification aligned.
- Established `MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001` as the protected feature and documentation baseline.
- Added the root `documents/` user-documentation hub with a user manual, task-based how-to guide, administrator guide, baseline record and mandatory phase history.
- Added deterministic documentation index and manifest synchronization, phase scaffolding, contract tests and CI policy enforcement so maintained feature changes cannot merge without the required user documentation and changelog updates.
- Corrected the RC4 Windows audit harness so Git Bash maps installer-only `python3` calls to the exact Python interpreter running the local test process, without changing the Ubuntu production installer or requiring a machine-wide Windows alias.

### Compatibility

- Preserved `VIBMAIL_*` environment variables, `vibmail-*` service names, `/etc/vibmail` paths, database identifiers, source directories, and legacy deployment contracts.
- No application behavior, database migration operations, mail-flow, authentication, authorization, or deployment contract was intentionally changed. Legacy protocol headers such as `X-VibMail-CSRF` remain unchanged.

## 1.3.0-rc.3 — 2026-08-17

### Security

- Upgraded the locked transitive `sqlparse` runtime from 0.5.5 to 0.6.0 after GitHub Actions run `32053931714` identified CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and CVE-2026-54284.
- Kept Django at 5.2.16; its declared `sqlparse>=0.3.1` dependency accepts sqlparse 0.6.0, and MailStack's Python 3.12 runtime satisfies sqlparse 0.6.0's Python 3.10+ requirement.
- Preserved all PHASE-003 installation, recovery, LMTP, ingestion, UI, route, schema, and deployment behavior; this maintenance delta changes only the vulnerable dependency pin plus required release metadata and verification records.

### CI

- Corrected RC2 qualification records that could be read as if the current PHASE-003 dependency audit had passed. The RC2 branch passed structural/documentation/installer/operations gates but stopped at the blocking online advisory gate.
- Regenerated deterministic documentation, design, and forensic inventories for RC3. Full dependency-backed GitHub Actions requalification remains mandatory before merge or release.

## 1.3.0-rc.2 — 2026-08-17

### Fixed

- Prevented the installer from changing the host-wide `/var/log` mode and added explicit least-privilege log-path checks.
- Isolated installer-launched Django management commands from stale parent-shell database and Django environment variables.
- Prepared the mailbox provisioning runtime lock directory before clean/repair bootstrap commands.
- Made reviewed repair resumable with explicit idempotent initial-administrator and system-mailbox preservation while retaining strict duplicate rejection by default.
- Persisted root-only initial administrator credentials immediately after administrator creation so later installer failures do not lose the generated password.
- Fixed Postfix-to-Dovecot LMTP delivery by configuring the static userdb with `allow_all_users=yes` while preserving Postfix SQL recipient validation.
- Allowed official one-shot dry-run ingestion verification to run beside the live ingestion worker without taking the exclusive worker lock or mutating ServiceHeartbeat state.
- Qualified the two conservative MariaDB uniqueness warnings against the existing `utf8mb4_unicode_ci` and unique-column deployment contract without changing schema or migrations.

### Operations

- Added SSH session-resilience guidance and a non-blocking installer warning when a mutating run starts outside `tmux`/`screen`.
- Synchronized the live-staging fixes back into the canonical source so fresh deployments require no manual copies of the acceptance hotfixes.

## 1.3.0-rc.1 — 2026-06-30

### Preserved

- All approved mailbox, ingestion, access-control, live-update, audit, public-site and contact-service behavior
- Existing migrations, URLs, templates, static assets and legacy `vibmail.my` deployment compatibility

### Added

- Configurable Ubuntu 24.04 one-command installer
- MariaDB, Postfix, Dovecot, Nginx, systemd and environment templates
- Root open-source governance and security documents
- Complete AGPL-3.0 license text
- GitHub CI, Dependabot configuration, issue templates and release-artifact workflow
- SEO-oriented README, repository metadata, roadmap, FAQ, troubleshooting, build, maintenance, API and dependency documentation
- Source, template, installer, operations, documentation and release verification gates
- Deterministic source archive, manifest and checksum generation
- Vib Tools publisher and ecosystem references

### Fixed and hardened

- Fixed-domain production coupling was generalized while retaining legacy defaults
- Production settings now fail closed on unsafe hosts, paths, origins, secrets and SQL identifiers
- Database grants, Postfix lookup access, LMTP identity and systemd confinement were tightened
- Backup/restore compatibility, validation and exact service-state restoration were strengthened
- Repository audits now ignore supported local audit environments while still blocking generated artifacts from release archives

### Qualification

Repository CI, the online dependency advisory audit, deterministic release build, release verification and clean-clone verification pass. Stable promotion remains blocked on a clean Ubuntu 24.04 VPS acceptance campaign, external SMTP/LMTP verification, backup/restore acceptance and release-owner legal confirmation.
