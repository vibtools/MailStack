# Official Baseline Freeze — MailStack v1.3.3

## Freeze decision

`v1.3.3` is the official frozen baseline for the next production-readiness update cycle.

### Canonical baseline identity

| Field | Frozen value |
|---|---|
| Product | MailStack |
| Version | `1.3.3` |
| Tag | `v1.3.3` |
| Commit | `21dff33219afab3819e7bd1ae1e0a0cc2e7d3698` |
| Tree | `74682033f3164a6a0069a381ae5a38661aad1669` |
| Release archive | `mailstack-1.3.3-source.zip` |
| Release archive SHA-256 | `9e2016ce486f1e1f7e30361c73fa50ff73e7c9c72f87dd0941c1a9b5ed2e9964` |
| Live installed version | `1.3.3` |
| Live previous version marker | `1.3.0-rc.1` |
| Live source-fidelity check | PASS |
| Upgrade rollback snapshot | Verified during live upgrade |
| Coordinated data backup | Verified during live upgrade |

## Evidence reconciliation

### [CONFLICT] Uploaded candidate baseline versus published baseline

The uploaded `MailStack_v1.3.3_Baseline.zip` has SHA-256
`b25d693caef36b8370c279bdf5c59d97a1e8d100d8485eccbc8fd74bb4d1370f`, and its accompanying freeze
record explicitly classifies it as `OWNER-FROZEN_CANDIDATE` with release/live gates pending.

The production server was later upgraded using the published v1.3.3 release archive with SHA-256
`9e2016ce486f1e1f7e30361c73fa50ff73e7c9c72f87dd0941c1a9b5ed2e9964`, and the deployed source-fidelity
check passed against that published source.

**Resolution:** the published/live-verified release identity above is authoritative for future implementation.
The candidate ZIP remains evidence/reference only.

## Frozen architecture and behavior

Unless a later owner approval explicitly expands scope, the following are immutable:

- receive-only product model;
- Internet SMTP -> Postfix -> Dovecot LMTP -> Maildir -> ingestion -> MariaDB -> Django/browser flow;
- no outbound send/reply/forward, SMTP submission, IMAP, POP3, campaigns or public registration;
- mailbox ownership/membership and object authorization semantics;
- user/admin permission model and destructive-action permissions;
- message read/unread and soft-delete semantics;
- attachment authorization and storage confinement;
- database schema unless a migration is separately reviewed and explicitly approved;
- Postfix/Dovecot routing and LMTP contracts;
- installer, backup, upgrade and rollback contracts unless a confirmed defect requires a narrow correction;
- service names, deployment directories, DNS/TLS model and production data locations;
- MailStack name, logo, light-theme product identity and blue-oriented brand color family.

## Allowed next-cycle scope

The planned next cycle is restricted to production-readiness corrections identified in the forensic report:

1. HTML message-rendering integrity and repair of already-indexed affected messages.
2. Safe rendering UX cleanup without weakening sanitization/sandbox/security controls.
3. Confirmed runtime error investigation/closure, including the observed Gunicorn read-only-filesystem control-server log.
4. Compact shared UI geometry and typography using VibTools structural references while retaining MailStack theme.
5. Mailboxes, Inbox, message reader, create-mailbox, user-management, add/edit-user and authenticated-shell responsive refinement.
6. Authenticated footer cleanup.
7. Focused error-handling improvements required by those changes.
8. Automated tests, live acceptance, inbound email E2E and final production-readiness evidence.

## Prohibited implementation behavior

- No unrelated refactor or cleanup.
- No feature removal unless explicitly required by approved scope; visual removal of non-operational clutter is allowed only where documented.
- No renaming routes, models, classes, modules, IDs or configuration keys for style preference.
- No data-destructive repair of existing messages.
- No delete-and-reingest strategy for existing email repair.
- No weakening HTML sanitization, iframe sandboxing, referrer protection, CSRF, authentication or object authorization.
- No hidden feature expansion such as compose/reply/forward.

## Freeze release rule

Any implementation delta must be compared against this baseline identity. If the base commit/tree differs,
implementation stops until the owner explicitly re-baselines the project.
