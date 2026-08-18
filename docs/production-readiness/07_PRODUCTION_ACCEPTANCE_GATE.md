# Production Acceptance Gate

## Rule

Production readiness is a **blocking gate**, not a subjective statement. Every `BLOCKING` item below must pass.
A healthy server does not compensate for an unreadable mailbox UI.

## Gate A — Baseline and source integrity — BLOCKING

- [ ] base commit/tree equals the frozen v1.3.3 baseline before implementation;
- [ ] final release commit/tag/version are internally consistent;
- [ ] deterministic source archive verifies;
- [ ] SHA-256 and source manifest verify;
- [ ] no unexpected file additions/deletions;
- [ ] deployed source matches the final release source after production upgrade.

## Gate B — HTML reader integrity — BLOCKING

- [ ] Harpoon-style fixture renders readable content;
- [ ] zero visible style-block CSS rules;
- [ ] script/event-handler content is removed/blocked;
- [ ] unsafe remote images are not fetched by default;
- [ ] blocked remote image does not show broken-image residue;
- [ ] links remain safely constrained;
- [ ] iframe remains sandboxed;
- [ ] referrer policy remains `no-referrer`;
- [ ] plain-text-only mail renders correctly;
- [ ] malformed HTML falls back safely without 500.

## Gate C — Existing-message repair — BLOCKING

- [ ] dry-run command works;
- [ ] targeted mailbox/message selection works;
- [ ] repair uses original Maildir source;
- [ ] UUID/read/delete/membership/source identity is preserved;
- [ ] first mutation run repairs affected body;
- [ ] second run is safe/idempotent;
- [ ] errors are counted/reported without data destruction;
- [ ] production repair has a before/after count report.

## Gate D — Core functionality regression — BLOCKING

- [ ] login/logout;
- [ ] login throttling;
- [ ] dashboard;
- [ ] mailbox list/search/filter/pagination;
- [ ] create mailbox;
- [ ] enable/disable mailbox;
- [ ] permission-gated mailbox delete;
- [ ] user list/create/edit/delete rules;
- [ ] mailbox assignment;
- [ ] Inbox search/read/attachment filters;
- [ ] message read/unread;
- [ ] permission-gated message delete;
- [ ] attachment download;
- [ ] live update polling;
- [ ] direct live endpoint does not show raw JSON as a document.

## Gate E — Compact desktop UI — BLOCKING

- [ ] topbar/sidebar meet approved compact structure;
- [ ] Mailboxes table/list is compact and legible;
- [ ] Inbox rows are compact;
- [ ] message reader is compact/readable;
- [ ] Create mailbox form is compact;
- [ ] User management is compact;
- [ ] Add/Edit user forms are compact;
- [ ] authenticated public/promotional footer links are absent;
- [ ] owner approves desktop screenshots.

## Gate F — Responsive/mobile — BLOCKING

Verify at minimum: `320`, `360`, `375`, `390`, `400`, `430`, `768`, `1024`, desktop widths.

- [ ] no viewport horizontal overflow;
- [ ] mobile sidebar uses coherent drawer behavior;
- [ ] Mailboxes mobile list is not generic seven-row tall cards;
- [ ] message reader header/body/actions remain usable;
- [ ] forms fit without clipped controls;
- [ ] destructive actions remain accessible;
- [ ] owner approves mobile screenshots.

## Gate G — Accessibility — BLOCKING

- [ ] keyboard navigation works;
- [ ] visible focus indicators;
- [ ] icon-only controls have labels/tooltips;
- [ ] active navigation has accessible state;
- [ ] mobile drawer exposes expanded/controls state;
- [ ] Escape/backdrop close works;
- [ ] status is not color-only where text label exists;
- [ ] reduced-motion behavior preserved;
- [ ] 200% zoom sanity check.

## Gate H — Error handling — BLOCKING

- [ ] 404 and 500 remain correct;
- [ ] permission failures do not leak object existence;
- [ ] form errors remain visible;
- [ ] parser/render failure has safe fallback;
- [ ] existing-message repair failures are bounded and reported;
- [ ] no repeated unresolved Gunicorn control-server read-only-filesystem error during bounded observation;
- [ ] no unexpected new 5xx burst in application logs.

## Gate I — Security/static analysis/dependency — BLOCKING

- [ ] supported Python version test environment;
- [ ] Django system checks;
- [ ] migration drift check;
- [ ] full application tests;
- [ ] focused UI/parser/backfill tests;
- [ ] Ruff;
- [ ] Bandit;
- [ ] dependency audit according to repository policy;
- [ ] documentation/forensic source audit;
- [ ] release/upgrade contract tests.

## Gate J — Production operational health — BLOCKING

- [ ] MariaDB active;
- [ ] Postfix active and `postfix check` passes;
- [ ] Dovecot active and `doveconf -n` passes;
- [ ] Nginx active and config test passes;
- [ ] Gunicorn active;
- [ ] ingestion active;
- [ ] public-contact service active;
- [ ] `/health/live/` 200;
- [ ] `/health/ready/` 200 ready;
- [ ] app login page 200;
- [ ] public site 200.

## Gate K — Real external inbound E2E — BLOCKING

- [ ] send external normal email to a production mailbox;
- [ ] prove Postfix acceptance;
- [ ] prove Dovecot LMTP/Maildir arrival;
- [ ] prove ingestion creates/recognizes DB message;
- [ ] prove browser shows message;
- [ ] prove message is readable;
- [ ] repeat with HTML-rich email;
- [ ] repeat with attachment when practical;
- [ ] attachment download remains authorized and functional.

## Gate L — Backup/upgrade/rollback — BLOCKING

- [ ] final release upgrade artifact/checksum verifies;
- [ ] upgrade detects expected migration count;
- [ ] production backup/snapshot created before mutation;
- [ ] `MAILSTACK_UPGRADE=PASS` captured;
- [ ] installation marker contains final version/SHA;
- [ ] rollback path remains known and intact;
- [ ] no implicit database/Maildir rollback is performed without explicit reviewed need.

## Final decision states

Only one of these may be recorded:

- `PRODUCTION_READY=PASS`
- `PRODUCTION_READY=FAIL`
- `PRODUCTION_READY=BLOCKED`

`PASS` requires all blocking gates above plus owner visual acceptance.
