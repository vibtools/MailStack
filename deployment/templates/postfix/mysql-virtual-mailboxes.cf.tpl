user = {{POSTFIX_DB_USER}}
password = {{POSTFIX_DB_PASSWORD}}
hosts = 127.0.0.1
dbname = {{MAIL_DB_NAME}}
query = SELECT maildir FROM postfix_virtual_mailboxes WHERE email = LOWER('%s')
