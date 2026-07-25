# Screenshot guide

The immutable files under `design/intake/original/` are approved design references, not evidence
of implemented runtime behavior. They may contain controls for planned or architecture-review
features and must not be published as completed product screenshots. The design manifest records
their status and scope.

The source package intentionally excludes screenshots containing real mail, users, domains, IP addresses or credentials.

PHASE-002 implements the shared application shell, but the existing page bodies are not yet
redesigned. Runtime screenshots may be used to verify sidebar, top bar, account menu, responsive
drawer, sign-in shell, and active navigation only. Do not present the imported PNG pages or any
planned controls as implemented product behavior. Page-comparison screenshots remain pending each
page-specific phase and staging verification.

Recommended GitHub README/release screenshots:

1. Login page with a synthetic domain
2. Administrator dashboard with synthetic counts
3. Mailbox list with `example.com` addresses
4. Inbox and message detail using generated fixture mail
5. User-management and mailbox-assignment screens
6. Public website and contact form
7. Installer `--plan` output with documentation-only IP ranges

Before publishing, remove personal data, browser profiles, terminal history, server identifiers and notification contents. Use only `example.com`, `example.org`, `example.net` and documentation IP ranges.
