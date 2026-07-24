## Summary

Describe the change and the operational problem it solves.

## Compatibility

- [ ] Existing mailbox, ingestion, access-control, audit, public-site, and contact-service behavior is preserved.
- [ ] Database and deployment compatibility were reviewed.
- [ ] Any intentional breaking change is explicitly approved and documented.

## Verification

- [ ] Tests added or updated
- [ ] `python scripts/forensic_audit.py --root . --full`
- [ ] `python scripts/validate_templates.py`
- [ ] `python scripts/test_installer.py`
- [ ] Dependency audit reviewed
- [ ] No secrets, production identifiers, user data, or generated artifacts added

## Security and operations

Describe authorization, input-validation, data-retention, performance, migration, backup, and rollback effects.
