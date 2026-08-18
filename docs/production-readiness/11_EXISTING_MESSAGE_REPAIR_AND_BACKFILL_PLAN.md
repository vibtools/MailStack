# Existing Message Repair and Backfill Plan

## Problem

The v1.3.3 ingestion service identifies an already-indexed message by mailbox + Maildir `source_file_key` and
returns `duplicate` before parsing it again. Therefore existing rows with a bad `sanitized_html_body` will not
be repaired merely by deploying a corrected parser.

## Safety objective

Repair parser-derived presentation data from the preserved original Maildir source **without deleting messages,
changing user state, or re-creating database identities**.

## Allowed source of truth

The existing original Maildir message file referenced by each message's mailbox and `source_file_key` is the
repair source. It is already preserved by MailStack's receive-only architecture.

## Fields that must remain unchanged

Unless a separately evidenced defect requires a narrower exception:

- message primary key;
- message UUID;
- mailbox foreign key;
- `source_file_key`;
- existing source identity contract;
- `is_read`;
- `deleted_at`;
- `deleted_by`;
- created timestamp;
- mailbox memberships/permissions;
- attachment rows and files;
- audit identity/history.

## Candidate parser-derived fields eligible for reviewed update

Exact implementation must compare current model/parser behavior before coding. Expected candidates include:

- sender name/address when parser behavior explicitly requires correction;
- recipients/CC;
- subject;
- received date only if parser correction requires it;
- `text_body`;
- `sanitized_html_body`;
- parse status/warning.

For this production-readiness defect, the preferred narrow mutation is body/render-related fields plus
parse-status/warning only. Broader metadata rewrites require evidence.

## Required command behavior

Proposed management-command characteristics:

- explicit command name related to message resanitization/repair;
- `--dry-run`;
- `--mailbox <local-part or address>` targeting;
- optional message UUID targeting;
- optional bounded `--limit`/batch size;
- clear counters: scanned, eligible, changed, unchanged, skipped, missing-source, warning, error;
- non-zero exit when blocking errors occur;
- no deletion of source files;
- no creation of duplicate Message rows;
- transaction safety per message or appropriately bounded batch;
- audit/log summary without dumping full raw email content.

## Eligibility strategy

Prefer an evidence-based eligibility rule rather than rewriting every message blindly. Possible verified
criteria may include:

- stored HTML contains recognizable leaked CSS patterns from stripped style blocks;
- parser version/repair marker if an implementation introduces one without schema change;
- owner-selected mailbox/message scope;
- explicit all-message mode only after dry-run counts are reviewed.

The final criterion must be determined by tests against real affected and unaffected source messages.

## Pre-production test sequence

1. create fixture message with leaked style-block CSS under old behavior;
2. ingest/store it using controlled test state;
3. run repair dry-run and verify no mutation;
4. run repair mutation;
5. verify sanitized body becomes readable;
6. verify UUID/read/delete/source identity unchanged;
7. verify attachments unchanged;
8. run repair a second time;
9. verify idempotent `unchanged` result;
10. test missing source file and malformed source behavior.

## Production execution sequence

1. confirm PHASE-006 release is deployed and healthy;
2. take/confirm normal pre-change operational backup according to existing policy;
3. run repair dry-run and save counters/output;
4. review count of eligible/affected messages;
5. run bounded mutation;
6. verify database/message counts unchanged;
7. open representative previously broken messages in browser;
8. verify read/unread/deleted states are preserved;
9. verify attachment access;
10. rerun dry-run/repair to demonstrate idempotence;
11. record final repair counts in PHASE-006 completion log.

## Prohibited repair strategies

- delete database rows and re-ingest;
- delete or move original Maildir mail solely to trigger ingestion;
- reset read/unread state;
- reset soft-delete state;
- create new message UUIDs for repaired records;
- blanket allow CSS/JavaScript/remote assets to avoid sanitizer complexity;
- restore MariaDB from backup merely to repair presentation data.
