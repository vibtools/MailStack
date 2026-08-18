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
PHASE-004A finalizes the forensic/documentation baseline before later PHASE-004 subphases change
release automation or upgrade tooling.

## Scope

PHASE-004A is restricted to forensic evidence finalization, baseline identity, version/release
metadata synchronization, this phase record, and deterministic documentation/design/forensic
manifests. It records the completed RC4 qualification using the successful `main`, tag-CI, and
release-artifact workflows and replaces stale pre-RC4-publish wording.

Later approved PHASE-004 subphases may address automatic tag-to-GitHub-Release publication, a
controlled existing-server upgrade/rollback mechanism, and operational backup/restore and reboot
acceptance. Those runtime/tooling changes are not implemented by PHASE-004A.

## User-facing changes

There is no application UI or mailbox behavior change in PHASE-004A. Maintainers and operators gain
a single explicit official source baseline for RC4 and corrected evidence that distinguishes
published RC4 qualification from the new RC5 development identity.

## How to use

Treat `mailstack-1.3.0-rc.4-source.zip`, SHA-256
`58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`, tag `v1.3.0-rc.4`, and commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56` as the immutable official source baseline. Start
PHASE-004 work from that source identity. The working repository version is `1.3.0-rc.5`; do not
retag or rewrite RC4.

## Compatibility

PHASE-004A introduces no model, migration, URL, permission, template, CSS, JavaScript, mail-flow,
ingestion, installer, deployment-template, service, database, DNS, TLS, or existing-VPS change.
The `v1.3.0-rc.4` tag and deterministic RC4 source archive remain unchanged. There is no data or
configuration migration and no rollback operation is required for this documentation-only delta.

## Verification

The RC4 evidence recorded by this phase is anchored to `main` CI run `32071701530`, tag CI run
`32072699991`, and release-artifact workflow `32072699830`. RC4 passed 198 tests with 95.00 percent
coverage, the dependency vulnerability audit, Ruff, Bandit, installer and operations contracts,
full forensic audit with zero blocking findings, deterministic source build, and release
verification.

PHASE-004A itself must pass documentation synchronization/tests, design-manifest integrity,
forensic-inventory regeneration/check, template validation, installer/operations regression
contracts, `git diff --check`, structural forensic audit, and final GitHub CI before it is considered
fully qualified.

## Documentation impact

This subphase updates the root and application changelogs, current build/release examples, README
status wording, dependency/performance evidence, forensic and test reports, the canonical baseline,
UI implementation-status evidence, active managed-document version metadata, generated
documentation/design/forensic manifests, and this PHASE-004 record. No user workflow guide requires
behavioral changes because application behavior is unchanged.
