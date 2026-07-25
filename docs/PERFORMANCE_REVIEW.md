# Performance review — MailStack 1.3.0

## Application and web serving

- Gunicorn defaults to three workers with two threads each and a 60-second request timeout; worker count is installer-configurable.
- Nginx serves static assets directly and uses a Unix socket for the Django application.
- Protected attachments use an internal Nginx route, avoiding Python streaming when enabled by the application contract.
- Static assets use immutable cache headers.

## Ingestion and storage

- The ingestion worker scans Maildir with `os.scandir`, streams file hashing in 1 MiB chunks, and processes database records transactionally.
- Duplicate source keys and content identifiers prevent repeated indexing.
- Mailbox iteration uses Django queryset iterators to avoid loading the complete mailbox set into memory.
- Attachment files are stored outside the public web root.
- Oversized messages are recorded without loading their content into memory.

## Database behavior

- Mailbox, status, timestamps, membership, counters, message identifiers, read-state, and audit paths retain database indexes/constraints from the audited application.
- Production connections use bounded persistent connections and read-committed isolation.
- Postfix lookup views and underlying tables use indexed domain, email, source, and active fields.

## Public contact service

- SQLite uses WAL mode, full synchronous durability, a busy timeout, indexed rate-limit/status paths, and short immediate transactions.
- Gunicorn request recycling limits long-lived worker growth.

## Operational characteristics

- The reference architecture is intentionally single-node.
- Ingestion polling defaults to 15 seconds; live browser polling and visible mailbox limits are configurable.
- Backup creates a short delivery/application maintenance window to guarantee consistent Maildir/database state.

## Performance gate result

No regression was observed in the automated suite; 189 tests completed in approximately 4.2 seconds in the audit container. No production load benchmark was executed. Before high-volume use, benchmark realistic message size, attachment mix, mailbox count, concurrency, disk latency, and MariaDB buffer settings on target hardware.

## Release packaging

Deterministic source packaging stores already-compressed PNG, JPEG, GIF, and web-font assets
without redundant DEFLATE work. Text and source files remain compressed. This preserves archive
reproducibility while preventing the UI reference set from causing unnecessary CI CPU time.
