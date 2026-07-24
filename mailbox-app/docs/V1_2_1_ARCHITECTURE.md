# MailStack 1.2.1 architecture

## Identity and authorization

Django's existing user model remains unchanged. `UserAccessPolicy` stores granular destructive permissions. `MailboxMembership` provides many-to-many user/mailbox assignment. Administrators are active staff or superusers and always have global access.

All mailbox and message routes use centralized object-scoped querysets in `apps/core/access.py`. Unauthorized object requests return 404 where object existence must not be disclosed.

## Data deletion

Message and mailbox deletion are soft operations. Message rows and Maildir source files remain so ingestion cannot recreate deleted messages. Deleted mailboxes are disabled in the authoritative mail-server database, hidden from normal application access, and their local parts remain permanently reserved.

## Live updates

Authenticated same-origin polling uses `/messages/live/`. The initial bootstrap establishes a monotonic message-ID cursor without notifying for historical messages. Later bounded requests return authorized summary counters, bounded mailbox state, and up to the configured number of new messages. Browser code uses text nodes rather than unsafe HTML insertion.

## Read state

Opening an authorized message marks it read inside a database transaction. The message and mailbox are locked and counters are recalculated from non-deleted messages. Repeated/concurrent opens are idempotent. Mark-unread remains POST/CSRF protected.

## Mail flow

Postfix and Dovecot remain independent of the web request path. LMTP writes Maildir data; the ingestion service indexes it into `vibmail_app`; browser polling reads only indexed database state.
