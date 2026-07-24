# MailStack administrator user-management guide

Administrators can create ordinary users, activate/deactivate them, assign shared mailboxes, and grant message-delete and mailbox-delete permissions independently.

A mailbox may be assigned to multiple users. A user may have multiple mailboxes. An unassigned mailbox is administrator-only. Deleting a user removes the login and assignments but preserves mailboxes, messages, attachments, and audit history.

Initial passwords are set only during user creation. Passwords are validated and hashed by Django and are never written to audit logs. The edit screen intentionally has no password field.
