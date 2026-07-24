# Postfix Integration

Apply only during Phase 2.

The application migration creates:

```sql
SELECT email, maildir_path
FROM postfix_virtual_mailboxes
WHERE email = lower('<recipient>');
```

For `team@example.com`, the expected active result is `example.com/team/Maildir/`. Disabling the mailbox removes it from this view without deleting Maildir or indexed content. Postfix must then reject new mail for that address.

Use the assets under `deployment/postfix/`. Replace the lookup password securely, grant only view `SELECT`, test with `postmap -q`, and verify that ports 465/587 and SASL submission are not enabled by this integration.
