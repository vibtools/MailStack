---
document_id: phase-007-multi-domain-mailbox-and-dns
title: Multi-domain Mailboxes and DNS Verification
document_type: phase
audience: administrators-users-and-maintainers
status: active
version: 1.3.5.3
last_reviewed: 2026-09-18
phase_id: PHASE-007
---

# PHASE-007: Multi-domain mailboxes and DNS verification

## Objective

Promote MailStack from one settings-defined mail domain to a controlled multi-domain receive-only
platform. Administrators will manage domains from the Admin Panel, verify the required DNS records,
enable or disable delivery safely, and select an active domain when creating a mailbox.

The implementation must reuse the existing Postfix/Dovecot MariaDB domain contract and preserve the
current domain, mailbox addresses, Maildir paths, authorization rules, receive-only boundary, upgrade
path, and rollback behavior.

## Scope

This phase includes:

- A first-class Django `Domain` record with normalized unique domain names, status, verification
  state, DNS check timestamps, and generated verification metadata where needed.
- An admin-only Domains page with a compact table showing domain, delivery status, DNS status, mailbox
  count, last check, and actions.
- Domain create, edit, enable/disable, manual DNS verification, and safe removal/archive behavior.
- Required DNS instructions rendered on the domain detail or add screen, including record type, host,
  value, priority, and current verification result.
- Mailbox creation with an active, DNS-ready domain selector and an address preview.
- Per-domain uniqueness for mailbox local parts and per-domain Maildir paths such as
  `<storage-root>/<domain>/<local-part>/Maildir/`.
- Parameterization of the existing mail-server integration so domain lookup and mailbox provisioning
  use the selected domain instead of `settings.MAIL_DOMAIN`.
- A data migration that creates the current configured domain first and attaches every existing
  mailbox to it without changing an address or Maildir path.
- Focused tests, operational verification commands, documentation, and release-contract updates.

This phase does not add outbound mail, SMTP submission, DKIM signing, aliases, catch-all routing,
per-domain user authorization, scheduled DNS polling, or automatic DNS provider changes. DKIM and
scheduled checks remain follow-up work after the receive-only multi-domain path is qualified.

## User-facing changes

Administrators gain a compact Domains page under Management with domain CRUD, DNS instructions,
manual verification, mailbox counts, and enable/disable controls. Mailbox creation gains a verified
active-domain selector and a server-generated full-address preview. Existing mailboxes retain their
current addresses, paths, messages, memberships, and permissions.

## Data and migration design

### Domain model

The application-owned domain record should contain at minimum:

- `uuid`
- normalized lowercase `name`
- `status`: `active` or `disabled`
- `verification_status`: `pending`, `verified`, or `failed`
- `last_checked_at`, `created_at`, and `updated_at`
- stored verification/error details that do not contain credentials

The domain name must be validated as a DNS hostname, reject IP literals and unsafe labels, and be
unique case-insensitively. The application record must map to the existing mail-server domain row;
creation must fail closed if the external row cannot be created or activated.

### Mailbox migration

`Mailbox` will gain a required foreign key to `Domain`. The migration sequence is:

1. Create the application domain table.
2. Insert the current `settings.MAIL_DOMAIN` as the default active/verified domain.
3. Add a nullable mailbox foreign key temporarily.
4. Backfill every existing mailbox to the default domain.
5. Preserve each existing `email_address` and `maildir_relative_path` exactly.
6. Add the per-domain/local-part unique constraint and make the foreign key required.
7. Retain the existing case-insensitive full-address uniqueness contract.

The old global local-part uniqueness constraint must be replaced only after the backfill succeeds.
The migration must be reversible at the schema level, and a separate operational rollback note must
explain that newly-created secondary-domain mailboxes require explicit data review before reverting
to a single-domain release.

## Admin UI and workflow

### Domain list

Add **Domains** under the admin Management navigation. The page must be compact and operationally
scannable:

| Domain      | Delivery | DNS      | Mailboxes | Last checked | Actions              |
| ----------- | -------- | -------- | --------: | ------------ | -------------------- |
| example.com | Active   | Verified |        12 | 2 min ago    | Check, Edit, Disable |

Actions must be explicit, CSRF-protected POST operations where state changes occur. Disable must stop
new provisioning and mail delivery for that domain while preserving existing Maildir data and message
history. Hard deletion is prohibited when mailboxes or messages exist; use disabled/archive behavior
instead.

### Add/edit/check flow

The add form validates and normalizes the domain, creates or reconciles its external mail-server
domain row, and displays the exact DNS records required by the deployment. The page must show a
clear state for each check:

- `Pending`: domain has not been checked.
- `Verified`: required records match the expected values.
- `Failed`: one or more required records are missing or incorrect, with a safe diagnostic.
- `Disabled`: delivery and mailbox creation are blocked regardless of previous verification.

DNS checking must use a bounded resolver with timeouts, no shell interpolation, and deterministic
record normalization. It must not require DNS provider credentials. The initial required checks are
MX for the domain and the mail host A/AAAA target; SPF is displayed and reported as recommended
unless the deployment contract explicitly makes it required. Checks must never expose internal
resolver details or secrets in the UI.

## Mailbox and mail-server behavior

Mailbox creation must require an active, DNS-ready domain and show a live address preview such as
`support@example.com`. Uniqueness is `(domain, local_part)` case-insensitively; the same local part
may exist in different domains. The generated email address and Maildir relative path are derived
server-side and cannot be trusted from posted form data.

The existing mail-server service must accept an explicit domain object/name for all domain-sensitive
operations, including mailbox existence, domain lookup, mailbox creation, activation, schema checks,
Postfix rows, and listing. No domain-sensitive operation may silently fall back to the global
`settings.MAIL_DOMAIN` after this phase. SQL identifiers remain strictly configured/validated, and
SQL values remain parameterized.

Provisioning remains transactional and lock-protected:

1. Validate the active/verified domain and local part.
2. Acquire the existing mailbox provisioning lock using a domain-safe lock key.
3. Create the domain-scoped Maildir safely.
4. Create the external mail-server mailbox with the selected `domain_id`.
5. Save the Django mailbox and memberships atomically.
6. Clean up newly-created filesystem paths on failure and record an audit event.

Disable/enable must update the external mailbox rows consistently. Domain disable must reject new
mailbox provisioning and prevent active delivery; it must not delete data or silently disable other
domains.

## Compatibility

The existing configured domain is the migration baseline and remains the default domain for current
users. Existing URLs, mailbox UUIDs, addresses, memberships, message records, attachments, audit
history, ingestion source keys, backups, and Maildir contents must remain valid.

The top-bar configured domain display must become a selected/default-domain or domain-count display
without misleading users into believing the application is still single-domain. Existing settings
remain accepted during the transition; after migration, `MAIL_DOMAIN` is used only as bootstrap and
fallback configuration, not as the source of mailbox identity.

Deployment must include:

- migration ordering and preflight checks;
- external mail-schema compatibility checks;
- a dry-run/reconciliation command for existing domains and mailboxes;
- upgrade and rollback documentation;
- a post-deploy verification sequence for DNS, SMTP delivery, Maildir creation, ingestion, and UI;
- explicit backup requirements before migration.

## Verification

Implementation is complete only when all of the following pass:

- Domain model, normalization, status transitions, and migration tests.
- Existing mailbox migration tests proving unchanged addresses, paths, UUIDs, memberships, and
  message references.
- Admin authorization tests for list/create/edit/check/enable/disable/archive actions.
- DNS resolver tests for valid, missing, malformed, timeout, mismatch, and safe-error cases.
- Mailbox form tests for domain selection, disabled/unverified rejection, address preview, and
  per-domain duplicate handling.
- Maildir path confinement tests covering same local parts across multiple domains and traversal
  rejection.
- Mail-server contract tests proving the selected domain ID is used and failure rolls back safely.
- Postfix/Dovecot schema and external delivery verification tests.
- Full Django tests, migration-drift checks, Ruff, Bandit, dependency checks, documentation/design
  gates, UI foundation tests, forensic audit, and deterministic inventory checks.
- Manual acceptance on a clean Ubuntu 24.04 environment with two real test domains, including DNS
  propagation delay, delivery to both domains, mailbox disable behavior, ingestion, backup, and
  rollback evidence.

Blocking production failures include accepting mail for an unverified/disabled domain, cross-domain
mailbox collision, changed existing Maildir paths, orphaned external mail-server rows, unsafe DNS
resolver behavior, authorization bypass, or a migration that cannot be safely interrupted and
reconciled.

## How to use

Administrators will open **Management > Domains**, add a domain, publish the displayed DNS records,
run **Check DNS**, and enable the domain only after the required checks are verified. During mailbox
creation, select the verified active domain, enter the local part, confirm the generated address, and
assign users as usual.

Operators should verify both domains externally after deployment:

- query MX and mail-host A/AAAA records;
- send a controlled message to each test mailbox;
- confirm Maildir creation and ingestion;
- confirm the message appears only in the intended mailbox;
- disable the domain and verify new delivery/provisioning is rejected without deleting stored data.

## Implementation status

The first production vertical slice is active. It includes the `Domain` model and migration
backfill, safe hostname validation, bounded dependency-free MX/A/AAAA verification, admin domain
CRUD/check/toggle routes, verified-domain mailbox selection, per-domain local-part uniqueness and
Maildir paths, and explicit domain propagation through provisioning, ingestion, and mail-server
reconciliation. Existing configured-domain mailboxes are backfilled without changing their address
or relative path. SPF remains displayed as recommended and scheduled checks, aliases, DKIM, and
provider automation remain out of scope.

## Documentation impact

The phase is active for implementation qualification. Before release, update the canonical
administrator and user guides with domain management, DNS setup, mailbox creation, disable behavior,
backup, and rollback instructions. Release inventory, forensic-audit, and source-archive tooling
excludes the local-only `reference/` directory so private reference material cannot create CI drift
or enter a public source archive. Synchronize the documentation index and manifest, then regenerate
and check the forensic inventory before any release or commit gate.
