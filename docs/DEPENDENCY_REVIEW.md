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
| WhiteNoise | 6.11.0 | MIT | Static-file fallback |

Transitive runtime versions are pinned in `mailbox-app/requirements/locked.txt`. Development tooling is pinned in `requirements/development.txt` and includes pytest, coverage, Ruff, Bandit and pip-audit.

## Compatibility assessment

The UI design-intake phase adds no runtime or development package dependency. PNG integrity,
hashing, manifest synchronization, and contract tests use the Python standard library.

No obvious conflict was identified between the declared direct dependency license families and `AGPL-3.0-or-later`. `mysqlclient` is GPL-2.0-or-later, permitting use of a later GPL version; AGPLv3 section 13 addresses combination with GPLv3-covered work. This is a technical inventory, not legal advice. The release owner must confirm copyright ownership and license compatibility before publication.

## Vulnerability review

`pip check` passes. Django is pinned to 5.2.16, the July 2026 security maintenance release for the 5.2 LTS line. The blocking network-enabled `pip-audit` gate passed in GitHub Actions run `30133728843` for commit `1e1737edea2e6c922265a15d8584b56671820c65` and remains mandatory for future changes.
