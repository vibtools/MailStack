# Error Handling Register and Production Plan

## Purpose

Record error handling that is already implemented in v1.3.3, identify gaps exposed by the live forensic audit,
and define additions allowed during the two production-readiness phases.

## Existing error handling — [CONFIRMED]

### Authentication and login
- failed login attempts are persisted;
- lockout/rate-limiting is enforced after the configured failure threshold/window;
- successful login clears prior failed attempts for the same normalized username/IP context;
- login success/failure events are audit-recorded;
- unsafe external `next` redirects are rejected by host/scheme validation.

### Authorization
- admin-only operations call `require_admin()` and raise `PermissionDenied` when unauthorized;
- non-admin mailbox/message queries are restricted to membership-accessible objects;
- unauthorized destructive message/mailbox access is intentionally hidden as 404 in relevant paths;
- delete permissions are separately evaluated for messages and mailboxes.

### Mailbox validation and provisioning
- local-part validation rejects empty/too-long/path-dangerous/invalid values;
- duplicate/reserved mailbox addresses are rejected;
- provisioning uses a dedicated `ProvisioningError` abstraction;
- provisioning/status/delete operations use transactions and guarded filesystem paths;
- safe provisioning locks prevent conflicting mailbox operations;
- UI catches provisioning failures and surfaces form/flash errors.

### Message and attachment access
- invalid read-state mutation raises `PermissionDenied`;
- missing/unauthorized messages return 404;
- attachment paths are confined to the configured attachment root;
- missing attachment files return 404;
- downloads set `nosniff` and private/no-store headers.

### Ingestion
- MIME parser failures fall back to decoded text and record a warning;
- invalid/missing Date and sender metadata produce parse warnings rather than crashing ingestion;
- oversized messages and attachments are bounded;
- attachment storage rollback deletes partially stored attachment files on ingestion failure;
- database creation is transaction-protected;
- ingestion exceptions increment error counters and write audit/log evidence;
- duplicate Maildir source keys are detected and not re-created.

### Health and readiness
- liveness endpoint returns process-level live state;
- readiness checks database, pending migrations, mail storage, attachment storage and core production config;
- storage writability is tested through temporary healthcheck files;
- readiness returns HTTP 503 when required checks fail.

### Application error pages
- custom 404 template/handler exists;
- custom 500 template/handler exists.

### Upgrade/rollback operations
- deterministic archive/checksum verification fails closed;
- migration-history mutation is guarded;
- pre-upgrade source snapshot and coordinated data backup precede source mutation;
- no-new-migration source/runtime failures support automatic source rollback;
- migration-capable failure after schema mutation refuses unsafe automatic source/schema rollback;
- service/config/post-upgrade verification is blocking.

## Current error-handling gaps / required additions

### EH-001 — HTML rendering failure must not make mail unreadable
**Phase:** PHASE-006
**Priority:** BLOCKER

Required behavior:
- sanitizer strips non-content CSS/style blocks without leaking their text;
- if sanitized HTML is unusable, render the stored plain-text alternative;
- if neither body is usable, show a compact safe message state rather than raw code or an exception;
- record server-side diagnostic context without exposing sensitive source content in user-facing error text.

### EH-002 — Existing-message repair command needs fail-safe behavior
**Phase:** PHASE-006
**Priority:** BLOCKER

Required behavior:
- `--dry-run` default/recommended path;
- bounded selection;
- per-message success/skip/warning/error counters;
- one message failure does not corrupt unrelated messages;
- transaction boundary per message or safe batch strategy;
- preserve original Maildir source;
- idempotence proof;
- non-zero process exit when blocking repair errors occur.

### EH-003 — Remote-image blocking must degrade gracefully
**Phase:** PHASE-006

A rejected remote image must not leave a broken-image icon/layout residue that looks like a rendering failure.
It should disappear cleanly or become a safe compact placeholder/alt representation, without remote tracking.

### EH-004 — Gunicorn control-server filesystem error must be classified
**Phase:** PHASE-006
**State:** OPEN

Required:
- capture exact attempted path and trigger;
- classify whether it affects request serving/reload/control features;
- correct only the necessary writable path/config if repo-owned;
- retain systemd confinement;
- bounded post-fix log observation.

### EH-005 — 400/403 presentation consistency
**Phase:** PHASE-007
**State:** REVIEW

Current source has explicit custom 404/500 pages. Permission failures may use Django's default 403 response.
During UI consolidation, determine whether dedicated 400/403 templates can be added without changing underlying
status codes or authorization semantics. This is presentation-only and must be test-backed.

### EH-006 — Responsive action-menu failure states
**Phase:** PHASE-007

If row actions are consolidated into menus, keyboard/focus/backdrop behavior and failed POST feedback must remain
accessible. No destructive action may become a client-only operation that bypasses existing server-side checks.

### EH-007 — Empty/loading/filter states
**Phase:** PHASE-007

Provide compact consistent states for:
- no mailboxes;
- no messages;
- no filter results;
- unavailable message body;
- missing attachment;
- loading/live-update delay where applicable.

These states must not claim data loss when the source Maildir remains preserved.

### EH-008 — User-visible flash/error density
**Phase:** PHASE-007

Existing Django form errors and flash messages remain semantically correct. Refine their layout so they are
compact and noticeable without expanding the entire page or hiding validation detail.

## Error logging rules

- Never log passwords, secret keys, private signing material, full session tokens or private environment values.
- Do not copy complete raw emails into generic exception logs.
- Prefer identifiers: mailbox address where appropriate, message UUID/source key, error type and bounded warning.
- User-facing messages must be actionable but not reveal filesystem/database internals.
- Security/authorization failures must not disclose object existence to unauthorized users.

## Final acceptance for error handling

Error-handling work is accepted only when:

- no raw CSS/parser exception is shown as normal mail content;
- message reader has a safe fallback path;
- repair command is dry-run capable and idempotent;
- no regression in 404/authorization behavior;
- no repeated unresolved Gunicorn control-server error in the final observation window;
- health/readiness remains accurate;
- automated tests cover all new error branches.
