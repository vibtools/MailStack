# Changelog

All notable repository-level changes are recorded here. Application history before the open-source conversion remains in `mailbox-app/CHANGELOG.md`.

## Unreleased — MailStack repository bootstrap

### Changed

- Adopted **MailStack** as the public open-source project name.
- Set `https://github.com/vibtools/MailStack` as the canonical repository.
- Rebuilt the root README with SEO-oriented positioning for a self-hosted mail server and shared team inbox.
- Updated public documentation, citation metadata, notices, badges, support links, and private security advisory routing.
- Added the MailStack product logo and Vib Tools-aligned branding guidance.
- Changed deterministic source release archive branding to `mailstack-<version>-source.zip`.
- Added a compatibility-safe repository bootstrap, first-commit guidance, and GitHub metadata/topics specification.
- Removed the stale root `SOURCE_MANIFEST.sha256`; verified release archives continue to generate their own manifest.
- Upgraded the pinned Django LTS runtime from 5.2.15 to 5.2.16 to resolve the July 2026 Django security advisories and kept exact-version deployment verification aligned.

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

Automated gates pass. Stable promotion remains blocked on a clean Ubuntu 24.04 VPS acceptance campaign, external SMTP/LMTP verification, online dependency advisory audit and release-owner legal confirmation.
