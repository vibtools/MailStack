# MailStack v1.2.1 Security Audit Report

## Result

**Static/application security review: PASS**  
**Live production security acceptance: pending controlled installation**

## Dependency remediation

- Rejected release v1.2.0 pinned vulnerable Bleach 6.3.0 and python-dotenv 1.2.1.
- v1.2.1 pins Bleach 6.4.0 and python-dotenv 1.2.2.
- Bleach email linkification is explicitly disabled with `parse_email=False`.
- `scripts/audit_dependencies_v1_2_1.sh` uses an AST check to guarantee exactly one `Linker` call and a literal `parse_email=False` before applying the narrow `GHSA-g75f-g53v-794x` exception.
- Any additional Linker call or any change enabling email parsing fails the audit.
- Deployment and post-deployment verification require exact Django, Bleach, and python-dotenv versions.

## Application controls verified

- Central object-level authorization for mailbox, message, safe HTML, attachment, dashboard, and live-update access
- Administrator-only user management
- Ordinary-user mailbox isolation
- Separate message-delete and mailbox-delete permissions
- CSRF-protected POST destructive actions with confirmation
- Soft deletion preserves Maildir evidence and blocks re-ingestion/reuse
- No user password-change or public password-reset route
- Case-insensitive username and mailbox uniqueness
- Inter-process mailbox provisioning lock
- Parameterized cross-schema SQL
- Confined paths and symlink rejection
- Sanitized HTML in a sandboxed iframe
- Authorized attachment delivery as `application/octet-stream`
- Authenticated, scoped, bounded, body-free live-update payloads
- Safe DOM insertion using `textContent`
- Nginx duplicate Host-header defect remains closed
- ACME, dotfile denial, TLS, protected attachments, and security headers preserved
- Release source cannot be the live application tree

## Tool results

- 187 automated tests: PASS
- Ruff: PASS
- Bandit: PASS
- Django checks: PASS
- Migration drift: PASS
- Local online vulnerability query: unavailable because the build container cannot resolve public PyPI

## Mandatory server gate

Run `scripts/audit_dependencies_v1_2_1.sh` on the network-enabled VPS. Installation is prohibited unless it reports `Online dependency vulnerability audit: PASS`.
