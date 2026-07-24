# Coding standards

## Python

- Target Python 3.12 and Django 5.2.
- Use type hints for new public functions where practical.
- Keep database values parameterized; interpolate only strictly validated SQL identifiers.
- Preserve transaction boundaries, authorization checks and migration history.
- Pass Ruff, Bandit, Django checks and the full pytest suite.

## Django

- Enforce object-level mailbox access in querysets and services, not only templates.
- Keep forms and views fail-closed on authorization errors.
- Add migrations for schema changes; never edit an applied migration.
- Avoid logging message bodies, credentials or personal data.

## Shell

- Use `set -Eeuo pipefail`, restrictive umasks and quoted variables.
- Validate paths, hostnames, identifiers and archives before privileged operations.
- Avoid `eval`, unpinned remote execution and curl-to-shell installation patterns.
- Preserve service state during maintenance and fail before printing success.

## Documentation

- Use relative links for repository documents.
- Mark release-candidate limitations accurately.
- Never present unexecuted external acceptance as passed.
