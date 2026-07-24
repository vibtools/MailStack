# Maildir Ingestion

```bash
python manage.py ingest_maildir --once
python manage.py ingest_maildir --watch --interval 15
python manage.py ingest_maildir --once --mailbox mailbox1
python manage.py ingest_maildir --once --dry-run
python manage.py rebuild_mail_index --mailbox mailbox1
```

The worker scans application mailboxes in `Maildir/new` and `Maildir/cur`, ignores `tmp`, rejects escaped paths, limits message/attachment sizes, and never moves or deletes source files. It parses with Python's standard email package, records warnings per message, and continues after malformed input.

Identity combines mailbox, relative source key, raw SHA-256, and internal UUID. The same source file is not indexed twice, while identical bytes delivered under separate source filenames remain separate deliveries. A non-blocking filesystem lock rejects a second worker.
