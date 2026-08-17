---
document_id: user-manual
title: MailStack User Manual
document_type: user-manual
audience: mailbox-users
status: active
version: 1.3.0-rc.2
last_reviewed: 2026-08-17
---

# MailStack user manual

## Overview

MailStack is a private, receive-only shared team inbox. Authorized users can view assigned
mailboxes, search received messages, inspect sanitized email content, download permitted
attachments, and receive browser notifications for new mail. Administrators control user
accounts, mailbox assignments, mailbox status, and destructive permissions.

MailStack does not provide public registration, outbound email sending, SMTP submission, IMAP, or
POP3 in this release.

## Sign in

Open the application hostname supplied by the administrator and enter the assigned username and
password. Accounts are created by an administrator; users cannot self-register or change their
password inside MailStack. Repeated failed sign-in attempts are rate limited. Authenticated pages use a shared sidebar and top
bar. On desktop, the sidebar may be collapsed; on tablet or mobile, use the menu button to open the
navigation drawer. Open the account menu in the top bar and use **Log out** when leaving a shared
device.

## Dashboard

The dashboard summarizes the mailboxes available to the signed-in user, including active and
disabled mailbox counts, received and unread totals, the last received time, recent messages, and
recent mailboxes. Administrators also see ingestion, mail-storage, and database health indicators.
Dashboard and mailbox counters update through authenticated live polling. The active navigation
item is visually highlighted and announced as the current page. The shell also shows a persistent
receive-only notice so users do not mistake MailStack for an outbound webmail client.

## Mailboxes

Open **Mailboxes** to list only the mailboxes assigned to the current user. Search by local part or
full address and filter by active or disabled status. Select **Open inbox** to read messages, or
select an address to copy it.

Any authenticated user can create a mailbox. A normal user is automatically assigned to the new
mailbox. An administrator can assign one or more active ordinary users during creation or leave the
mailbox administrator-only. Local parts accept lowercase letters, numbers, dots, underscores, and
hyphens, up to 64 characters. Reserved system names cannot be created. Deleted addresses remain
reserved and cannot be recreated accidentally.

## Messages

Inside a mailbox, search by sender or subject and filter by read state or attachment presence.
Opening a message marks it read. Use **Mark unread** to return it to the unread state. The message
screen shows sender, recipients, received time, size, parse status, plain text, sanitized HTML, and
available attachments.

Sanitized HTML is displayed in a sandboxed frame with remote and active content blocked. A delete
button appears only when the current account has permission. Message deletion removes the indexed
application record from normal use while preserving the source email according to the current
retention design.

## Notifications

When the browser supports notifications, select **Enable notifications** in the Mail section of the
sidebar and approve the browser prompt. Notifications are generated only for newly indexed messages that the
current user is authorized to access. Browser permissions can be changed later in the browser site
settings.

## Limits and safety

Attachments are delivered as downloads with path confinement and authorization checks, but this
release does not claim antivirus scanning. Treat unexpected files as untrusted and scan them with
approved endpoint security before opening. MailStack is receive-only; reply or forwarding actions
must be performed through another approved mail system. Access is limited to assigned mailboxes,
and unauthorized objects return a not-found or permission response.

For account, mailbox assignment, or password issues, contact the MailStack administrator. For
service outages, provide the time, affected mailbox, and visible error without sending message
content, credentials, attachments, or other sensitive data through an unapproved channel.
