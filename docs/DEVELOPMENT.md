# Development guide

## Supported runtime

The production target is CPython 3.12 on Ubuntu Server 24.04 LTS. The application test configuration uses SQLite; production uses MariaDB and the external mail-schema contract.

## Local setup

```bash
cd mailbox-app
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements/development.txt
python manage.py migrate --settings=config.settings.test
pytest --cov=apps --cov-report=term-missing --cov-fail-under=85
ruff check .
bandit -c .bandit -q -r apps config
```

From the repository root also run:

```bash
python scripts/validate_templates.py
python scripts/test_installer.py
python scripts/forensic_audit.py --root . --full
```

Never use production databases, Maildir content, credentials, certificates, or personal addresses as test fixtures.
