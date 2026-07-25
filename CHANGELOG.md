# Changelog

All notable repository-level changes are recorded here. Application history before the open-source conversion remains in `mailbox-app/CHANGELOG.md`.

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

### Compatibility

- Preserved `VIBMAIL_*` environment variables, `vibmail-*` service names, `/etc/vibmail` paths, database identifiers, source directories, and legacy deployment contracts.
- No application behavior, database migration operations, mail-flow, authentication, authorization, or deployment contract was intentionally changed. Legacy protocol headers such as `X-VibMail-CSRF` remain unchanged.

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
