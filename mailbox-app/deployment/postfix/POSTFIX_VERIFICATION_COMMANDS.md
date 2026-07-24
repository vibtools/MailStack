# Postfix verification commands

```bash
postmap -q example.com mysql:/etc/postfix/mysql-virtual-domains.cf
postmap -q team@example.com mysql:/etc/postfix/mysql-virtual-mailboxes.cf
postmap -q definitely-unknown@example.com mysql:/etc/postfix/mysql-virtual-mailboxes.cf
postfix check
postconf -n
```

Expected: domain and mailbox return values; unknown mailbox returns no value. Do not print map passwords.
