from django.db import migrations


POSTGRES_SQL = """
CREATE VIEW postfix_virtual_mailboxes AS
SELECT lower(email_address) AS email,
       maildir_relative_path AS maildir_path
FROM mailboxes_mailbox
WHERE status = 'active'
  AND deleted_at IS NULL
  AND local_part = lower(local_part)
  AND length(local_part) BETWEEN 1 AND 64
  AND lower(email_address) LIKE local_part || '@%'
  AND maildir_relative_path = split_part(lower(email_address), '@', 2) || '/' || local_part || '/Maildir/'
  AND local_part ~ '^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$'
  AND position('..' in local_part) = 0
"""

SQLITE_SQL = """
CREATE VIEW postfix_virtual_mailboxes AS
SELECT lower(email_address) AS email,
       maildir_relative_path AS maildir_path
FROM mailboxes_mailbox
WHERE status = 'active'
  AND deleted_at IS NULL
  AND local_part = lower(local_part)
  AND length(local_part) BETWEEN 1 AND 64
  AND instr(lower(email_address), '@') > 1
  AND lower(email_address) LIKE local_part || '@%'
  AND maildir_relative_path = substr(lower(email_address), instr(lower(email_address), '@') + 1)
      || '/' || local_part || '/Maildir/'
  AND local_part NOT GLOB '*[^a-z0-9._-]*'
  AND substr(local_part, 1, 1) GLOB '[a-z0-9]'
  AND substr(local_part, -1, 1) GLOB '[a-z0-9]'
  AND instr(local_part, '..') = 0
"""


def replace_view(_apps, schema_editor):
    if schema_editor.connection.vendor == "mysql":
        return
    schema_editor.execute("DROP VIEW IF EXISTS postfix_virtual_mailboxes")
    sql = POSTGRES_SQL if schema_editor.connection.vendor == "postgresql" else SQLITE_SQL
    schema_editor.execute(sql)


def restore_legacy_view(_apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        schema_editor.execute("DROP VIEW IF EXISTS postfix_virtual_mailboxes")


class Migration(migrations.Migration):
    dependencies = [("mailboxes", "0003_mailboxmembership_and_more")]
    operations = [migrations.RunPython(replace_view, restore_legacy_view)]
