# Forensic audit report — MailStack 1.3.0 RC5 development baseline

**PHASE-004C audit date:** 2026-08-17
**Repository development version:** `1.3.0-rc.5`
**Latest published release candidate:** `v1.3.0-rc.4`
**Target runtime:** Ubuntu Server 24.04 LTS and CPython 3.12
**Current classification:** RC4 official baseline preserved; PHASE-004A/004B branch qualification passed; PHASE-004C locally source-qualified and pending GitHub requalification

## Executive disposition

| Gate | Status |
|---|---|
| Official RC4 source baseline identity | PASS |
| RC4 `main` CI run `32071701530` | PASS |
| RC4 tag CI run `32072699991` | PASS |
| RC4 release-artifact workflow `32072699830` | PASS |
| RC4 dependency vulnerability audit | PASS — no known vulnerabilities reported |
| RC4 Django application suite | PASS — 198 passed, 0 failed |
| RC4 application coverage | PASS — 95.00%, minimum 85% |
| RC4 Ruff and Bandit | PASS |
| RC4 Django checks and migration drift | PASS |
| RC4 contact-service tests, Ruff, and Bandit | PASS |
| RC4 installer and operations contracts | PASS |
| RC4 full forensic audit | PASS — zero blocking findings |
| RC4 deterministic release build and verification | PASS |
| RC4 deterministic source SHA-256 | `58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac` |
| PHASE-003 staging external SMTP/LMTP path | PASS after accepted fixes |
| Exact RC4 clean-host reinstall | DEFERRED until a fresh VPS is available |
| Real backup/restore acceptance | PENDING |
| Restart/reboot recovery acceptance | PENDING |
| Final ownership/license review | PENDING release owner |
| PHASE-004A structural/local repository gates | PASS |
| PHASE-004A branch GitHub CI run `32087558399` | PASS |
| PHASE-004B release automation contracts | PASS locally — 7 focused contracts |
| PHASE-004B structural forensic audit | PASS locally — 407 files, 146 Python, 13 shell, zero blocking findings |
| PHASE-004B GitHub branch CI run `32093468669` | PASS — exact commit `ee90764335f8724727cea86e0af035c049c79e62` |
| PHASE-004C upgrade/archive/rollback contracts | PASS locally |
| PHASE-004C structural forensic audit | PASS locally — 411 files, 148 Python, 15 shell, zero blocking findings |
| PHASE-004C live existing-server upgrade | NOT EXECUTED — reserved for PHASE-004D |
| PHASE-004C GitHub branch CI | PENDING after delta apply/push |

**OFFICIAL_RC4_SOURCE_BASELINE:** PASS
**RC4_OPEN_SOURCE_RELEASE_CANDIDATE:** PASS
**PHASE_004A_REMOTE_QUALIFICATION:** PASS — branch CI `32087558399`
**PHASE_004B_LOCAL_QUALIFICATION:** PASS
**PHASE_004B_REMOTE_QUALIFICATION:** PASS — branch CI `32093468669`
**PHASE_004C_LOCAL_QUALIFICATION:** PASS
**PHASE_004C_REMOTE_QUALIFICATION:** PENDING GITHUB CI
**RC5_DEVELOPMENT_REQUALIFICATION:** PENDING PHASE-004C GITHUB CI
**STABLE_PRODUCTION_ACCEPTANCE:** PENDING

## Official RC4 baseline identity

The official frozen source baseline is `MAILSTACK-1.3.0-RC4-OFFICIAL-SOURCE-BASELINE-001`:

- release: `1.3.0-rc.4`
- tag: `v1.3.0-rc.4`
- commit: `896dbcc2ed1f38d9c618bf0b712efe5923f92e56`
- Git tree: `0d845b3d975949894c24581e6834aff7b33c30b4`
- deterministic archive: `mailstack-1.3.0-rc.4-source.zip`
- archive SHA-256: `58f06adea7c813e9861799d20e392441367bf64f6513d6e0634455d2011d4eac`
- verified archive members: 405
- verified manifest members: 404

The prior `MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001` remains historical documentation provenance; it is
not the current canonical source anchor.

## RC4 authoritative automated evidence

The post-merge `main` workflow run `32071701530` completed successfully at commit
`896dbcc2ed1f38d9c618bf0b712efe5923f92e56`. Its blocking quality-and-security job passed source
safety, documentation and design integrity, shared UI contracts, forensic inventory, deployment
templates, installer contracts, operations contracts, dependency vulnerability audit, Ruff,
Bandit, Django tests and coverage, contact-service tests/lint/security checks, Django checks, shell
syntax, full forensic audit, deterministic release build, and release verification.

The release tag triggered two further authoritative workflows on the same source commit:

- tag CI run `32072699991`: **PASS**
- release-artifact workflow `32072699830`: **PASS**

The release-artifact workflow used Ubuntu 24.04 and Python 3.12, reran the full forensic gate, built
the deterministic source archive, verified the checksum/manifest, and uploaded the verified GitHub
Actions artifact.

## RC4 test and coverage result

The authoritative released-RC4 application suite collected and passed 198 tests with zero failures.
Total application coverage was 95.00 percent against the repository's 85 percent minimum. The
network-enabled dependency advisory audit reported no known vulnerabilities for the locked RC4
runtime, including `sqlparse==0.6.0`.

Historical PHASE-002 local Windows evidence of 195 passed tests, one capability-based symbolic-link
skip, and 94.99 percent coverage remains valid as historical evidence only; it is no longer the
current release-qualification result.

## Architecture and feature preservation

The audited baseline preserves:

- administrator and ordinary-user authentication;
- administrator-managed user lifecycle;
- object-scoped mailbox memberships;
- mailbox create, enable, disable, and soft-delete behavior;
- reserved postmaster/abuse handling;
- receive-only Postfix virtual-recipient validation;
- Dovecot LMTP delivery to Maildir;
- durable Maildir ingestion, duplicate protection, and restart safety;
- MIME parsing, sanitized HTML, and protected attachment authorization;
- search, pagination, counters, read/unread state, and live inbox updates;
- security audit logging and readiness/health routes;
- public website and isolated contact workflow;
- backup/restore/rollback tooling and legacy `vibmail.my` compatibility.

No SMTP submission, IMAP, POP3, public registration, outbound reply/forward/send, campaigns, or
multi-node operation is introduced.

## PHASE-003 reliability evidence

PHASE-003 corrected the reproduced installer and inbound-delivery defects without adding a database
migration or changing application product scope. The accepted source includes protection of the
host-wide `/var/log` mode, sanitized least-privilege installer execution, provisioning lock-path
preparation, explicit repair preservation, early root-only initial-admin credential persistence,
Dovecot static-userdb `allow_all_users=yes` for Postfix-validated recipients, live-safe one-shot
Maildir verification, narrow production MariaDB warning qualification, and SSH session-resilience
guidance.

The staging campaign demonstrated real Gmail delivery through Postfix and Dovecot LMTP into Maildir,
queue drain, ingestion, and web-inbox visibility after the accepted fixes. The exact final RC4
archive was not reinstalled on a new clean host before publication; that clean-host acceptance is
explicitly deferred rather than being claimed.

## PHASE-004A audit boundary

PHASE-004A starts the repository development identity `1.3.0-rc.5` and is documentation/metadata
only. It finalizes RC4 evidence, establishes the official RC4 source baseline, adds the PHASE-004
record, synchronizes active managed-document version metadata, updates current build/release examples,
and regenerates deterministic documentation/design/forensic manifests.

PHASE-004A does not change application runtime logic, models, migrations, URLs, authorization,
templates, CSS, JavaScript, mail flow, ingestion behavior, installer behavior, deployment templates,
service definitions, database schema, DNS/TLS configuration, or the existing VPS.

## PHASE-004B release automation boundary

PHASE-004B changes repository release automation only. It adds a fail-closed Python release gate and
focused contract tests, updates CI/full-forensic enforcement, and splits tag handling into a read-only
verified-build job plus a tag-only publication job with `actions: read` and `contents: write`.
Publication requires matching VERSION/package/tag identity, the exact current `main` head, successful
`main` push CI for the tagged SHA, and proof that no release already exists. Deterministic ZIP/SHA
assets are published without `--clobber` or release editing. Manual dispatch remains build-only.
GitHub branch CI run `32093468669` passed this boundary on exact commit
`ee90764335f8724727cea86e0af035c049c79e62`, including 198 application tests at 95.00 percent coverage,
seven release-workflow contracts, zero-blocking full forensic audit, and deterministic source
build/verification with SHA-256 `fdfff6c1e4ec409d950e3d612be1feab1ac7987f8d436c3ef3c0fc6ee1865bb5`.

## PHASE-004C existing-server upgrade/rollback boundary

PHASE-004C adds operational source/runtime tooling without changing Django application behavior,
schema, Postfix/Dovecot routing, deployment templates, DNS, TLS, or the existing VPS. The generic
upgrader requires both deterministic release assets, validates canonical ZIP/source-manifest and
version identity, rejects same/downgrade and migration-history rewrites, acquires a runtime lock,
creates a source snapshot plus the maintained consistent data backup before mutation, stages source
outside the live tree, converges application/public-site dependencies, and runs post-upgrade
verification. New migration files require explicit acknowledgement.

After the pre-upgrade consistent backup returns, the source mutation window stops Gunicorn, ingestion,
and the contact worker while leaving Postfix and Dovecot active so accepted messages can accumulate
in Maildir. For a no-new-migration target, source/runtime failure recovery can restore the prior app
and public-site pointer. Once a migration-capable upgrade begins schema mutation, automatic source or
database rollback is refused; the coordinated backup/snapshot are reported for reviewed reconciliation.
The standalone rollback command never restores MariaDB or Maildir implicitly.

The PHASE-004C local structural audit passed 411 files, 148 Python files, 15 shell files, zero blocking
findings, and the focused upgrade/archive/rollback contract suite. No live VPS upgrade is claimed;
PHASE-004D is the real existing-server acceptance boundary. GitHub CI requalification remains pending
after the PHASE-004C delta is applied and pushed.

## Security review

The RC4 source remains pinned to Django 5.2.16, Python 3.12, and `sqlparse==0.6.0`. The blocking
online `pip-audit` gate passed after RC3 replaced the vulnerable `sqlparse==0.5.5` pin. No advisory
suppression was added for those findings. Existing security boundaries remain: Argon2 password
hashing, CSRF and secure-cookie controls, login throttling, object-level mailbox authorization,
sanitized HTML, protected attachments, receive-only SMTP, no public registration, MariaDB least
privilege, systemd confinement, archive safety, checksum verification, and fail-closed release gates.

## External acceptance gates before stable promotion

1. Preserve a passing GitHub CI baseline for every subsequent release commit.
2. Perform an exact-source clean installation on an isolated Ubuntu Server 24.04 VPS when a fresh
   test host is available.
3. Validate DNS/MX/PTR/rDNS/TLS/firewall and unknown-recipient rejection on that clean host.
4. Perform a real backup/restore acceptance exercise with data-integrity verification.
5. Verify restart/reboot recovery of MariaDB, Postfix, Dovecot, Gunicorn, ingestion, Nginx, and the
   contact service.
6. Confirm copyright ownership and third-party license compatibility.
7. Obtain final release-owner acceptance before promoting `1.3.0` stable.

## Final disposition

The published `v1.3.0-rc.4` source is a qualified release candidate and is the official frozen source
baseline for PHASE-004. PHASE-004A corrects the documentation evidence around that baseline but does
not retroactively modify or retag RC4. The working repository version `1.3.0-rc.5` remains a development candidate. PHASE-004B branch CI
has passed, while PHASE-004C still requires dependency-backed GitHub CI and no live upgrade is claimed
until the separately approved PHASE-004D acceptance campaign.
