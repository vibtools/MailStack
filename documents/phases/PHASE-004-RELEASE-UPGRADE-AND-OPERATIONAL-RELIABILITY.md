---
document_id: phase-004-release-upgrade-and-operational-reliability
title: Release, Upgrade and Operational Reliability
document_type: phase
audience: users-operators-and-maintainers
status: active
version: 1.3.0-rc.5
last_reviewed: 2026-08-17
phase_id: PHASE-004
---

# PHASE-004: Release, upgrade and operational reliability

## Objective

Make post-RC4 release handling, upgrades, rollback, and operational acceptance reproducible without
weakening the receive-only architecture or disturbing an already working MailStack deployment.
PHASE-004A finalized the forensic/documentation baseline. PHASE-004B adds fail-closed automatic
tag-to-GitHub-Release publication while keeping upgrade/runtime changes for later approved subphases.

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

Later approved PHASE-004 subphases may address a controlled existing-server upgrade/rollback
mechanism and operational backup/restore and reboot acceptance. Those runtime changes are not
implemented by PHASE-004A or PHASE-004B.

## User-facing changes

There is no application UI or mailbox behavior change in PHASE-004A or PHASE-004B. Maintainers and
operators gain a single explicit official source baseline for RC4, corrected RC4 qualification
evidence, and a tag-driven release workflow that removes the need to upload deterministic release
assets manually from a workstation.

## How to use

Treat `mailstack-1.3.0-rc.4-source.zip`, SHA-256
`58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`, tag `v1.3.0-rc.4`, and commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56` as the immutable official source baseline. The working
repository version remains `1.3.0-rc.5`; do not retag or rewrite RC4. For future releases, merge the
release commit to `main`, require successful `main` CI, create the matching `v<version>` tag at the
current `main` head, and push the tag. The release workflow then builds/verifies the deterministic
source archive and publishes the GitHub Release automatically. `workflow_dispatch` validates and
builds artifacts but never publishes a release.

## Compatibility

PHASE-004A and PHASE-004B introduce no model, migration, URL, application permission, template, CSS,
JavaScript, mail-flow, ingestion, installer, deployment-template, service, database, DNS, TLS, or
existing-VPS change. PHASE-004B changes only repository release automation, audit tooling, focused
contract tests, and required documentation/manifests. The `v1.3.0-rc.4` tag and deterministic RC4
source archive remain unchanged. No data/configuration migration or VPS rollback is required.

## Verification

The RC4 evidence recorded by this phase is anchored to `main` CI run `32071701530`, tag CI run
`32072699991`, and release-artifact workflow `32072699830`. RC4 passed 198 tests with 95.00 percent
coverage, the dependency vulnerability audit, Ruff, Bandit, installer and operations contracts,
full forensic audit with zero blocking findings, deterministic source build, and release
verification.

PHASE-004A branch CI run `32087558399` passed all blocking gates, including 198 Django tests at
95.00 percent coverage, dependency audit, full forensic audit, deterministic RC5 source build, and
release verification.

PHASE-004B must pass its release-workflow contract tests, documentation/design/inventory gates,
installer/operations regression contracts, dependency/security/application CI, full forensic audit,
and deterministic release build/verification before merge. Actual publication is intentionally not
tested by creating a fake public tag/release; the first legitimate post-merge release tag is the
end-to-end publication acceptance event.

## Documentation impact

PHASE-004A updated the root/application changelogs, build/release examples, README status wording,
dependency/performance evidence, forensic/test reports, canonical baseline, UI implementation
status, active managed-document version metadata, generated manifests, and this phase record.
PHASE-004B updates the release workflow, release gate/contract tests, root changelog, release/build/
publishing documentation, release notes, forensic/test evidence, generated forensic/documentation
manifests, and this phase record. No application user workflow guide requires a behavioral change.
