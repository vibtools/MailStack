# Administrator Guide

Sign in at `https://app.vibmail.my` using the account created by `create_initial_admin`. Public registration and email-based password reset do not exist.

Create mailboxes by entering only the local part. The domain is fixed to `vibmail.my`. Reserved operational names are blocked in the UI. A reviewed system address can be created from the server with `python manage.py create_system_mailbox <name> --confirm`.

Disabling a mailbox preserves its messages and files but removes it from the Postfix lookup view. Re-enable it to restore inbound eligibility. There is no permanent deletion in Phase 1.

Use inbox filters for sender/subject, read state, and attachments. HTML opens in an isolated safe view. Attachments are not antivirus scanned. Change the password from the application; recover it locally with `python manage.py changepassword <username>`.
