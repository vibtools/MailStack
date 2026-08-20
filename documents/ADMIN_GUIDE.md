---
document_id: admin-guide
title: MailStack Administrator Guide
document_type: admin-guide
audience: mailstack-administrators
status: active
version: 1.3.4-rc.2
last_reviewed: 2026-08-18
---

# MailStack administrator guide

## Administrator role

Administrators can view all maintained mailboxes, create and manage ordinary users, assign mailbox
memberships, control deletion permissions, create mailboxes, enable or disable mailboxes, and
review operational health. The authenticated shell displays **User management** only when the
existing administrator authorization check passes. Administrator accounts are intentionally not
editable or deletable through the ordinary user-management screen.

## User management

Open **User management** and select **Add user**. Set a unique case-insensitive username, active
state, initial password, mailbox assignments, and optional message or mailbox deletion permissions.
Passwords are set during account creation and cannot be changed through the current MailStack UI.

Editing an ordinary user can change the username, active state, mailbox assignments, and deletion
permissions. Deleting an ordinary user removes the login account and assignments while preserving
mailboxes, received messages, attachments, and audit history. The current administrator cannot
delete itself, and the interface does not delete administrator accounts.

## Mailbox administration

Use **Create mailbox** to provision the application record and Maildir. Assign active ordinary
users or leave the mailbox administrator-only. From **Mailboxes**, administrators can enable or
disable an address. Disabled or deleted addresses must reject new delivery according to the
Postfix recipient contract. Deletion requires full-address confirmation, performs a soft deletion,
and leaves the local part permanently reserved.

Review assignments before granting destructive permissions. Ordinary users can see only assigned
mailboxes. Message and mailbox deletion controls remain hidden unless policy allows them.

## Existing-message body repair

After deploying a reader/sanitizer correction, already-indexed messages are repaired only through the
maintained management command; normal duplicate ingestion does not rewrite an existing message body.
Run a bounded dry-run first:

```text
python manage.py repair_message_bodies --dry-run --limit 500
```

After reviewing the result counters and errors, explicitly authorize the bounded mutation:

```text
python manage.py repair_message_bodies --confirm-repair --limit 500
```

Use `--mailbox <local-part>` or `--message <uuid>` for targeted repair. The command verifies the
associated Maildir source and updates only parser-derived body fields. It must not delete/re-ingest
messages or recreate attachments, and it preserves UUID, mailbox membership, read/unread state,
deletion state, source identity and attachment records.

## Operational health

The administrator dashboard reports ingestion heartbeat, mail-storage accessibility, and database
connectivity. Server-side verification should also use the maintained health and verification
scripts, systemd service status, and journal logs. The one-shot dry-run verifier can run while the
live ingestion worker remains active and does not update its heartbeat. After deployment, verify external delivery to
`postmaster@DOMAIN` and `abuse@DOMAIN`, Maildir creation, ingestion, browser visibility, and backup
creation before onboarding users.

## Security boundaries

The shared shell uses only local CSS, JavaScript, logo, and SVG icon assets. Logout remains a
CSRF-protected POST action; hidden mobile navigation is removed from interaction; no planned route
or control is exposed by the shell. Preserve these boundaries in every subsequent page patch.

MailStack is receive-only and must not be treated as an outbound relay, public registration system,
or general-purpose webmail service. Preserve object-scoped authorization, sanitized HTML,
attachment path confinement, protected environment files, least-privilege database roles, and the
legacy runtime identifiers documented by the project. Never publish credentials, Maildir data,
attachments, database dumps, backups, certificates, private keys, or unsanitized screenshots.

Before production use, complete clean Ubuntu 24.04 VPS acceptance, TLS and DNS validation, real
SMTP/LMTP delivery tests, backup/restore acceptance, and security review. Use the documented repair
or upgrade path rather than running the clean installer over an unreviewed existing mail stack. A
reviewed repair preserves an existing valid administrator and bootstrap mailboxes, creates only
missing bootstrap objects, and never silently resets an administrator password.
