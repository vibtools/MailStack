---
document_id: how-to-use
title: How to Use MailStack
document_type: how-to
audience: mailbox-users-and-administrators
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# How to use MailStack

## Sign in

1. Open the configured MailStack application URL.
2. Enter the administrator-provided username and password.
3. Select **Sign in**.
4. Confirm that the dashboard shows only the mailboxes assigned to the account.

There is no public registration or in-application password-change workflow in this release.

## Create a mailbox

1. Select **Create mailbox**.
2. Enter the local part that will appear before the configured mail domain.
3. Administrators may select active ordinary users to assign; ordinary users are assigned to their
   own new mailbox automatically.
4. Select **Create mailbox and Maildir**.
5. Confirm that the address appears in **Mailboxes** with an active status.

A deleted or previously reserved address cannot be reused. Administrators can disable or enable a
mailbox from the mailbox list.

## Read and filter messages

1. Open **Mailboxes** and select **Open inbox**.
2. Search by sender address or subject when needed.
3. Use the read-state filter for **Unread** or **Read** messages.
4. Use the attachment filter for messages with or without attachments.
5. Open a message to view its metadata, plain text, safe HTML, and attachments.
6. Select **Mark unread** when the message should return to the unread queue.

Opening a message marks it read. Live updates are available on an unfiltered first inbox page and
on the dashboard.

## Download an attachment

1. Open the authorized message.
2. Review the attachment filename, detected MIME type, and size.
3. Select **Download**.
4. Scan the downloaded file with approved endpoint protection before opening it.

MailStack enforces mailbox and attachment authorization, protected paths, private caching, and
forced-download headers. The interface explicitly states that attachments are not antivirus
scanned by MailStack.

## Enable browser notifications

1. Select **Enable notifications** in the authenticated navigation.
2. Approve the browser permission prompt.
3. Leave MailStack open in a supported browser to receive new-message notifications.
4. To disable notifications later, change the permission in the browser site settings.

Notifications are scoped to messages the signed-in user can access.

## Delete permitted content

A delete action is visible only when the administrator has granted the required permission.
Message deletion preserves the source email under the current retention design. Mailbox deletion
requires typing the full address, soft-deletes the mailbox, and permanently reserves the address.
Use destructive actions only after confirming retention and operational requirements.
