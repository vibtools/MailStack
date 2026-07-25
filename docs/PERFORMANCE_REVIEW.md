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

- SQLite uses WAL mode, full synchronous durability, a busy timeout, indexed rate-limit/status paths, short immediate transactions, and deterministic connection closure after every context.
- Gunicorn request recycling limits long-lived worker growth.

## Operational characteristics

- The reference architecture is intentionally single-node.
- Ingestion polling defaults to 15 seconds; live browser polling and visible mailbox limits are configurable.
- Backup creates a short delivery/application maintenance window to guarantee consistent Maildir/database state.

## Performance gate result

No regression was observed in the local Windows suite; 195 tests passed, one capability-based symbolic-link case was skipped, and the suite completed in approximately 7.4 seconds with 94.99 percent coverage. No production load benchmark was executed. Before high-volume use, benchmark realistic message size, attachment mix, mailbox count, concurrency, disk latency, and MariaDB buffer settings on target hardware.

## Release packaging

Deterministic source packaging stores already-compressed PNG, JPEG, GIF, and web-font assets
without redundant DEFLATE work. Text and source files remain compressed. This preserves archive
reproducibility while preventing the UI reference set from causing unnecessary CI CPU time.

## PHASE-002 shared-shell review

The runtime change adds one local stylesheet, one small local icon sprite, and a local copy of the
existing logo. It adds no framework, package, external font, network dependency, or client-side
rendering layer. The shell uses CSS Grid/Flexbox, bounded transitions, one responsive media-query
listener, and event listeners attached once during `DOMContentLoaded`. The desktop collapse
preference stores one boolean string in browser local storage. Existing live polling frequency and
payload behavior are unchanged.

No production browser performance benchmark has been executed. Page-level rendering and large-list
performance remain subject to the later page phases and staging acceptance.
