# Changelog

All notable repository-level changes are recorded here. Application history before the open-source conversion remains in `mailbox-app/CHANGELOG.md`.

## Unreleased — PHASE-006 reader integrity and repair

### Corrected

- Advanced the pinned Django 5.2 LTS runtime from 5.2.16 to 5.2.17 after RC2 `pip-audit` identified the upstream security advisory, and synchronized active dependency, deployment verification, and security-test contracts without changing application behavior.
- Renamed CSS parser token-kind locals to avoid Bandit B105 credential-name false positives; no Bandit rule, exclusion, sanitizer policy, or runtime behavior is weakened.
- Added the RC2 high-fidelity reader candidate: safe inline CSS and bounded sanitized `<style>`/responsive `@media` rules are preserved through an explicit allowlist while CSS URLs, imports, fonts, dynamic/custom-property functions, active positioning/effects and remote resources remain denied.
- Added deterministic CSS parsing with pinned `tinycss2==1.5.1` plus focused parser, repair, security and safe-reader regression fixtures/tests; no database, route, authorization, iframe/CSP, mail-flow or repair-architecture change is included.
- Prevented stripped HTML `<style>`/head/active blocks from leaking CSS text into the visible message body while preserving the deny-by-default sanitizer posture.
- Removed blocked remote image nodes so tracking/remote images do not leave broken-image residue in the protected reader.
- Removed the permanent protected-rendering banner from the normal reader while retaining sandbox, no-referrer, sanitizer, URL and active-content restrictions.
- Added a bounded, idempotent existing-message body repair path that re-parses verified Maildir source without delete/re-ingest behavior and preserves message identity/state/attachments.
- Disabled the unused Gunicorn control interface through source-level configuration rather than weakening systemd filesystem confinement.

### Verification state

- Local PHASE-006 focused qualification: 60 tests passed; targeted Ruff, Bandit, Django system check and migration-drift gates passed.
- PHASE-006 implementation commit `90175b7a4549cb67d874692081bd5b0484eddccc` passed GitHub Actions CI run `32183300485`.
- RC1 was squash-merged through PR #12 to `main` at `212ccaf7fab94e1b42ef2a57afb7bdfee673667e` and tagged `v1.3.4-rc.1`; controlled reader acceptance retained the security fix but found original HTML/CSS fidelity insufficient, opening the RC2 continuation.
- The combined RC2 implementation/dependency candidate passed local qualification with 223 tests passed and one Windows symbolic-link capability skip, 93.03% coverage, Ruff/Bandit/Django/migration/dependency/documentation/design/installer/operations/release/upgrade gates PASS, `pip-audit` reporting no known vulnerabilities, and standard/full forensic audits with zero blocking findings.
- Release identity is promoted to `1.3.4-rc.2` for repeat local qualification, branch/main CI, exact-main tag publication and controlled live acceptance; none of those post-promotion gates are claimed complete here.

### Compatibility

- No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization redesign, outbound feature, broad UI redesign, installer-flow change, reader-policy change, or application behavior change is introduced by the RC2 release-identity promotion.

## 1.3.3 — PHASE-005A qualification correction

### Corrected

- Synchronized the 1.3.3 release identity across VERSION, CI/release workflows, deterministic artifact paths, managed documentation, and release-workflow contract tests after the failed qualification run exposed stale 1.3.2 metadata.
- Removed the accidental empty repository-root `85%` file created when non-comment CMD guidance containing `>=85%` was interpreted as output redirection.
- Corrected PHASE-005A import-order lint findings and regenerated forensic/document metadata so source-safety and Ruff gates evaluate the intended source tree.
- Preserved live updates for browsers that still hold the previously immutable-cached `app.js`: the live endpoint accepts either the new explicit `X-MailStack-Live-Request: 1` header or the legacy `Accept: application/json` poll signature, while ordinary document navigation continues to redirect to the dashboard instead of exposing raw JSON.
- Replaced the prose-paste handoff with an executable Windows CMD script whose explanatory lines are `REM` comments and whose gates stop on failure.

### Compatibility

- No model, migration, parser/sanitizer, mailbox permission, ingestion, Postfix/Dovecot, Maildir, MariaDB, attachment, installer, deployment-template, backup/restore, or upgrade/rollback behavior changes.
- Published `v1.3.1` remains immutable official release provenance; `1.3.2` is retained only as failed development-qualification history and is not promoted as a release baseline.

## 1.3.2 — PHASE-005A development

### UI navigation reliability

- Hardened the authenticated live-update transport so `/messages/live/` returns JSON only to MailStack background polling requests carrying the explicit `X-MailStack-Live-Request: 1` header; ordinary authenticated document navigation redirects to the dashboard instead of rendering raw JSON.
- Preserved same-origin credentials, no-store responses, authorization filtering, bounded live payloads, polling backoff, notifications, and mailbox counter updates.

### Compact mailbox and unified reader

- Replaced the oversized mailbox header and generic message grid with a compact webmail-style inbox surface, integrated search/read/attachment filters, denser unread rows, message previews, attachment/size metadata, and responsive desktop/mobile behavior.
- Added preview text derived only from the existing indexed plain body or sanitized HTML text; no model, migration, parser, or persistence change is introduced.
- Removed the visible `Plain text` / `Safe HTML` tabs and replaced them with one message reader that automatically shows the existing sanitized HTML in the retained sandbox/no-referrer frame, or the indexed plain-text body when no HTML body exists.
- Compact sender/routing metadata, actions, warnings, and attachments into the unified reader while preserving mark-unread, deletion permissions, attachment authorization, sanitizer policy, CSP, and receive-only boundaries.

### Qualification and release metadata

- Added PHASE-005A regression coverage for direct live-endpoint navigation, background JSON polling, compact inbox rendering, HTML-derived previews, unified HTML rendering, and plain-only fallback.
- Synchronized the approved target identity to `1.3.2`, including CI deterministic-artifact verification and release-note file selection, without changing release-gate semantics.
- Froze published `v1.3.1` as `MAILSTACK-1.3.1-OFFICIAL-SOURCE-BASELINE-001`, anchored to commit `039a6e6eea6e198b4b15612db9d2f208b6305a16`, tree `9437ba2ebac2033a229accd190268b8711d5b26e`, and deterministic source SHA-256 `517778967ca491974f315d231dfd43b3dba85fe86b47dcfc63e4c7051d1010bd`.

## 1.3.1 — 2026-08-18

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

### Verification and CI correction

- Corrected the five PHASE-004C Ruff findings in `verify_upgrade_archive.py` without changing archive, migration, upgrade, rollback, service, or data semantics.
- Recorded GitHub Actions run `32097491341` as a failed qualification attempt: source safety, documentation, upgrade/rollback contracts, and dependency audit passed before Ruff stopped the workflow; downstream runtime/release gates were therefore not executed in that run.
- Marked the next source-baseline identity as `1.3.1`, synchronized deterministic build/release examples, and moved automated publication to version-matched `docs/RELEASE_NOTES_1.3.1.md`. The version mark is not itself a production-readiness or GitHub-release claim.

### Compatibility

- PHASE-004C changes maintained operational tooling only; it does not add a database migration, application route, authorization/UI/mail-flow behavior, installer behavior, deployment-template rewrite, DNS/TLS change, or automatic host-configuration migration.
- `v1.3.0-rc.4` remains immutable historical release provenance. `v1.3.1` is the current frozen published source/release baseline; PHASE-005A develops `1.3.2` from that exact source without rewriting either historical tag.

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
