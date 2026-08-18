---
document_id: phase-004-release-upgrade-and-operational-reliability
title: Release, Upgrade and Operational Reliability
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.1
last_reviewed: 2026-08-17
phase_id: PHASE-004
---

# PHASE-004: Release, upgrade and operational reliability

## Objective

Make post-RC4 release handling, upgrades, rollback, and operational acceptance reproducible without
weakening the receive-only architecture or disturbing an already working MailStack deployment.
PHASE-004A finalized the forensic/documentation baseline. PHASE-004B adds fail-closed automatic
tag-to-GitHub-Release publication. PHASE-004C adds the separately approved generic existing-server
source/runtime upgrade and rollback mechanism while leaving real VPS execution for PHASE-004D.

## Scope

PHASE-004A is restricted to forensic evidence finalization, baseline identity, version/release
metadata synchronization, this phase record, and deterministic documentation/design/forensic
manifests. It records the completed RC4 qualification using the successful `main`, tag-CI, and
release-artifact workflows and replaces stale pre-RC4-publish wording. Its branch CI run
`32087558399` passed on exact commit `586400e56b388873ecfcd8c67fc494a88dd73e31`.

PHASE-004B is restricted to release automation and its tests/documentation. A tag push must match
`VERSION` and the Python package version, point at the exact current `main` head, have a successful
`main` push CI run for that SHA, and have no existing GitHub Release for the tag. The verified build
job has read-only repository access. A separate tag-only publication job receives `actions: read` and
`contents: write`, downloads the verified workflow artifact, and creates the GitHub Release with the
deterministic ZIP and checksum. Manual workflow dispatch remains build/validation only.

PHASE-004C is restricted to the controlled existing-server upgrade/rollback mechanism, its
non-destructive contracts, and required documentation/forensic integration. The upgrader requires a
deterministic target source ZIP and matching SHA-256, verifies canonical archive/source-manifest and
version/package identity, rejects same-version/downgrade and migration-history rewrites, acquires a
non-blocking runtime lock, and creates both a source/runtime rollback snapshot and the maintained
consistent data backup before mutation. New migration files require explicit `--allow-migrations`
acknowledgement. After that backup completes, the application mutation window leaves Postfix and
Dovecot active while Gunicorn, ingestion, and the contact worker are stopped, allowing accepted mail
to accumulate in Maildir. Application/public-site source and Python dependencies are staged and
verified without rewriting host mail/web/TLS/systemd configuration.

For a no-new-migration target, a failure after mutation can automatically restore the prior
application/runtime source and public-site pointer. If a migration-capable upgrade fails after schema
mutation begins, automatic source/database rollback is refused and the tool reports the coordinated
data backup and source snapshot for reviewed reconciliation. The standalone rollback command never
restores MariaDB or Maildir implicitly and requires explicit forward-schema acknowledgement when its
snapshot records new migrations.

PHASE-004C does not execute this mechanism on the existing production/staging VPS. The first real
controlled existing-server upgrade is reserved for PHASE-004D. Backup/restore and reboot acceptance
remain later PHASE-004 operational gates.

## User-facing changes

There is no application UI or mailbox behavior change in PHASE-004A, PHASE-004B, or PHASE-004C.
Maintainers and operators gain a single explicit official source baseline for RC4, corrected RC4
qualification evidence, tag-driven release publication, and a reviewed source/runtime upgrade and
rollback tool that fails closed around archive integrity, migration risk, and recovery provenance.

## How to use

Treat `mailstack-1.3.0-rc.4-source.zip`, SHA-256
`58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`, tag `v1.3.0-rc.4`, and commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56` as the immutable official source baseline. The working
source-baseline version is `1.3.1`; do not retag or rewrite RC4, and do not publish `v1.3.1` until the
new main/CI and remaining release-acceptance gates pass. For future releases, merge the
release commit to `main`, require successful `main` CI, create the matching `v<version>` tag at the
current `main` head, and push the tag. The release workflow then builds/verifies the deterministic
source archive and publishes the GitHub Release automatically. `workflow_dispatch` validates and
builds artifacts but never publishes a release.

For an existing-server source/runtime upgrade, provide both published deterministic assets to
`/opt/vibmail/app/scripts/upgrade.sh`: `mailstack-X.Y.Z-source.zip` and its matching `.sha256`. The
target must be newer than the installed version. New migration files require explicit review and
`--allow-migrations`; modified or removed historical migration files are rejected. Successful runs
print the exact rollback snapshot and nested consistent-data-backup paths. See `docs/UPGRADE.md` for
the migration-aware rollback rules. PHASE-004D, not PHASE-004C, owns the first real VPS execution.

## Compatibility

PHASE-004A and PHASE-004B introduce no application/runtime change. PHASE-004C changes operational
source/runtime upgrade tooling only: it adds no application model or migration, URL, permission, UI,
mail-flow behavior, installer behavior, deployment-template rewrite, database schema change, DNS, TLS,
or live existing-VPS mutation. Postfix, Dovecot, Nginx, systemd, `/etc/vibmail`, certificates, Maildir,
and MariaDB data remain outside generic source replacement except for explicitly acknowledged future
Django migrations. The `v1.3.0-rc.4` tag and deterministic RC4 source archive remain unchanged.

## Verification

The RC4 evidence recorded by this phase is anchored to `main` CI run `32071701530`, tag CI run
`32072699991`, and release-artifact workflow `32072699830`. RC4 passed 198 tests with 95.00 percent
coverage, the dependency vulnerability audit, Ruff, Bandit, installer and operations contracts,
full forensic audit with zero blocking findings, deterministic source build, and release
verification.

PHASE-004A branch CI run `32087558399` passed all blocking gates, including 198 Django tests at
95.00 percent coverage, dependency audit, full forensic audit, deterministic RC5 source build, and
release verification.

PHASE-004B branch CI run `32093468669` passed on exact commit
`ee90764335f8724727cea86e0af035c049c79e62`, including seven release-workflow contracts, 198 Django
tests at 95.00 percent coverage, dependency/security gates, full forensic audit with zero blocking
findings, and deterministic source build/verification. Actual publication remains intentionally
reserved for a legitimate post-merge release tag rather than a fake public release.

PHASE-004C must pass its upgrade/archive/rollback contracts, existing installer/operations/release
contracts, documentation/design/inventory gates, dependency/security/application CI, full forensic
audit, and deterministic release build/verification. Its automated tests are non-destructive and do
not claim a real host upgrade; PHASE-004D is the live acceptance boundary.

## PHASE-004C CI correction and 1.3.1 baseline mark

GitHub Actions run `32097491341` tested exact PHASE-004C commit
`47e62bb6c0acd0216fb261f47f85959655b489e0`. All gates through the dependency vulnerability audit
passed, including the focused upgrade/archive/rollback contracts. Ruff then stopped the workflow on
four E501 line-length findings and one SIM102 nested-`if` finding in
`mailbox-app/scripts/verify_upgrade_archive.py`; downstream runtime and release gates were skipped.
The correction changes only formatting/control-expression layout needed for Ruff compliance and does
not change upgrade/archive/migration/rollback behavior.

At the owner's explicit request, the corrected source is version-marked `1.3.1` and the deterministic
build/release documentation is synchronized to that identity. This is a source-baseline freeze, not
a claim that the stable-looking version has passed the still-outstanding live PHASE-004D/operational
acceptance or has been published as a GitHub Release.

## Documentation impact

PHASE-004A updated the root/application changelogs, build/release examples, README status wording,
dependency/performance evidence, forensic/test reports, canonical baseline, UI implementation
status, active managed-document version metadata, generated manifests, and this phase record.
PHASE-004B updates the release workflow, release gate/contract tests, root changelog, release/build/
publishing documentation, release notes, forensic/test evidence, generated forensic/documentation
manifests, and this phase record. PHASE-004C updates operational upgrade/rollback scripts, a target
archive verifier, focused upgrade contracts, CI/full-forensic enforcement, upgrade/backup/operations
documentation, changelogs/release notes, forensic/test evidence, generated manifests/inventory, and
this phase record. No application UI/user workflow guide requires a behavioral change.
