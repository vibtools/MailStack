user = {{POSTFIX_DB_USER}}
password = {{POSTFIX_DB_PASSWORD}}
hosts = 127.0.0.1
dbname = {{MAIL_DB_NAME}}
query = SELECT destination FROM postfix_virtual_aliases WHERE source = LOWER('%s')
