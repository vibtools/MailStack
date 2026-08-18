# Two-Phase A-to-Z Production-Readiness Roadmap

## Roadmap constraint

The remaining production-readiness update is limited to **a maximum of two implementation phases**.
No third implementation phase is planned. If a new blocker appears, it must be absorbed into one of these two
phases or the owner must explicitly re-plan the roadmap.

## Phase map

| Phase | Name | Primary purpose | Start gate | Completion gate |
|---|---|---|---|---|
| **PHASE-006** | Reader Integrity, Data Repair & Runtime Error Closure | Fix mail readability and critical operational findings first | Planning pack approved | Reader/security/backfill/runtime tests and live smoke PASS |
| **PHASE-007** | Compact UI System & Final Production Acceptance | Complete compact responsive UI and perform final production acceptance | PHASE-006 logged complete | Full CI + visual/responsive + real inbound E2E + stability PASS |

---

# PHASE-006 — Reader Integrity, Data Repair & Runtime Error Closure

## Objective

Make every received email reliably readable without weakening MailStack's security boundary, repair already
indexed affected messages safely, close the observed Gunicorn runtime finding, and establish reliable error
handling before broad UI refinement.

## A-Z implementation sequence

### 006-A — Baseline re-verification
- verify base tag/commit/tree/source SHA against the frozen v1.3.3 identity;
- verify no unrelated local changes;
- verify current test baseline before modifications.

### 006-B — Reproduction fixtures
- add representative HTML fixtures containing `head`, `style`, media/style rules, remote images, inline safe
  content, links, tables, plain-text alternative and malformed HTML;
- include a fixture representative of the observed Harpoon CSS leakage;
- capture expected readable text and forbidden output patterns.

### 006-C — Sanitizer correction
- remove non-body style/active content safely before Bleach sanitization;
- keep allowlisted structural HTML only;
- keep event-handler/style denial unless a separately reviewed safe CSS policy is explicitly approved;
- keep URL protocol validation;
- ensure no raw style-block CSS appears as visible body text.

### 006-D — Remote-image graceful handling
- maintain default no-tracking/no-remote-fetch posture;
- remove or convert blocked remote images into a non-broken presentation;
- preserve meaningful alt text when useful;
- do not introduce a remote image proxy in this phase.

### 006-E — Message reader security UX cleanup
- remove the permanent visible `Protected rendering · remote and active content are blocked.` banner from the
  normal reading path;
- retain iframe `sandbox`, `referrerpolicy="no-referrer"`, sanitizer and attachment restrictions;
- add tests that prove security remains active after the visual banner is removed.

### 006-F — Existing-message repair command
- implement an idempotent management command for re-parsing existing source Maildir messages;
- dry-run first;
- mailbox and message targeting;
- bounded batch operation and result counters;
- preserve UUID/read/delete/membership/source identity;
- do not delete/re-ingest records.

### 006-G — Existing-message repair verification
- run dry-run against controlled fixtures/test DB;
- run mutation test on copies/fixtures;
- prove second run is safe/idempotent;
- compare field-level before/after contract.

### 006-H — Reader fallback/error handling
- if safe HTML cannot be produced, prefer usable text body;
- if neither is usable, render a compact non-crashing error/empty state;
- never expose raw parser exception details to ordinary users;
- record useful server-side diagnostics/audit context.

### 006-I — Gunicorn read-only-filesystem forensic closure
- reproduce with focused logs;
- capture attempted filesystem path/context;
- classify repo-owned vs host/upstream;
- apply narrow fix only if evidence supports it;
- preserve `ProtectSystem=strict` unless a narrower writable path is proven necessary;
- add/revise service contract tests if template changes.

### 006-J — Authenticated live-endpoint regression
- direct authenticated browser GET `/messages/live/` must redirect into normal app UI, never raw JSON;
- explicit background custom-header request returns JSON;
- cached legacy `Accept: application/json` poller compatibility remains functional.

### 006-K — Phase verification
- parser/sanitizer unit tests;
- message-reader functional tests;
- backfill command tests;
- auth/access regressions;
- attachment regressions;
- Django checks / migration drift check;
- Ruff/Bandit/dependency audit according to project policy;
- deterministic source forensic audit.

### 006-L — Controlled live acceptance
- deploy through existing upgrade tooling, not manual source editing;
- verify services and health;
- open previously broken HTML emails and confirm readability;
- verify plain-text email;
- verify no repeated Gunicorn control-server error during bounded observation;
- log PHASE-006 completion before PHASE-007 starts.

## PHASE-006 must not include

- broad shell/table/form redesign beyond any minimum reader change necessary for usability;
- database migration unless separately proven necessary and explicitly approved;
- outbound mail features;
- route/model/permission redesign.

---

# PHASE-007 — Compact UI System & Final Production Acceptance

## Objective

Apply a coherent compact design system across the authenticated MailStack application, using VibTools Web UI
v2.1.2 for structural geometry/typography and Licora v5.5.0 as an implementation-pattern reference, while
preserving MailStack's light theme, brand colors and all business logic.

## A-Z implementation sequence

### 007-A — MailStack compact token mapping
Create shared MailStack light-theme tokens mapped to the VibTools structural reference:

- primary UI text target: approximately `13px`;
- micro/helper: `11–12px`;
- card/compact heading: `13–14px`;
- section heading: approximately `16px`;
- page-title cap: approximately `20px` where practical;
- regular/medium weights `400/500`, limited `600` emphasis;
- sidebar target: approximately `196px` expanded;
- topbar target: approximately `44px`;
- buttons: `28px` small / `32px` medium target;
- inputs: `30px` small / `34px` medium target;
- card padding around `10px 12px`;
- radii around `6px / 8px / 12px`;
- light, border-driven surfaces; avoid broad decorative shadows.

Exact final values may be adjusted slightly for MailStack logo/readability, but deviations require documented
reason rather than page-specific hardcoding.

### 007-B — Shared authenticated shell
- compact expanded sidebar;
- coherent icon-only desktop collapse with tooltips/accessible labels;
- compact topbar;
- mobile/tablet off-canvas navigation;
- no duplicate navigation tree;
- no viewport-level horizontal overflow.

### 007-C — Authenticated footer cleanup
- remove Source code/Open-source hub/Free subdomains links from operational workspace;
- retain minimal product/legal identity only if needed;
- no large persistent footer consuming mail-reading space.

### 007-D — Mailboxes desktop redesign
- compact full-width list/table;
- address primary, status/unread/total/last-received secondary;
- demote Created metadata;
- compact action menu/area preserving permission and CSRF/action contracts;
- shared toolbar for search/status filters and pagination.

### 007-E — Mailboxes mobile redesign
- purpose-built compact mobile list/card;
- essential data above secondary metadata;
- compact action handling;
- no generic seven-row table-card expansion;
- verify 320/360/375/390/400/430px widths.

### 007-F — Inbox compact refinement
- target denser rows than current 58px baseline;
- sender + subject/preview + attachment state + time hierarchy;
- unread emphasis without oversized weight;
- filter/search toolbar uses compact shared controls;
- live-inserted rows exactly match server-rendered rows.

### 007-G — Message reader compact refinement
- compact back/action/sender/routing header;
- readable body region without excessive nested scrolling;
- attachments directly follow body;
- no permanent security banner;
- safe HTML and plain fallback remain unified.

### 007-H — Create mailbox redesign
- compact page width/rhythm;
- compact local-part input group;
- improved user assignment selector while preserving field semantics;
- clear primary action and validation.

### 007-I — User management redesign
- compact table/list typography and row spacing;
- correct username/created metadata separation;
- role/status chips;
- action consolidation;
- responsive behavior designed specifically for the data.

### 007-J — Add/Edit user redesign
- compact fields and help text;
- preserve password validation copy;
- compact assigned-mailbox selection;
- clear permission controls;
- no behavior changes to admin restrictions or mailbox assignments.

### 007-K — Shared feedback/error visual system
- form errors, flash messages, warnings, empty states and 404/500 pages use compact consistent components;
- preserve error semantics and accessibility;
- add 403/400 presentation only if current behavior/test evidence supports it without changing authorization
  semantics.

### 007-L — Responsive/accessibility pass
- keyboard navigation;
- focus visibility;
- accessible icon-only controls;
- aria-current/expanded/controls behavior;
- reduced motion behavior;
- 200% zoom sanity;
- no clipped text or inaccessible action menus.

### 007-M — Visual regression matrix
- Dashboard;
- Mailboxes desktop/mobile;
- Inbox;
- HTML message;
- plain message;
- attachment message;
- Create mailbox;
- User management;
- Add/Edit user;
- delete/confirmation states;
- empty/loading/error states;
- collapsed and mobile navigation.

### 007-N — Full regression/CI qualification
- existing application tests;
- UI contract tests;
- parser/backfill tests from PHASE-006;
- release/upgrade tests;
- documentation/forensic gates;
- dependency/security gates;
- deterministic build/release verification.

### 007-O — Production upgrade rehearsal
- build deterministic release artifact;
- verify checksum/manifest;
- verify upgrade tool sees correct version direction and migration count;
- validate rollback snapshot path and data backup contract in isolated/staging environment when available.

### 007-P — Production deployment
- use supported upgrade tool in resilient terminal session;
- capture `MAILSTACK_UPGRADE=PASS` and exact source SHA;
- verify installation marker and deployed-source fidelity.

### 007-Q — Production UI acceptance
- owner visual check against supplied screenshots and approved structure;
- HTML emails readable;
- mobile compactness approved;
- no public footer contamination;
- no raw JSON navigation.

### 007-R — Real external inbound E2E
At least:
- one normal external email;
- one HTML-rich external email;
- one message with attachment when practical;
- prove Postfix -> Dovecot LMTP -> Maildir -> ingestion -> MariaDB -> browser visibility;
- prove message remains readable and attachment access works.

### 007-S — Bounded stability observation
- services remain active;
- no repeated Gunicorn read-only-filesystem error;
- no ingestion error growth;
- health remains ready;
- no unexpected 5xx in application logs.

### 007-T — Final documentation and completion log
- update actual implementation status;
- mark PHASE-007 complete;
- record 2/2 phases complete;
- record final release identity and acceptance evidence;
- no further update phase remains unless the owner opens a new scope.

## Final roadmap state target

`PHASE-006 COMPLETE` -> `PHASE-007 COMPLETE` -> `PRODUCTION READY / OWNER ACCEPTED`
