# Screenshot guide

The immutable files under `design/intake/original/` are approved design references, not evidence
of implemented runtime behavior. They may contain controls for planned or architecture-review
features and must not be published as completed product screenshots. The design manifest records
their status and scope.

The source package intentionally excludes screenshots containing real mail, users, domains, IP addresses or credentials.

Recommended GitHub README/release screenshots:

1. Login page with a synthetic domain
2. Administrator dashboard with synthetic counts
3. Mailbox list with `example.com` addresses
4. Inbox and message detail using generated fixture mail
5. User-management and mailbox-assignment screens
6. Public website and contact form
7. Installer `--plan` output with documentation-only IP ranges

Before publishing, remove personal data, browser profiles, terminal history, server identifiers and notification contents. Use only `example.com`, `example.org`, `example.net` and documentation IP ranges.
