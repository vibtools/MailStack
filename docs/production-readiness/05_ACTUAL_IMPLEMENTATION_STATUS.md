# Actual Implementation Status

## Purpose

Track **what is actually working**, what exists but is defective, what each production-readiness phase adds,
and what remains. This file must reflect evidence, not planned marketing language.

## Baseline: v1.3.3 actual working state

### Working and verified at server/core level

| Capability | State | Notes |
|---|---|---|
| Receive-only SMTP architecture | WORKING | No outbound send/reply/forward feature |
| Postfix inbound service | WORKING | Active and config check passed during live acceptance |
| Dovecot LMTP delivery | WORKING | Active and config check passed |
| Maildir storage | WORKING | Readiness/storage verification passed |
| MariaDB application data | WORKING | Ready check passed |
| Gunicorn web app serving | WORKING WITH OPEN LOG FINDING | HTTP works; control-server read-only-filesystem log remains open |
| Nginx HTTPS app/public routing | WORKING | Config and HTTP checks passed |
| Maildir ingestion worker | WORKING | Verification scan reported zero errors |
| Public contact service | WORKING | Active during live acceptance |
| Backup | WORKING | Coordinated upgrade backup verified |
| Upgrade | WORKING | v1.3.0-rc.1 -> v1.3.3 completed with `MAILSTACK_UPGRADE=PASS` |
| Automatic source/runtime rollback path | WORKING/PROVEN | A failed no-migration upgrade attempt auto-rolled back successfully |
| Health `/health/live/` | WORKING | HTTP 200 live |
| Health `/health/ready/` | WORKING | HTTP 200 ready with all checks true |

### Working application features

- login/logout;
- failed-login throttling/lockout and audit events;
- dashboard operational summary;
- mailbox list/search/status filtering/pagination;
- mailbox creation and Maildir provisioning;
- mailbox enable/disable;
- permission-gated mailbox deletion/reservation;
- user list/search;
- user creation/edit/delete rules;
- mailbox assignment to users;
- per-user delete permissions;
- Inbox search by sender/subject;
- read/unread filter;
- attachment/no-attachment filter;
- message row previews;
- message detail route;
- automatic mark-read on open;
- mark-unread action;
- permission-gated soft delete;
- attachment download authorization;
- background live-update endpoint and direct-navigation guard in source;
- plain-text body fallback;
- sanitized-HTML iframe mechanism exists;
- audit records for major user/mailbox/message events.

## Existing but not production-acceptable

| Capability | Actual state | Why not accepted |
|---|---|---|
| HTML email reading | **DEFECTIVE / BLOCKER** | Style-block CSS is visible as body text for real emails |
| Existing stored HTML bodies | **DEFECTIVE / BLOCKER** | Parser fix alone will not repair duplicate-indexed messages |
| Remote image blocking presentation | DEFECTIVE UX | Can leave broken-image/alt residue |
| Protected-rendering security notice | FUNCTIONAL BUT REJECTED UX | Permanent banner is intrusive |
| Mailboxes desktop UI | FUNCTIONAL BUT NOT COMPACT | Heavy seven-column table/actions |
| Mailboxes mobile UI | FUNCTIONAL BUT NOT COMPACT | Excessively tall generic card conversion |
| Collapsed sidebar | FUNCTIONAL BUT NOT ACCEPTED | Geometry/spacing visually unfinished |
| Message reader layout | FUNCTIONAL BUT NOT ACCEPTED | Excessive height/nested scrolling/spacing |
| Create mailbox UI | FUNCTIONAL BUT NOT ACCEPTED | Large dead space/native tall multi-select |
| User management UI | FUNCTIONAL BUT NOT ACCEPTED | Density/alignment/action presentation issues |
| Add/Edit user UI | FUNCTIONAL BUT NOT ACCEPTED | Oversized controls/help spacing |
| Authenticated footer | FUNCTIONAL BUT REJECTED UX | Public/promotional links appear in operational app |

## PHASE-006 implementation candidate — locally qualified, live acceptance pending

The PHASE-006 source implementation is locally focused-qualified but is not yet a production/live acceptance claim.
The current production baseline defects listed above remain authoritative until controlled deployment and live repair acceptance pass.

- corrected safe HTML parser/sanitizer;
- readable style-heavy HTML emails;
- no CSS leakage from style blocks;
- graceful blocked remote-image presentation;
- silent retained rendering security controls;
- existing-message repair/backfill management command;
- safe text fallback when sanitized HTML cannot be used;
- authenticated `/messages/live/` document-navigation proof;
- Gunicorn control-server filesystem finding fixed or formally evidenced/dispositioned;
- focused regression tests and live reader acceptance.

## PHASE-007 expected actual additions

After PHASE-007 is complete, this section must be converted from `EXPECTED` to `WORKING VERIFIED` with evidence.

- compact MailStack token system based on VibTools structural sizing;
- compact desktop shell/topbar/sidebar;
- proper mobile off-canvas navigation;
- clean authenticated workspace footer;
- compact Mailboxes desktop list;
- compact Mailboxes mobile list/cards;
- refined compact Inbox;
- refined compact unified reader;
- compact Create mailbox page;
- compact User management page;
- compact Add/Edit user pages;
- consistent responsive/empty/error/feedback components;
- final accessibility checks;
- final deterministic build/CI qualification;
- final production upgrade verification;
- real external inbound E2E including HTML and attachment coverage;
- final bounded stability acceptance.

## Remaining feature boundary after production readiness

The following remain intentionally **not implemented** unless a future owner-approved scope changes the product:

- outbound Compose;
- Reply;
- Forward;
- Sent;
- Drafts;
- SMTP submission for users;
- IMAP;
- POP3;
- public registration;
- campaigns/bulk sending;
- high-availability/multi-node architecture.

They are not production-readiness defects because MailStack is intentionally receive-only.
