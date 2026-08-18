# Test report — MailStack 1.3.0 RC5 development baseline

**PHASE-004B verification date:** 2026-08-17
**Latest published release candidate:** `v1.3.0-rc.4`
**Repository development version:** `1.3.0-rc.5`

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
and required workflow protections. The assembled candidate passes all seven contracts locally. They
are blocking in the main CI workflow and are also invoked by the forensic audit. The structural
forensic audit passes with 407 files scanned, 146 Python files, 13 shell files, and zero blocking
findings. GitHub branch CI remains the final authority. No fake public tag/release is created for
testing.

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

The final assembled delta is additionally checked with `git diff --check` before handoff.
Dependency-backed GitHub CI remains the final authority for the RC5 development candidate. Until
that branch workflow passes, PHASE-004A is locally qualified only and `1.3.0-rc.5` must not be
published as a release candidate.

## Manual acceptance still outstanding before stable `1.3.0`

A future isolated Ubuntu 24.04 acceptance campaign must cover the exact-source clean install,
TLS/DNS/mail routing, unknown-recipient rejection, real inbound delivery, authorization isolation,
contact delivery, backup, restore, restart/reboot recovery, and final release-owner/legal review.
