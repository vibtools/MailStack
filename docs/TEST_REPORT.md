# Test report — MailStack 1.3.0 RC1

**Baseline verification date:** 2026-07-24

## Application suite

```text
Collected: 189
Passed: 189
Failed: 0
Coverage: 94.99%
Required coverage: 85%
```

Covered areas include authentication, user management, mailbox membership isolation, mailbox lifecycle, Postfix contract behavior, Maildir provisioning/ingestion, MIME parsing, HTML sanitization, attachment storage and authorization, duplicate handling, counters, live updates, reliability, security controls, responsive routes, deterministic user-document synchronization, draft blocking and feature-document policy enforcement.

## Additional automated gates

| Gate | Result |
|---|---|
| Ruff | PASS |
| Bandit with repository policy | PASS |
| Django system check (test settings) | PASS |
| Django production `check --deploy` | PASS |
| Migration drift | PASS — no changes detected |
| Contact service tests | PASS |
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
| Mixed stored/deflated deterministic release packaging | PASS |

## Runtime qualification

GitHub Actions run `30133728843` completed successfully on Ubuntu 24.04 with Python 3.12 for source safety, documentation, dependency audit, Ruff, Bandit, tests and coverage, contact tests, Django checks, shell syntax, the full forensic gate, deterministic release build and release verification. The qualifying source commit is `1e1737edea2e6c922265a15d8584b56671820c65`.

## Dependency advisory qualification

The network-enabled blocking `pip-audit` gate passed in GitHub Actions after Django was upgraded to 5.2.16. Dependency changes remain subject to `pip check`, the locked requirements contract and the blocking online advisory gate.

## Manual acceptance still required

On an isolated Ubuntu 24.04 VPS, verify installation, TLS issuance/renewal, external SMTP reception, Postfix lookup rejection for unknown/disabled recipients, Dovecot LMTP delivery, Maildir ingestion, login and authorization isolation, live updates, safe HTML, attachment downloads, contact delivery, backup, restore, and restart recovery.
