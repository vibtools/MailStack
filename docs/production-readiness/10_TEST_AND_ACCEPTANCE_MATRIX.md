# Test and Acceptance Matrix

## Purpose

Define the minimum deterministic test coverage for PHASE-006 and PHASE-007 so visual changes do not silently
break receive-only functionality, security or operational upgrade behavior.

## PHASE-006 focused matrix

| Area | Test | Expected |
|---|---|---|
| Sanitizer | style block in head | CSS rules absent from visible sanitized body |
| Sanitizer | script/event attributes | removed |
| Sanitizer | allowed structural HTML | preserved/readable |
| Sanitizer | links | only approved protocols; security callbacks preserved |
| Sanitizer | remote image | no external fetch; no broken residue |
| Sanitizer | data image | accepted only for approved data-image types |
| MIME | multipart alternative | text + HTML parsed correctly |
| MIME | malformed HTML | safe output/fallback, no crash |
| Reader | sanitized HTML present | unified safe HTML reader |
| Reader | plain only | readable plain fallback |
| Reader | neither usable | safe compact empty/error state |
| Reader security | iframe | sandbox remains present |
| Reader security | referrer | no-referrer remains present |
| Reader UX | security banner | permanent banner absent if owner-approved removal is implemented |
| Backfill | dry-run | no DB mutation |
| Backfill | target mailbox | only target scope considered |
| Backfill | mutation | approved fields update only |
| Backfill | identity | UUID/read/delete/source state unchanged |
| Backfill | second run | safe/idempotent |
| Live endpoint | normal authenticated GET | app redirect, not raw JSON |
| Live endpoint | custom live header | JSON |
| Live endpoint | legacy JSON Accept | JSON compatibility preserved |
| Gunicorn | service start/request | no functional regression |
| Gunicorn | bounded logs | no repeated unresolved read-only FS control error |

## PHASE-007 UI matrix

### Desktop
- Dashboard 1366/1440/1920 widths.
- Mailboxes with 0, 1, many rows.
- Mailbox search and status filters.
- Inbox with long sender/subject, unread/read, attachments.
- Message reader with long HTML and plain body.
- Create mailbox with/without assigned users.
- User management with long usernames and multiple role/status states.
- Add/Edit user validation errors.
- destructive confirmation screens.

### Mobile / tablet
Minimum widths:
- 320;
- 360;
- 375;
- 390;
- 400;
- 430;
- 768;
- 1024.

At each relevant width verify:
- no viewport horizontal overflow;
- menu opens/closes correctly;
- no clipped controls;
- no overlapping text;
- Mailboxes record remains compact;
- table/list actions remain reachable;
- forms fit and labels/errors remain associated;
- reader body is usable without nested unusable scroll traps.

## Functional regression matrix

- login success/failure/lockout;
- logout POST;
- admin-only access;
- non-admin mailbox visibility;
- mailbox create unique/reserved validation;
- mailbox enable/disable;
- mailbox delete confirmation and permission;
- user create/edit/delete restrictions;
- mailbox assignment persistence;
- message search/read/attachment filtering;
- read on open;
- mark unread;
- message soft delete;
- attachment access/missing attachment;
- browser live update insertion;
- audit events for key actions.

## Operational matrix

- Django deploy check;
- no migration drift;
- mailserver schema verification;
- Maildir storage verification;
- Postfix lookup contract;
- ingestion dry-run;
- Gunicorn socket/app verification;
- live/ready endpoints;
- Postfix/Dovecot/Nginx config tests;
- service activity;
- deterministic archive verification;
- upgrade archive migration comparison;
- backup checksums;
- rollback snapshot checksums.

## Security/static matrix

- Ruff;
- Bandit;
- dependency audit;
- sanitizer XSS fixture set;
- path confinement tests;
- permission/object authorization tests;
- CSRF contracts;
- security headers/CSP tests if present in existing suite;
- no secrets in source/log output;
- documentation/forensic inventory checks.

## Final real-world matrix

At production acceptance:

1. external plain/normal email;
2. external HTML-rich email from a modern provider/template;
3. external message with attachment when practical;
4. verify receipt through server chain;
5. verify Inbox live update;
6. verify reader readability;
7. verify attachment download;
8. verify mark unread/read behavior;
9. verify non-admin access boundary where applicable;
10. observe service/app logs for a bounded interval.
