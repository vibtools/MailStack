# Existing Postfix integration contract

Do not replace the live MySQL/MariaDB Postfix maps. The server already uses:

```text
virtual_mailbox_domains = mysql:/etc/postfix/mysql-virtual-domains.cf
virtual_mailbox_maps = mysql:/etc/postfix/mysql-virtual-mailboxes.cf
virtual_alias_maps = mysql:/etc/postfix/mysql-virtual-aliases.cf
virtual_transport = lmtp:unix:private/dovecot-lmtp
virtual_mailbox_base = /var/vmail
```

The application creates or enables/disables rows in the existing `vibmail.mailboxes` table. The existing `vibmail.postfix_virtual_mailboxes` view remains the only Postfix mailbox lookup source.
