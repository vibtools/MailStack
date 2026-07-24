# MailStack v1.2.1 Test Report

## Result

**Security-hotfix release verification: PASS**

- Automated tests: **187 passed**
- Application coverage: **94.99%**
- Exact local audit runtime: Python 3.13, Django 5.2.15, Bleach 6.4.0, python-dotenv 1.2.2
- Django system check: PASS
- Migration drift: PASS (`No changes detected`)
- Python compilation: PASS
- Ruff: PASS
- Bandit: PASS
- JavaScript syntax (`node --check`): PASS
- Shell syntax for all release scripts: PASS

## Added security-hotfix regression coverage

- Ordinary URLs remain linkified after sanitization.
- Email addresses are not converted into `mailto:` links.
- The only Bleach `Linker` call explicitly sets `parse_email=False`.
- Dependency lock files require Bleach 6.4.0 and python-dotenv 1.2.2.
- Preflight, deployment, and post-deployment scripts enforce exact security-sensitive versions.

## Production acceptance

The production host uses Python 3.12. The package retains the strict `>=3.12,<3.13` runtime contract. Final acceptance requires the online dependency audit and the controlled VPS preflight before installation.
