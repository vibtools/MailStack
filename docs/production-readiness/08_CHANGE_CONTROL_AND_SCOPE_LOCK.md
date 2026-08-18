# Change Control and Scope Lock

## Scope owner rule

The frozen baseline may change only inside explicitly approved PHASE-006 and PHASE-007 scope. A useful cleanup,
refactor, rename or redesign is **not authorization** by itself.

## Change classes

### Class A — Approved defect correction
Allowed when directly tied to a forensic finding and phase task.

Examples:
- sanitizer CSS leakage fix;
- existing-message repair command;
- compact UI token mapping;
- responsive Mailboxes fix;
- authenticated footer cleanup;
- confirmed Gunicorn service-template fix.

### Class B — Required supporting test/documentation
Allowed when necessary to verify Class A work.

Examples:
- regression fixtures;
- UI contract tests;
- backfill tests;
- phase/change manifests;
- release notes and acceptance evidence.

### Class C — Requires explicit additional owner approval
Do not implement automatically.

Examples:
- database schema migration not already approved;
- new external dependency;
- remote-image proxy;
- new mail protocol;
- new user role model;
- route/API redesign;
- new public page/feature;
- new update wrapper command if it changes deployment surface;
- deletion/renaming of existing features or modules.

## Protected contracts

Implementation must preserve:

- URL names and route behavior unless a confirmed defect specifically requires a narrow guard;
- form field names and POST contracts;
- CSRF handling;
- object authorization;
- mailbox membership and delete permissions;
- read/unread semantics;
- soft-delete semantics;
- attachment authorization;
- original Maildir source preservation;
- mail database schema unless separately approved;
- Postfix/Dovecot contracts;
- service names;
- backup/upgrade/rollback behavior;
- receive-only scope.

## UI reference boundary

VibTools and Licora are **design references**, not source-code donors for MailStack runtime behavior.

Allowed to adopt:
- typography scale;
- spacing/density;
- sidebar/topbar geometry;
- component grouping;
- table/action-menu patterns;
- responsive drawer structure;
- accessibility patterns.

Must not copy without explicit need:
- product branding;
- product-specific colors;
- unrelated business features;
- Licora/PHP updater behavior;
- VibTools dark theme as MailStack's production theme.

## File-change discipline

Each implementation phase must produce:

1. exact changed-file list;
2. exact deleted-file list (normally empty unless owner-approved);
3. SHA-256 for the delta artifact;
4. change manifest mapping each file to an approved task/finding;
5. regression/test report;
6. phase completion-log update.

Any file not mapped to an approved task is an out-of-scope finding and blocks merge until explained or removed.

## Stop conditions

Stop implementation and request review when:

- base commit/tree does not equal the frozen baseline;
- a migration becomes necessary unexpectedly;
- a fix would weaken sanitizer/security isolation;
- existing mail data would need deletion/re-ingestion;
- a change affects Postfix/Dovecot/mail routing unexpectedly;
- a new dependency becomes necessary;
- repeated test failures indicate a root cause outside approved scope;
- production state differs from release source identity.
