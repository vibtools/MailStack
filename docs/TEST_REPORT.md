# Test report — MailStack 1.3.0 RC1

**Execution date:** 2026-06-30

## Application suite

```text
Collected: 189
Passed: 189
Failed: 0
Coverage: 94.99%
Required coverage: 85%
```

Covered areas include authentication, user management, mailbox membership isolation, mailbox lifecycle, Postfix contract behavior, Maildir provisioning/ingestion, MIME parsing, HTML sanitization, attachment storage and authorization, duplicate handling, counters, live updates, reliability, security controls, and responsive routes.

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
| Deterministic ZIP/manifest/checksum verification | Required final release-build gate |
| Documentation and forensic inventory gates | PASS |

## Runtime qualification

Local tests executed with Python 3.13.5 because that is the available audit runtime. The package declares and CI enforces Python 3.12 for production. The CI job runs on Ubuntu 24.04 with Python 3.12.

## Dependency advisory qualification

The local online vulnerability query could not run because DNS access to the external package/advisory service was unavailable. The exact command is retained as a blocking CI step. A public release must not be promoted when that CI step fails.

## Manual acceptance still required

On an isolated Ubuntu 24.04 VPS, verify installation, TLS issuance/renewal, external SMTP reception, Postfix lookup rejection for unknown/disabled recipients, Dovecot LMTP delivery, Maildir ingestion, login and authorization isolation, live updates, safe HTML, attachment downloads, contact delivery, backup, restore, and restart recovery.
