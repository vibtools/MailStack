from django.db import migrations

POSTGRES_SQL = """
CREATE VIEW postfix_virtual_mailboxes AS
SELECT lower(email_address) AS email,
       maildir_relative_path AS maildir_path
FROM mailboxes_mailbox
WHERE status = 'active'
  AND local_part = lower(local_part)
  AND length(local_part) BETWEEN 1 AND 64
  AND lower(email_address) = local_part || '@vibmail.my'
  AND maildir_relative_path = 'vibmail.my/' || local_part || '/Maildir/'
  AND local_part ~ '^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$'
  AND position('..' in local_part) = 0
"""

SQLITE_SQL = """
CREATE VIEW postfix_virtual_mailboxes AS
SELECT lower(email_address) AS email,
       maildir_relative_path AS maildir_path
FROM mailboxes_mailbox
WHERE status = 'active'
  AND local_part = lower(local_part)
  AND length(local_part) BETWEEN 1 AND 64
  AND lower(email_address) = local_part || '@vibmail.my'
  AND maildir_relative_path = 'vibmail.my/' || local_part || '/Maildir/'
  AND local_part NOT GLOB '*[^a-z0-9._-]*'
  AND substr(local_part, 1, 1) GLOB '[a-z0-9]'
  AND substr(local_part, -1, 1) GLOB '[a-z0-9]'
  AND instr(local_part, '..') = 0
"""


def create_view(_apps, schema_editor):
    # Production MariaDB uses the pre-existing vibmail.postfix_virtual_mailboxes view.
    # Never create, replace, or drop that mail-server-owned view from application migrations.
    if schema_editor.connection.vendor == "mysql":
        return
    schema_editor.execute("DROP VIEW IF EXISTS postfix_virtual_mailboxes")
    sql = POSTGRES_SQL if schema_editor.connection.vendor == "postgresql" else SQLITE_SQL
    schema_editor.execute(sql)


def drop_view(_apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        schema_editor.execute("DROP VIEW IF EXISTS postfix_virtual_mailboxes")


class Migration(migrations.Migration):
    dependencies = [("mailboxes", "0001_initial")]
    operations = [migrations.RunPython(create_view, reverse_code=drop_view)]
