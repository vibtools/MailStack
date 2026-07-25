## Summary

Describe the change and the operational problem it solves.

## Compatibility

- [ ] Existing mailbox, ingestion, access-control, audit, public-site, and contact-service behavior is preserved.
- [ ] Database and deployment compatibility were reviewed.
- [ ] Any intentional breaking change is explicitly approved and documented.

## Documentation baseline

- [ ] UI/design changes preserve original references and pass the design manifest and contract tests
- [ ] Planned or future-review controls remain inactive unless this PR contains the approved feature architecture
- [ ] A `documents/phases/PHASE-NNN-*.md` record was added or updated
- [ ] User-facing changes update `USER_MANUAL.md`, `HOW_TO_USE.md`, or `ADMIN_GUIDE.md`
- [ ] `CHANGELOG.md` was updated
- [ ] `python scripts/manage_documents.py check`
- [ ] `python scripts/test_documents.py`
- [ ] `python scripts/manage_designs.py --root . check`
- [ ] `python scripts/test_designs.py`
- [ ] `python scripts/test_ui_foundation.py`
- [ ] `python scripts/check_documentation_policy.py --base HEAD^ --head HEAD`

## Verification

- [ ] Tests added or updated
- [ ] `python scripts/forensic_audit.py --root . --full`
- [ ] `python scripts/validate_templates.py`
- [ ] `python scripts/test_installer.py`
- [ ] Dependency audit reviewed
- [ ] No secrets, production identifiers, user data, or generated artifacts added

## Security and operations

Describe authorization, input-validation, data-retention, performance, migration, backup, and rollback effects.
