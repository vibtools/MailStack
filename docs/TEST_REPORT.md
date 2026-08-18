# Test report — MailStack 1.3.2 PHASE-005A development verification

**PHASE-005A verification date:** 2026-08-18
**Immutable published baseline:** `v1.3.1`
**Development target:** `1.3.2`

## Authoritative released-RC4 application suite

The final released-RC4 qualification ran on Ubuntu 24.04 with Python 3.12 at commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56`.

```text
Collected: 198
Passed: 198
Failed: 0
Coverage: 95.00%
Required coverage: 85%
```

The suite covers authentication, user management, mailbox membership isolation, mailbox lifecycle,
Postfix recipient contracts, Maildir provisioning/ingestion, MIME parsing, HTML sanitization,
attachment storage and authorization, duplicate handling, counters, live updates, reliability,
security controls, responsive routes, documentation synchronization, draft blocking, and feature
document policy enforcement.

## RC4 authoritative workflow evidence

| Workflow / gate | Result |
|---|---|
| Post-merge `main` CI run `32071701530` | PASS |
| Tag CI run `32072699991` | PASS |
| Release-artifact workflow `32072699830` | PASS |
| Source safety audit | PASS |
| Documentation and metadata validation | PASS |
| Managed user-document synchronization | PASS |
| Documentation system tests | PASS |
| UI design intake integrity | PASS |
| UI design tests | PASS |
| Shared UI foundation contracts | PASS |
| Feature documentation policy | PASS |
| Forensic file inventory | PASS |
| Deployment template validation | PASS |
| Installer contract | PASS — 2 valid, 9 invalid plans |
| Backup/restore/health operations contracts | PASS |
| Dependency vulnerability audit | PASS — no known vulnerabilities reported |
| Ruff | PASS |
| Bandit | PASS |
| Django application tests and coverage | PASS — 198 / 198, 95.00% |
| Contact service tests | PASS |
| Contact service Ruff | PASS |
| Contact service Bandit | PASS |
| Django system checks | PASS |
| Migration drift | PASS — no changes detected |
| Shell syntax | PASS |
| Full forensic gate | PASS — zero blocking findings |
| Deterministic release build | PASS |
| Release verification | PASS |

The deterministic RC4 release archive is `mailstack-1.3.0-rc.4-source.zip` with SHA-256
`58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`. Release verification reported
405 archive members and 404 manifest members.

## PHASE-004A branch CI closure

GitHub Actions run `32087558399` passed on exact commit
`586400e56b388873ecfcd8c67fc494a88dd73e31` using Ubuntu 24.04 and Python 3.12.13. The clean CI
environment installed the repository's exact development pins, reported no broken requirements or
known dependency vulnerabilities, passed all 198 Django tests at 95.00 percent coverage, and passed
all documentation, design, installer, operations, forensic, release-build, and release-verification
gates.

## PHASE-004B release automation qualification

PHASE-004B adds seven focused release-workflow contracts covering version normalization, RC/stable
classification, tag identity, manual-dispatch non-publication, package-version mismatch rejection,
successful-main-CI evidence matching, existing-release fail-close behavior, exact-main-head guarding,
and required workflow protections. GitHub branch CI run `32093468669` passed on exact commit
`ee90764335f8724727cea86e0af035c049c79e62` using Ubuntu 24.04 and Python 3.12.13. The run passed all
seven release-workflow contracts, the dependency vulnerability audit, Ruff/Bandit, all 198 Django
tests at 95.00 percent coverage, full forensic audit with 407 files/146 Python/13 shell files and zero
blocking findings, and deterministic RC5 source build/verification. The deterministic archive SHA-256
was `fdfff6c1e4ec409d950e3d612be1feab1ac7987f8d436c3ef3c0fc6ee1865bb5`. No fake public tag/release
was created for testing; legitimate post-merge tag publication remains the end-to-end release event.

## Dependency advisory qualification

The earlier RC2 run `32053931714` stopped at the blocking advisory audit because
`sqlparse==0.5.5` was reported for CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and
CVE-2026-54284. RC3 introduced and RC4 preserved `sqlparse==0.6.0` in the production lock and
constraints. RC4 then passed the online dependency audit with no known vulnerabilities reported.
No advisory suppression was added for those four findings.

## Historical Windows qualification context

Before final RC4 CI, Windows validation exposed two host-tooling issues rather than application
regressions: generic `bash` resolved to a failing WSL launcher, and Git Bash did not expose a
`python3` command even though the host Python was available as `python`. RC4 centralized probed Bash
runtime discovery and added a process-local Windows audit bridge mapping installer-only `python3`
invocations to the exact harness interpreter. The Ubuntu production installer and its native
`python3` contract were not changed.

The older PHASE-002 Windows dependency-backed suite recorded 195 passes, one capability-based
symbolic-link skip, and 94.99 percent coverage. Those figures remain historical local evidence; the
198-pass, 95.00-percent Ubuntu RC4 workflow is the current authoritative release result.

## PHASE-003 installation/recovery reliability qualification

Installer contracts protect the global `/var/log` mode, sanitized `vmail` command execution,
provisioning runtime directories, immediate credential persistence, explicit repair idempotency,
the Dovecot static-userdb LMTP setting, and narrow MariaDB warning qualification. Ingestion tests
protect exclusive locking for real workers while allowing one-shot dry-run verification beside the
live worker without heartbeat mutation.

The live staging campaign demonstrated real external Gmail delivery through Postfix and Dovecot
LMTP into Maildir, queue drain, ingestion, and browser visibility after the accepted source fixes.
An exact RC4 clean-host reinstall remains deferred until a fresh test VPS is available.

## PHASE-004A verification scope

PHASE-004A changes documentation, version/release metadata, and generated manifests only. The
assembled local candidate passed the following dependency-free/structural gates:

| PHASE-004A local gate | Result |
|---|---|
| Documentation validation | PASS — 46 required files, 59 local links checked |
| Managed-document synchronization/check | PASS — 17 documents, 5 phases |
| Documentation tests | PASS — 4 contracts |
| Design manifest integrity | PASS — 25 source images |
| Design tests | PASS — 4 contracts |
| Shared UI foundation contracts | PASS — 8 contracts |
| Deployment template validation | PASS — 13 templates |
| Installer contracts | PASS — 2 valid, 9 invalid plans |
| Operations contracts | PASS — 4 scripts |
| Forensic inventory check | PASS — 404 maintained entries |
| Structural forensic audit | PASS — 405 files scanned, 144 Python, 13 shell, zero blocking findings |

The final assembled PHASE-004A delta was additionally checked with `git diff --check`; its branch CI
closure is recorded above. The `1.3.0-rc.5` identity was the PHASE-004 development candidate at that
time; the current owner-requested source-baseline mark is `1.3.1`.

## PHASE-004C upgrade/rollback tooling qualification

PHASE-004C adds three maintained operational components: the generic `upgrade.sh` driver,
`rollback_upgrade.sh`, and `verify_upgrade_archive.py`, plus a focused non-destructive contract suite.
The local structural candidate passed deterministic archive/checksum fixture verification, canonical
source-manifest checks, version ordering, migration-delta detection, bad-checksum fail-close behavior,
Bash syntax checks, runtime-lock contracts, pre-mutation backup/rollback requirements, inbound-service
continuity assertions, and migration-aware rollback refusal.

| PHASE-004C local gate | Result |
|---|---|
| Upgrade/archive/rollback contracts | PASS |
| Documentation validation | PASS — 46 required files, 59 local links checked |
| Managed-document synchronization/check | PASS — 17 documents, 5 phases |
| Documentation tests | PASS — 4 contracts |
| Design manifest integrity | PASS — 25 source images |
| Design tests | PASS — 4 contracts |
| Shared UI foundation contracts | PASS — 8 contracts |
| Deployment template validation | PASS — 13 templates |
| Installer contracts | PASS — 2 valid, 9 invalid plans |
| Existing operations contracts | PASS — 4 scripts |
| Release-workflow contracts | PASS — 7 contracts |
| Forensic inventory | PASS — 410 maintained entries plus the inventory file |
| Structural forensic audit | PASS — 411 files, 148 Python, 15 shell, zero blocking findings |

PHASE-004C intentionally does not claim a live server upgrade. It changes operational tooling and
documentation, not Django application business logic or schema. Dependency/security/application
regression and the deterministic release build must still pass in the user's isolated Python 3.12
validation and GitHub CI after the delta is applied. PHASE-004D owns the first real existing-VPS
upgrade acceptance.

## PHASE-004C GitHub CI failure and scoped correction

GitHub Actions run `32097491341` executed exact PHASE-004C commit
`47e62bb6c0acd0216fb261f47f85959655b489e0`. The run passed setup, dependency installation, source
safety, documentation/design/UI contracts, documentation policy, forensic inventory, deployment
templates, installer/operations/release-workflow contracts, all PHASE-004C upgrade/rollback contracts,
and the dependency vulnerability audit. Ruff then reported exactly five findings, all in
`mailbox-app/scripts/verify_upgrade_archive.py`: four line-length findings and one nested-`if`
SIM102 finding. Because CI is fail-closed, Bandit, Django tests/coverage, contact tests, Django
checks, shell syntax, the full forensic gate, deterministic build, and release verification were
skipped in that run.

The `1.3.1` correction changes only the Ruff representation of those verifier statements plus the
version/release/baseline metadata required by the owner's explicit baseline mark. It does not change
the verifier's conditions, error semantics, archive validation, migration comparison, or extraction
logic. A new GitHub Actions run on the correction commit remains required before remote qualification
or release publication.

## Manual acceptance still outstanding before publishing `1.3.1` as production-ready

A future isolated Ubuntu 24.04 acceptance campaign must cover the exact-source clean install,
TLS/DNS/mail routing, unknown-recipient rejection, real inbound delivery, authorization isolation,
contact delivery, backup, restore, restart/reboot recovery, and final release-owner/legal review.
## PHASE-005A local verification

PHASE-005A adds focused Django regression tests for direct live-endpoint navigation, explicit background JSON polling, compact inbox preview rendering, unified sanitized-HTML selection, plain-only fallback, and HTML-derived live preview text. Existing live authorization, bounded-payload/query-count, search/filter/pagination, sandbox/no-referrer, XSS, attachment, mark-unread, delete-permission, and shared-shell tests remain in the suite.

Dependency-free/local gates completed as follows:

| PHASE-005A local gate | Result |
|---|---|
| Documentation validation | PASS — 46 required files, 60 local links |
| Managed-document synchronization | PASS — 18 documents, 6 phases |
| Documentation tests | PASS — 4 contracts |
| Design manifest integrity | PASS — 25 PNG references |
| Design tests | PASS — 4 contracts |
| Shared UI foundation | PASS — 8 contracts |
| JavaScript syntax | PASS |
| Python syntax for changed Python files | PASS |
| Deployment template validation | PASS — 13 templates |
| Installer contracts | PASS — 2 valid, 9 invalid |
| Operations contracts | PASS — 4 scripts |
| Release-workflow contracts | PASS — 7 contracts |
| Upgrade/archive/rollback contracts | PASS |
| Forensic inventory | PASS — 414 maintained entries plus inventory |
| Structural forensic audit | PASS — 415 files, 149 Python, 15 shell, zero blockers |
| Deterministic 1.3.2 build/verification | PASS before report synchronization; final SHA regenerated after documentation/inventory finalization |

The artifact environment does not contain supported CPython 3.12/Django/Ruff/Bandit dependencies and cannot reach the package index. Therefore the complete Django test/coverage, Ruff, Bandit, pip-audit, Django check/migration-drift, and full dependency-backed forensic gates are deliberately not claimed locally; they are mandatory in the user's isolated Python 3.12 environment and GitHub CI before merge/release.

## PHASE-005A live acceptance boundary

No existing-VPS mutation is performed by this patch. After 1.3.2 branch/PR/main/tag/release qualification, the existing server should be upgraded once using the PHASE-004 controlled upgrade mechanism, followed by browser acceptance of compact inbox/message rendering, direct-live-route redirect behavior, live polling, and preserved real inbound mail flow.
