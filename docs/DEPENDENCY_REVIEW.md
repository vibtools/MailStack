# Dependency review

## Runtime Python dependencies

| Package | Version | Primary license family | Purpose |
|---|---:|---|---|
| Django | 5.2.16 | BSD-3-Clause | Web framework |
| argon2-cffi | 25.1.0 | MIT | Password hashing support |
| bleach | 6.4.0 | Apache-2.0 | HTML sanitization |
| filelock | 3.20.3 | Unlicense | Cross-process locking |
| gunicorn | 25.1.0 | MIT | WSGI server |
| mysqlclient | 2.2.7 | GPL-2.0-or-later | MariaDB/MySQL adapter |
| python-dotenv | 1.2.2 | BSD-3-Clause | Environment loading |
| sqlparse | 0.6.0 | BSD-3-Clause | Django SQL parsing dependency |
| WhiteNoise | 6.11.0 | MIT | Static-file fallback |

Transitive runtime versions are pinned in `mailbox-app/requirements/locked.txt`. Development tooling is pinned in `requirements/development.txt` and includes pytest, coverage, Ruff, Bandit and pip-audit.

## Compatibility assessment

The UI design-intake phase adds no runtime or development package dependency. PNG integrity,
hashing, manifest synchronization, and contract tests use the Python standard library.

No obvious conflict was identified between the declared direct dependency license families and `AGPL-3.0-or-later`. `mysqlclient` is GPL-2.0-or-later, permitting use of a later GPL version; AGPLv3 section 13 addresses combination with GPLv3-covered work. This is a technical inventory, not legal advice. The release owner must confirm copyright ownership and license compatibility before publication.

## Vulnerability review

Django remains pinned to 5.2.16, the July 2026 security maintenance release for the 5.2 LTS line.
GitHub Actions run `32053931714` on PHASE-003 RC2 passed the structural and repository gates but the
blocking `pip-audit` step found CVE-2026-71491, CVE-2026-59894, CVE-2026-59893, and CVE-2026-54284
in `sqlparse==0.5.5`. RC3 introduced and RC4 preserves `sqlparse==0.6.0`, the upstream security release fixing those findings.
Django 5.2.16 permits `sqlparse>=0.3.1`, and sqlparse 0.6.0 supports Python 3.10+, including
MailStack's required Python 3.12 runtime. RC4 subsequently passed `pip check` and the blocking
network-enabled `pip-audit` gate in the qualified branch/main/tag workflows with no known
vulnerabilities reported. The same gates remain mandatory for RC5 and later changes; no advisory is
ignored or suppressed.
