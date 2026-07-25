# Test report — MailStack 1.3.0 RC1

**Baseline verification date:** 2026-07-25

## Application suite

```text
Collected: 196
Passed: 195
Skipped: 1 — Windows symbolic-link capability unavailable
Failed: 0
Coverage: 94.99%
Required coverage: 85%
```

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
| Locked dependency advisory audit | PASS — no known vulnerabilities found |
| Canonical stored-entry release packaging and ZIP metadata verification | PASS |

## Runtime qualification

GitHub Actions run `30133728843` completed successfully on Ubuntu 24.04 with Python 3.12 for source safety, documentation, dependency audit, Ruff, Bandit, tests and coverage, contact tests, Django checks, shell syntax, the full forensic gate, deterministic release build and release verification. The qualifying source commit is `1e1737edea2e6c922265a15d8584b56671820c65`.

## Dependency advisory qualification

The network-enabled blocking `pip-audit` gate passed in GitHub Actions after Django was upgraded to 5.2.16. Dependency changes remain subject to `pip check`, the locked requirements contract and the blocking online advisory gate.

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
