# MailStack v1.2.1 Forensic Audit Report

## Release status

**PASS — security-hotfix release package ready for server-side dependency audit and controlled acceptance**

## Defects found and closed

1. v1.2.0 dependency audit found Bleach 6.3.0 sanitizer vulnerabilities.
2. v1.2.0 dependency audit found python-dotenv 1.2.1 symlink-handling vulnerability.
3. Bleach email-linkification advisory scope was previously implicit; v1.2.1 explicitly sets `parse_email=False`.
4. Dependency audit now validates the exact Linker AST before allowing the narrowly scoped advisory exception.
5. Preflight previously checked only Django; it now also checks Bleach and python-dotenv pins.
6. Deployment and post-deployment verification now confirm all three exact installed versions.
7. Operational scripts, reports, documentation, release identity, manifest, and hashes were rebuilt as v1.2.1.

All v1.2.0 feature-set fixes remain preserved, including authorization, mailbox memberships, IDOR prevention, concurrency locking, live inbox, notification deduplication, auto-read, mark-unread correction, click-to-copy, Nginx hotfixes, rollback hardening, and production-settings enforcement.

## Verification summary

- 187 automated tests: PASS
- 94.99% application coverage: PASS
- Ruff: PASS
- Bandit: PASS
- Django check: PASS
- Migration drift: PASS
- Python compilation: PASS
- JavaScript syntax: PASS
- Shell syntax: PASS

## Data-preservation conclusion

The hotfix changes application dependencies, release enforcement, tests, and documentation. Existing mailbox rows, Maildir paths, messages, attachments, Postfix/Dovecot schema, and receive-only flow remain unchanged.
