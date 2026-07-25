# Contributing to MailStack

MailStack welcomes focused, tested and backward-compatible contributions.

## Non-negotiable preservation rule

- Do not remove, disable or silently simplify an existing feature.
- Do not rewrite migration history.
- Do not change mail-flow or authorization behavior without tests and explicit review.
- Preserve existing configuration defaults and documented legacy compatibility.

## Development setup

```bash
cd mailbox-app
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements/development.txt
```

## Required local gates

From the repository root:

```bash
python scripts/manage_documents.py check
python scripts/test_documents.py
python scripts/check_documentation_policy.py --base HEAD^ --head HEAD
python scripts/check_docs.py
python scripts/validate_templates.py
python scripts/test_installer.py
python scripts/test_operations.py
python scripts/forensic_audit.py --root . --full
```

The full gate runs tests, coverage, Ruff, Bandit, Django checks, contact-service tests and source-safety checks.

## Pull requests

1. Open an issue for significant behavior, schema or deployment changes.
2. Keep changes narrow and explain compatibility impact.
3. Create or update a `documents/phases/PHASE-NNN-*.md` record for every maintained feature phase.
4. Update `documents/USER_MANUAL.md`, `documents/HOW_TO_USE.md`, or `documents/ADMIN_GUIDE.md` whenever user-visible behavior changes.
5. Run `python scripts/manage_documents.py sync` and commit the generated documentation index and manifest.
6. Add or update tests for every behavior change.
7. Update `CHANGELOG.md`, engineering documentation and release notes where applicable.
8. Do not commit secrets, real mailbox data, personal email addresses, certificates, databases, logs, archives or generated credentials.
9. Confirm the pull-request checklist and CI results.

## Documentation-first phase workflow

Start a maintained phase before implementation:

```bash
python scripts/manage_documents.py new-phase \
  --phase-id PHASE-001 \
  --title "Feature title" \
  --summary "What the phase changes for users"
```

Complete the generated draft, update the affected guides and changelog, then run `sync`, `check`,
the documentation contract tests and the feature-change policy. Draft phase documents and stale
generated documentation cannot pass CI.

## Coding standards

Follow `docs/CODING_STANDARDS.md`. New Python must support Python 3.12 and pass the configured Ruff and Bandit rules. Shell changes must use fail-closed practices and pass `bash -n` plus installer/operations contract tests.

By contributing, you agree that your contribution is licensed under `AGPL-3.0-or-later`.
