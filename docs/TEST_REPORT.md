# Test report — MailStack 1.3.0 RC3

**PHASE-003 verification date:** 2026-08-17

## Last completed dependency-backed application suite (pre-RC3)

```text
Collected: 196
Passed: 195
Skipped: 1 — Windows symbolic-link capability unavailable
Failed: 0
Coverage: 94.99%
Required coverage: 85%
```

RC3 adds one focused deployment-security regression contract that requires both
`requirements/locked.txt` and `requirements/constraints.txt` to pin `sqlparse==0.6.0` and reject
the vulnerable 0.5.5 pin. The full RC3 collection/pass count is intentionally not claimed until the
dependency-backed GitHub Actions rerun completes.

Covered areas include authentication, user management, mailbox membership isolation, mailbox lifecycle, Postfix contract behavior, Maildir provisioning/ingestion, MIME parsing, HTML sanitization, attachment storage and authorization, duplicate handling, counters, live updates, reliability, security controls, responsive routes, deterministic user-document synchronization, draft blocking and feature-document policy enforcement.

## Additional automated gates

| Gate | Result |
|---|---|
| Mailbox application Ruff | PASS |
| Mailbox application Bandit with repository policy | PASS |
| Django system check (test settings) | PASS |
| Django production `check --deploy` | PASS |
| Migration drift | PASS — no changes detected |
| Contact service tests | PASS — deterministic SQLite close and temporary-file cleanup verified |
| Python compileall | PASS |
| Shell `bash -n` for all shell scripts | PASS |
| Deployment templates | PASS — 13 rendered |
| Installer contract | PASS — 2 valid, 9 invalid plans |
| Backup/restore/health contract | PASS |
| Nginx final configuration syntax | PASS |
| Nginx bootstrap configuration syntax | PASS |
| systemd unit syntax | PASS |
| `pip check` | PASS |
| Source safety scan | PASS after generated files are removed |
| Deterministic ZIP/manifest/checksum verification | PASS in GitHub CI |
| Documentation and forensic inventory gates | PASS |
| User-document synchronization and manifest gate | PASS |
| Documentation change-policy contract tests | PASS |
| UI design manifest synchronization and PNG integrity gate | PASS |
| UI design contract tests | PASS |
| Shared UI foundation dependency-free contracts | PASS — 8 tests |
| Shared shell Django functional tests | PASS — 7 focused tests |
| Standalone contact-service Ruff/Bandit | Enforced by the final verifier, full forensic gate, and CI |
| Locked dependency advisory audit | PENDING RC4 requalification — RC2 run `32053931714` found four sqlparse 0.5.5 vulnerabilities; RC3/RC4 pin 0.6.0 |
| Canonical stored-entry release packaging and ZIP metadata verification | PASS |

## Runtime qualification

The last fully completed pre-PHASE-003 dependency-backed qualification remains GitHub Actions run
`30133728843` on Ubuntu 24.04 with Python 3.12 at commit
`1e1737edea2e6c922265a15d8584b56671820c65`. That historical evidence does not qualify RC4.

For the PHASE-003 branch, GitHub Actions run `32053931714` at commit
`7a800eb9f0b6d0e3fa347f4d7f05b5ad88a5e18f` passed source safety, documentation, design,
forensic inventory, deployment-template, installer, and operations gates. It then failed at the
blocking dependency vulnerability audit, so Ruff, Bandit, Django tests/coverage, Django checks,
full forensic audit, and deterministic release steps were correctly skipped.

## Dependency advisory qualification

The failed RC2 `pip-audit` gate reported four vulnerabilities in `sqlparse==0.5.5`:
CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and CVE-2026-54284. Upstream sqlparse 0.6.0 is the
security release containing fixes for those issues. RC3 introduced and RC4 preserves `sqlparse==0.6.0` in both
`requirements/locked.txt` and `requirements/constraints.txt`. No advisory suppression is added.
RC4 must pass `pip check`, the network-enabled `pip-audit` gate, and every subsequent CI stage before
qualification.

## RC4 Windows Bash-runtime qualification

A Windows CMD run of the RC3 candidate passed documentation, managed-document, design, shared UI,
forensic inventory, deployment-template, and `git diff --check` gates. `test_installer.py`,
`test_operations.py`, and the shell portions of `forensic_audit.py` then failed before executing any
MailStack shell logic because the generic `bash` executable resolved to the WSL launcher. WSL failed
to attach Docker Desktop's `ext4.vhdx` with `E_ACCESSDENIED`. The forensic report's 16 findings were
therefore cascading manifestations of one local shell-runtime failure, not 16 independent source
defects.

RC4 centralizes Bash discovery in `scripts/shell_runtime.py`. Windows prefers a probed Git for
Windows Bash runtime, supports `BASH_EXECUTABLE`, and falls back only to candidates that pass a
non-mutating startup probe. Installer plans and shell syntax checks use repository-relative POSIX
paths so the same contracts remain valid on Linux and Git Bash. A follow-up Windows qualification
showed that Git Bash correctly launched but did not expose a `python3` command even though the host
provided `python`. The RC4 harness now supplies a process-local `BASH_ENV` bridge that maps
installer-only `python3` calls to the exact Python interpreter running the test process. The bridge
is regression-tested and does not alter the production installer, Ubuntu's native `python3` contract,
or the developer machine.

## PHASE-003 installation/recovery reliability qualification

Dependency-free local qualification for 1.3.0-rc.4 passes the documentation index/manifest gate,
documentation contract tests, design manifest and PNG integrity tests, shared UI foundation
contracts, deployment-template rendering, installer contracts, operations contracts, Python compile,
shell syntax, forensic inventory generation/check, and the structural forensic audit. The installer
contract specifically protects global `/var/log`, sanitized `vmail` command execution, provisioning
runtime directories, early credential persistence, explicit repair idempotency, the Dovecot static
userdb LMTP setting, and the existing MariaDB collation qualification.

The current artifact-building environment does not contain the repository's pinned Django/Ruff/Bandit
dependencies and cannot download them, so the dependency-backed Django/coverage/lint/full-forensic
gates are delegated to the mandatory Ubuntu 24.04 GitHub Actions run for the PHASE-003 commit. This
does not waive those gates.

The live staging campaign that motivated PHASE-003 demonstrated real external Gmail delivery through
Postfix and Dovecot LMTP into Maildir, queue drain after the static-userdb correction, ingestion, and
web-inbox visibility. A final clean installation from the exact RC4 source remains a release-candidate
acceptance requirement before stable promotion.

## Manual acceptance still required

On an isolated Ubuntu 24.04 VPS, verify installation, TLS issuance/renewal, external SMTP reception, Postfix lookup rejection for unknown/disabled recipients, Dovecot LMTP delivery, Maildir ingestion, login and authorization isolation, live updates, safe HTML, attachment downloads, contact delivery, backup, restore, and restart recovery.

## PHASE-002 qualification status

The shared shell passed eight dependency-free local contract tests covering required assets, frozen
tokens, responsive breakpoints, current-route-only navigation, template control-flow balance, SVG
integrity, preserved JavaScript runtime markers, and unsafe construct blocking. `node --check` also
passed for `mailbox-app/static/js/app.js`.

Seven focused Django shell tests passed. The complete local Django suite collected 196 tests: 195
passed and one symbolic-link test was skipped because the Windows test environment does not expose
the required capability. Coverage remained 94.99 percent. Ruff, Bandit, Django checks, migration
drift, contact-service behavior, dependency consistency, installer, operations, template, design,
documentation, and structural forensic gates passed in the recorded local workflow.

The Windows cleanup failure was traced to Python's SQLite connection context semantics: transaction
context exit did not close the file handle. `_connection()` now owns and closes the handle in a
`finally` block, and the contact test explicitly verifies the closed state. The POSIX `0700`
Maildir assertion now remains active only on POSIX runtimes. Standalone contact-service Ruff and
Bandit checks are included in both the final verifier and GitHub Actions so this analysis scope
cannot regress silently.

Final qualification still requires the PHASE-002 commit's GitHub Actions run. The last authoritative
pre-phase baseline remains GitHub Actions run `30165905840` at commit
`a4b5f40d85c0db1d278490af218f1a6040d40218`.
