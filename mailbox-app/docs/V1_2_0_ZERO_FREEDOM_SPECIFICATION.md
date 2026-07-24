# VIB MAIL v1.2.0 — TEAM ACCESS, LIVE INBOX & BRANDING UPDATE
## ZERO-FREEDOM MEGA MASTER SPECIFICATION

**Target release:** `v1.2.0`  
**Authoritative baseline:** `VIB_MAIL_MVP_PHASE2_MARIADB_COMPAT_v1.1.2` **plus all verified live production hotfixes currently active on `app.vibmail.my`**  
**Production hosts:** `app.vibmail.my`, `mail.vibmail.my`  
**Mail domain:** `vibmail.my`  
**Application mode:** Private, receive-only team mailbox platform  
**Database:** MariaDB (`vibmail` mail-server source of truth + `vibmail_app` Django application database)

---

# 1. ABSOLUTE EXECUTION DIRECTIVE

Read every baseline file completely before changing any code.

Treat this document as the authoritative specification for MailStack v1.2.0.

Execute only the features and corrections defined in this document.

The developer has zero freedom to remove, simplify, reinterpret, postpone, mock, stub, or partially implement any requirement.

All existing approved features must remain operational unless this document explicitly replaces their behavior.

No working feature may regress.

No production data may be lost.

No existing mailbox, Maildir message, indexed message, attachment, audit log, user session policy, Postfix/Dovecot integration, MariaDB schema contract, TLS configuration, Nginx security control, deployment permission fix, or service-hardening control may be damaged.

The final delivery must be complete, tested, audited, versioned, migration-safe, rollback-safe, and production-ready.

---

# 2. BASELINE CONTRACT

## 2.1 Verified package baseline

Use the following release as the code baseline:

- Package: `VIB_MAIL_MVP_PHASE2_MARIADB_COMPAT_v1.1.2.zip`
- SHA-256: `87ef5b8ead2ca61ab82a34cbf34199cd499b89ab3dab3dc48c75268f94ff231f`
- Manifest version: `1.1.2`
- Manifest files: `197`
- Package integrity: PASS
- Manifest integrity: PASS
- ZIP integrity: PASS

The baseline audit reported:

- 152 tests passed
- 96.28% test coverage
- Ruff: PASS
- Bandit: PASS
- Django system check: PASS
- Migration drift check: PASS
- Shell syntax: PASS
- ZIP integrity and source cleanliness: PASS

All baseline tests must continue to pass after the update.

## 2.2 Mandatory live-production hotfix baseline

The raw v1.1.2 ZIP is not by itself the complete production baseline.

Before implementing v1.2.0, import and preserve the currently verified live Nginx corrections:

1. Do not combine `include proxy_params;` with duplicate explicit proxy headers.
2. Send exactly one `Host` header to Django.
3. Preserve explicit:
   - `proxy_set_header Host $host;`
   - `proxy_set_header X-Real-IP $remote_addr;`
   - `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`
   - `proxy_set_header X-Forwarded-Proto https;`
4. Use listener options compatible with the existing `mail.vibmail.my` site:
   - `listen 443 ssl;`
   - `listen [::]:443 ssl;`
5. Preserve the HTTP ACME challenge route:
   - `/.well-known/acme-challenge/`
6. Preserve HTTP-to-HTTPS redirect behavior.
7. Preserve the valid `app.vibmail.my` Let’s Encrypt certificate.
8. Preserve Nginx-to-Gunicorn-to-Django behavior without duplicated `HTTP_HOST`.
9. Preserve the current protected attachment route, static route, health route, and security headers.

The developer must compare the uploaded package config with the live production config and merge the live fixes into the v1.2.0 source before any release candidate is built.

## 2.3 Existing functionality that must remain intact

Preserve all approved baseline behavior, including:

- Receive-only mail architecture
- Postfix delivery
- Dovecot LMTP delivery
- Maildir storage under `/var/vmail`
- Existing `vibmail` mail-server database
- Existing `vibmail_app` Django database
- Cross-schema mailbox synchronization
- Existing mailbox creation
- Mailbox enable/disable
- Maildir ingestion
- Duplicate-ingestion protection
- Inbox filtering
- Sender and subject search
- Read/unread filtering
- Attachment filtering
- Safe HTML rendering
- Plain-text rendering
- Attachment access through protected delivery
- Login rate limiting
- Audit logging
- Security headers
- CSRF protection
- Session protection
- Responsive layout
- Health endpoints
- Backup, restore, rollback, verification, and deployment scripts
- Least-privilege `vmail` runtime
- Virtualenv `root:vmail` permission normalization
- MariaDB compatibility
- Existing production emails and mailboxes

---

# 3. RELEASE OBJECTIVES

Implement exactly these update groups:

1. **Admin and ordinary-user separation**
2. **User-management functions**
3. **Per-user mailbox isolation and controlled sharing**
4. **Admin-controlled deletion permissions**
5. **Strict duplicate-mailbox prevention**
6. **Live inbox updates without page reload**
7. **New-email notification**
8. **Automatic read state when opening a message**
9. **Site name and footer branding update**

---

# 4. UPDATE 1 — USER MANAGEMENT AND ACCESS CONTROL

## 4.1 Role model

Implement two application roles:

### Administrator

An administrator:

- Is an active Django superuser/staff administrator.
- Can access every mailbox and every message.
- Can create, edit, and delete ordinary users.
- Can assign one or more mailboxes to one or more users.
- Can view and change ordinary-user deletion permissions.
- Can create mailboxes.
- Can enable, disable, and operationally delete mailboxes.
- Can delete messages.
- Can see all application-wide counters and health information.
- Cannot accidentally delete the currently logged-in administrator account.
- Cannot delete the last active administrator.

### Ordinary user

An ordinary user:

- Is an authenticated, active, non-staff, non-superuser account.
- Can see only mailboxes explicitly assigned to that account.
- Can see only messages belonging to assigned mailboxes.
- Cannot see another user’s mailbox through lists, dashboard cards, search, direct UUID URLs, safe-HTML URLs, attachment URLs, live-update APIs, or manipulated requests.
- Can continue using a shared account with multiple human team members when the administrator chooses that operating model.
- Can also be given an individual account when the administrator chooses per-member access.
- Cannot manage users.
- Cannot assign mailboxes.
- Cannot grant permissions.
- Cannot change or update a password.
- Cannot delete messages or mailboxes unless the administrator explicitly grants the required permission.
- Even with deletion permission, can act only on mailboxes assigned to that user.

## 4.2 Do not replace Django’s user model

Do not introduce a mid-project custom `AUTH_USER_MODEL`.

Preserve the existing Django authentication tables.

Add a dedicated application policy/profile model linked one-to-one to the existing Django user.

Recommended production model:

`UserAccessPolicy`

Required fields:

- `user` — OneToOneField to the existing Django user
- `can_delete_messages` — Boolean, default `False`
- `can_delete_mailboxes` — Boolean, default `False`
- `created_at`
- `updated_at`

Administrators are authorized by `is_superuser`/`is_staff`; ordinary-user destructive capabilities are controlled by the policy fields.

Create policies automatically and safely for existing and new ordinary users.

Do not rely on template hiding as authorization.

Every permission must be enforced server-side.

## 4.3 Mailbox assignment model

Add an explicit many-to-many assignment model.

Recommended production model:

`MailboxMembership`

Required fields:

- `user`
- `mailbox`
- `assigned_by` — nullable administrator reference
- `created_at`

Required constraints:

- Unique constraint on `(user, mailbox)`
- Indexed lookup by user
- Indexed lookup by mailbox

Required behavior:

- One user may access multiple mailboxes.
- One mailbox may be shared with multiple users.
- A mailbox with no ordinary-user assignment remains administrator-only.
- Administrators always have global access and do not require membership rows.
- Existing mailboxes remain intact.
- Existing administrators retain access to all existing mailboxes.
- No existing mailbox or message may be deleted during migration.

## 4.4 Central authorization service

Create one central authorization/queryset layer and use it everywhere.

Required reusable functions or equivalent services:

- `accessible_mailboxes(user)`
- `accessible_messages(user)`
- `user_can_access_mailbox(user, mailbox)`
- `user_can_delete_message(user, message)`
- `user_can_delete_mailbox(user, mailbox)`
- `require_admin(user)`

Rules must not be duplicated inconsistently across views.

All object lookups must be scoped through authorized querysets.

Unauthorized object requests must return `404` to avoid leaking object existence.

## 4.5 User-management UI

Add an administrator-only User Management area.

Required screens:

### User list

Display:

- Username
- Active/inactive state
- Administrator/ordinary-user role
- Number of assigned mailboxes
- Delete-message permission
- Delete-mailbox permission
- Created date
- Last login
- Edit action
- Delete action

### User creation

Administrator can create an ordinary user with:

- Unique username
- Initial password
- Active state
- Assigned mailboxes
- Delete-message permission
- Delete-mailbox permission

The password must:

- Use existing Django password validators
- Never be logged
- Never be stored in plain text
- Never be returned by an API
- Never appear in audit details
- Be entered through password-type fields
- Be confirmed during creation

### User edit

Administrator can edit:

- Username, subject to uniqueness validation
- Active/inactive state
- Assigned mailboxes
- Delete-message permission
- Delete-mailbox permission

Password editing or password reset must not be present on the edit screen.

### User deletion

Administrator can delete an ordinary user.

Required safeguards:

- Only POST is allowed.
- CSRF is mandatory.
- A confirmation screen or explicit confirmation form is mandatory.
- The current logged-in administrator cannot delete itself.
- The final active administrator cannot be deleted.
- Deleting a user must not delete any mailbox, Maildir file, message, or attachment.
- Mailbox assignment rows for the deleted user may be removed safely.
- Existing audit records must remain.
- The delete action must be audited.
- Existing sessions for the deleted user must become unusable.

## 4.6 Password-change prohibition

Remove ordinary-user password-change capability from the web application.

Required changes:

- Remove the Password navigation item.
- Remove the public authenticated password-change route.
- Remove or retire the password-change view.
- Remove the password-change form from ordinary-user access.
- Remove the password-change template from navigable application behavior.
- Do not add public password reset.
- Do not add email-based password reset.
- Do not expose Django admin password-management pages through this application.
- User creation may set the initial password.
- No ordinary user may change or update that password through the application.
- No hidden alternate endpoint may bypass this rule.

Existing login, logout, rate limiting, password hashing, and session security must remain intact.

## 4.7 Dashboard and navigation separation

Administrator navigation must include:

- Dashboard
- Mailboxes
- Create mailbox
- User management
- Log out

Ordinary-user navigation must include only authorized functions:

- Dashboard
- Assigned mailboxes
- Create mailbox if the existing creation function remains available
- Log out

Do not show administrative links to ordinary users.

Server-side authorization remains mandatory even when links are hidden.

## 4.8 Preserve mailbox creation

Preserve the existing mailbox-creation feature.

Required assignment behavior:

- If an administrator creates a mailbox, the administrator may assign it to one or more ordinary users.
- The administrator may leave it unassigned, making it administrator-only.
- If an ordinary user creates a mailbox, automatically assign the new mailbox to that user.
- An ordinary user cannot assign the mailbox to another user.
- The mailbox must use the fixed `vibmail.my` domain.
- Existing reserved-name validation must remain.
- Existing Maildir provisioning must remain.
- Existing cross-schema mail-server creation must remain.
- Existing audit logging must remain.

## 4.9 Duplicate mailbox prohibition

Every mailbox must remain unique.

Enforce uniqueness across:

- Application `local_part`
- Application full email address
- Mail-server mailbox table
- Active alias source conflicts
- Case variants
- Concurrent requests

Examples that must be treated as duplicates:

- `sales`
- `Sales`
- `SALES`
- `sales@vibmail.my`

Required result:

- Exactly one concurrent creation attempt may succeed.
- All competing duplicate attempts must fail cleanly.
- No orphan application row may remain.
- No orphan mail-server row may remain.
- No unsafe or conflicting Maildir may remain.
- The existing successful mailbox must remain operational.

---

# 5. CONTROLLED DELETE BEHAVIOR

## 5.1 Permission separation

Use separate permissions:

- `can_delete_messages`
- `can_delete_mailboxes`

Do not combine them into one broad permission.

Administrators always possess both capabilities.

Ordinary users default to neither capability.

## 5.2 Message delete

Add a delete action for a received message.

Required authorization:

- Administrator, or
- Ordinary user with `can_delete_messages=True`
- The message must belong to a mailbox assigned to that ordinary user

Required implementation:

- Use controlled soft deletion in v1.2.0.
- Add `deleted_at` and `deleted_by` or an equivalent auditable soft-delete design.
- Deleted messages must disappear from normal inbox, search, dashboard, counters, live updates, and direct detail access.
- The source Maildir file must not be removed in this release.
- The database row must remain so ingestion cannot recreate the deleted message.
- Attachments must remain inaccessible through normal application routes after message deletion.
- Deletion must be idempotent.
- Deletion must be audited.
- Counters must be recalculated or changed atomically.
- A user without permission must receive no delete control and must be denied server-side.
- Use POST and CSRF.
- Use a confirmation step.

Physical purge is outside this release and must not be added.

## 5.3 Mailbox/email-address delete

Add a controlled operational delete action for a mailbox/email address.

Required authorization:

- Administrator, or
- Ordinary user with `can_delete_mailboxes=True`
- The mailbox must be assigned to that ordinary user

Required implementation:

- Use soft deletion/deprovisioning, not physical data destruction.
- Add a deleted state or deleted timestamp.
- Disable the mailbox in the authoritative `vibmail` mail-server table.
- Remove it from active Postfix recipient lookup behavior.
- Stop future inbound delivery for the deleted address.
- Hide it from normal mailbox lists and dashboard counters.
- Hide all contained messages from normal access.
- Preserve Maildir files, application rows, message rows, and attachment files.
- Preserve the local part permanently as reserved.
- A deleted local part must not be recreated as a new mailbox.
- Existing uniqueness constraints must continue to block reuse.
- Deletion must be idempotent, transactional where possible, and audited.
- Use POST and CSRF.
- Use a strong confirmation step showing the full email address.

Physical Maildir/database purge is outside this release and must not be added.

## 5.4 Existing enable/disable behavior

Preserve existing enable/disable behavior separately from delete.

Required states:

- Active
- Disabled
- Deleted

Meaning:

- Active: receives mail and is visible.
- Disabled: does not receive mail, remains visible and can be re-enabled.
- Deleted: does not receive mail, hidden from normal use, data preserved, address reserved.

Do not reinterpret Disabled as Deleted.

---

# 6. UPDATE 2 — LIVE MAILBOX AND MESSAGE UPDATES

## 6.1 Required user experience

The following must update without a full page reload:

- Newly received message appears in the correct inbox.
- Mailbox total-message count updates.
- Mailbox unread count updates.
- Dashboard total-message count updates.
- Dashboard unread count updates.
- Last-received timestamp updates.
- Recent-message list updates.
- Mailbox-list counters update where displayed.

## 6.2 Architecture requirement

Implement authenticated same-origin near-real-time updates using a lightweight polling/event-feed API compatible with the existing Gunicorn/Django deployment.

Do not introduce Redis, Celery, a message broker, Node.js, or a separate WebSocket stack unless this specification is formally amended.

Recommended behavior:

- Poll interval: approximately 5 seconds while the relevant page is visible.
- Pause or reduce polling while the browser tab is hidden.
- Prevent overlapping requests.
- Use exponential backoff on temporary failures.
- Resume normal polling after recovery.
- Use `Cache-Control: no-store`.
- Require authentication.
- Return data only for mailboxes authorized for the current user.
- Use an incremental cursor based on a stable monotonic value such as message primary key/event ID.
- Do not use only `received_at` as the cursor because email dates may be old or malformed.
- Do not return deleted messages.
- Do not expose another user’s mailbox identifiers, counts, senders, subjects, or timestamps.

## 6.3 Live API response

The authenticated endpoint must return only necessary fields.

Expected categories:

- Current authorized summary counters
- Updated authorized mailbox counters
- Newly indexed authorized messages after the supplied cursor
- New cursor
- Server timestamp

Do not return message bodies or attachment data through the live-update endpoint.

Apply a sensible result limit and cursor continuation behavior to prevent unbounded payloads.

## 6.4 DOM update behavior

Update the current page without destroying user state.

Preserve:

- Active filters
- Search input
- Pagination context
- Scroll position where possible
- Open tabs
- Form input
- Current message view

Do not insert a new message into a filtered list when it does not satisfy the current filter.

If the user is on a later pagination page, update counters and notification but do not corrupt pagination ordering.

Escape all inserted text.

Do not use unsafe `innerHTML` with email-controlled content.

## 6.5 New-email notification

When a new authorized message is received:

Mandatory:

- Show an in-application notification/toast.
- The toast must identify the mailbox.
- The toast may show safely escaped sender and subject.
- The toast must link to the authorized message detail or inbox.
- The notification must be accessible through an ARIA live region.
- The same message must not generate repeated toasts on every poll.

Optional browser notification:

- Provide an explicit “Enable notifications” user action.
- Request browser notification permission only after user interaction.
- If permission is granted, display a browser notification.
- If permission is denied or unsupported, the in-app toast must still work.
- Do not require a service worker in this release.
- Do not leak unauthorized message information.
- Deduplicate across tabs using `BroadcastChannel` or a safe local-storage fallback.

## 6.6 Ingestion compatibility

Preserve the existing ingestion service and idempotency.

The live-update feature must consume database state after successful ingestion.

Do not make the browser responsible for mail ingestion.

Do not make the page poll the Maildir directly.

The existing ingestion service remains the only indexing authority.

---

# 7. AUTOMATIC READ BEHAVIOR

## 7.1 Auto-read on open

Opening a message detail page must automatically mark that message as read.

Required behavior:

- Authorization is checked first.
- The transition is idempotent.
- Only an unread message is changed.
- The mailbox unread counter is updated atomically and never becomes negative.
- Concurrent opens do not double-decrement the counter.
- The read transition is audited only when the state actually changes.
- Dashboard and mailbox counters reflect the change.
- The user does not need to click “Mark read.”

## 7.2 Preserve mark-unread functionality

Preserve the existing ability to mark a read message as unread.

UI behavior:

- Remove the “Mark read” button for unread messages.
- Keep a “Mark unread” action after a message is read.
- The mark-unread action remains POST-only with CSRF.
- Counters update safely and idempotently.

## 7.3 Live counter synchronization

After auto-read or mark-unread:

- Update the visible unread count without a page reload where applicable.
- Other open tabs must receive the corrected count on their next authorized live poll.
- No unauthorized user may observe the update.

---

# 8. UPDATE 3 — SITE NAME AND FOOTER

## 8.1 Site name

Change all user-facing product branding from:

`MailStack MVP`

to:

`MailStack`

Update:

- Browser page titles
- Header brand
- Login page
- Dashboard
- Mailbox pages
- Message pages
- Context processor
- Documentation where it describes the current user-facing name

Do not rename Python packages, database names, service names, filesystem paths, or deployment identities merely for cosmetic branding.

## 8.2 Footer

Use this exact footer meaning, with a dynamic current year:

`© <year> MailStack. Service provided by vib.tools. Authorized team use only — not for public access.`

Requirements:

- Visible on login and authenticated pages.
- Responsive.
- Accessible.
- `vib.tools` may be plain text or a safe HTTPS link.
- Do not add public registration or public marketing language.

---

# 9. OBJECT-LEVEL SECURITY REQUIREMENTS

Every route must be reviewed.

At minimum, secure:

- Dashboard
- Mailbox list
- Mailbox create
- Mailbox status change
- Mailbox delete
- Inbox
- Message detail
- Safe HTML
- Read/unread state
- Message delete
- Attachment download
- Live-update endpoint
- User list
- User create
- User edit
- User delete

Specific baseline defect to close:

The existing safe-HTML route accepts only a message UUID and currently lacks mailbox ownership scoping. The updated implementation must verify that the authenticated user can access the message’s mailbox before returning any HTML.

Attachment access must also remain fully scoped.

Never depend only on UUID unpredictability.

---

# 10. DATABASE AND MIGRATION REQUIREMENTS

## 10.1 Migration safety

Create forward-only, deterministic Django migrations compatible with MariaDB 10.11 and the supported MySQL/MariaDB test matrix.

Do not modify the existing `vibmail` schema through Django migrations.

Application migrations operate only in `vibmail_app`.

Cross-schema operational mailbox state changes may continue through reviewed service-layer SQL on the existing MariaDB connection.

## 10.2 Existing-data migration

Required outcomes:

- Existing administrator remains administrator.
- Existing users remain valid.
- Existing mailboxes remain intact.
- Existing messages remain intact.
- Existing attachments remain intact.
- Existing counters remain valid.
- Existing Maildir paths remain unchanged.
- No existing mailbox must require a membership row for administrator access.
- Existing ordinary users, if any, must not automatically gain access to all mailboxes.
- User-policy rows must be created safely with both deletion permissions defaulting to false.
- No password is changed.
- No session secret is exposed.

## 10.3 Query performance

Add indexes required for:

- Membership lookup by user/mailbox
- Active/non-deleted mailbox filtering
- Active/non-deleted message filtering
- Live cursor lookup
- Unread counts for authorized mailboxes

Avoid N+1 queries in:

- Dashboard
- Mailbox list
- User list
- Inbox
- Live-update endpoint

Use `select_related`, `prefetch_related`, annotations, and bounded queries appropriately.

---

# 11. AUDIT LOG REQUIREMENTS

Audit at minimum:

- User created
- User edited
- User deleted
- User activated/deactivated
- Mailbox assignment added
- Mailbox assignment removed
- Delete permissions granted/revoked
- Mailbox created
- Mailbox enabled/disabled
- Mailbox deleted
- Message viewed
- Message auto-marked read
- Message marked unread
- Message deleted
- Attachment downloaded
- Unauthorized destructive attempt where appropriate
- Login/logout events already present

Never audit:

- Plain-text passwords
- Password hashes
- Session IDs
- CSRF tokens
- Secrets
- Full attachment contents
- Full email bodies

---

# 12. SECURITY REVIEW

Perform and close findings for:

- IDOR / broken object-level authorization
- Privilege escalation
- Horizontal data leakage
- Vertical data leakage
- Direct URL access
- Safe-HTML access bypass
- Attachment access bypass
- Live-API information leakage
- CSRF on destructive actions
- Password exposure
- Session continuation after user deletion
- Concurrent duplicate mailbox creation
- SQL injection
- Template injection
- Stored XSS
- Unsafe JavaScript DOM insertion
- Path traversal
- Maildir symlink attacks
- Attachment traversal
- Insecure soft-delete filters
- Accidental deleted-data exposure
- Audit-log secret leakage
- Race conditions in unread counters
- Race conditions in mailbox status/delete
- Rate-limit regression
- Nginx proxy-header regression
- Security-header regression

Run Bandit and dependency review.

No known high- or critical-severity issue may remain.

---

# 13. PERFORMANCE AND RELIABILITY REVIEW

Verify:

- Live polling does not create overlapping requests.
- Live API uses bounded response sizes.
- Hidden tabs reduce unnecessary polling.
- Database queries remain indexed.
- Dashboard remains responsive.
- Inbox remains responsive with large message counts.
- User list remains paginated.
- Mailbox list remains paginated.
- No long-running request blocks Gunicorn workers.
- No WebSocket requirement is introduced.
- Ingestion remains independent of browser activity.
- Gunicorn, ingestion, Nginx, Postfix, Dovecot, and MariaDB restart cleanly.
- Service shutdown remains deterministic.
- No memory leak is introduced by repeated polling.
- Browser notification deduplication works across tabs.
- Automatic read state remains correct under concurrent opens.

---

# 14. MANDATORY TEST MATRIX

## 14.1 Regression gate

All existing baseline tests must pass unchanged or be deliberately updated only where the specification changes expected behavior.

The final suite must contain more tests than the baseline suite.

Coverage must remain at least 90%, with no critical authorization branch untested.

## 14.2 Role and isolation tests

Test:

1. Administrator sees every mailbox.
2. Ordinary user sees assigned mailbox.
3. Ordinary user does not see unassigned mailbox.
4. Ordinary user cannot access another mailbox by UUID.
5. Ordinary user cannot access another message by UUID.
6. Ordinary user cannot access another message safe-HTML route.
7. Ordinary user cannot download another user’s attachment.
8. Ordinary user cannot receive another mailbox’s live events.
9. Shared mailbox assigned to two users is visible to both.
10. One shared user account works normally for multiple human team members.
11. Unassigned mailbox is administrator-only.
12. Dashboard totals are scoped for ordinary users.
13. Administrator totals remain global.

## 14.3 User-management tests

Test:

- Admin can list users.
- Admin can create user.
- Username uniqueness.
- Password validation.
- Password never appears in audit log.
- Admin can edit allowed fields.
- Admin can assign and unassign mailboxes.
- Admin can grant and revoke each delete permission independently.
- Ordinary user cannot open user-management routes.
- Ordinary user cannot call user-management POST endpoints.
- Admin can delete ordinary user.
- User deletion preserves mailboxes/messages.
- Current admin cannot delete itself.
- Last active admin cannot be deleted.
- Deleted user session becomes invalid.
- No password-change link exists.
- Password-change route is unavailable.
- No public reset route exists.

## 14.4 Mailbox tests

Test:

- Admin creates unassigned mailbox.
- Admin creates assigned mailbox.
- Ordinary user creates mailbox and is auto-assigned.
- Fixed-domain validation remains.
- Reserved names remain blocked.
- Case-insensitive duplicate creation fails.
- Duplicate full email creation fails.
- Mail-server duplicate fails.
- Alias-source conflict fails.
- Concurrent duplicate attempts produce exactly one mailbox.
- No orphan Maildir/database rows after failure.
- Enable/disable remains functional.
- Deleted mailbox becomes non-receiving.
- Deleted mailbox is hidden.
- Deleted mailbox data remains preserved.
- Deleted local part cannot be recreated.
- User without delete permission cannot delete mailbox.
- User with permission can delete only assigned mailbox.

## 14.5 Message tests

Test:

- Opening unread message automatically marks read.
- Opening read message is idempotent.
- Concurrent opens do not produce a negative or incorrect unread count.
- Mark unread still works.
- User without message-delete permission cannot delete.
- User with permission can delete only messages from assigned mailboxes.
- Deleted message is hidden from inbox, search, dashboard, counters, live API, detail, safe HTML, and attachments.
- Deleted message is not re-ingested.
- Administrator can delete any message.
- Audit records are correct.

## 14.6 Live-update tests

Test:

- New ingested authorized message appears without reload.
- Total and unread counts update without reload.
- Dashboard recent-message list updates.
- Mailbox-list counts update.
- In-app toast appears once.
- Duplicate polls do not duplicate the message or toast.
- Another tab does not produce repeated notifications.
- Browser-notification denial does not break in-app toast.
- Unauthorized message never appears.
- Active filters are preserved.
- Pagination is not corrupted.
- Polling backoff works after temporary failure.
- Polling resumes.
- Endpoint requires authentication.
- Endpoint uses no-store caching.
- Payload is bounded.

## 14.7 Deployment tests

Test:

- Fresh installation.
- Upgrade from v1.1.2.
- Upgrade with existing mailboxes/messages.
- MariaDB migration.
- `manage.py check --deploy`.
- Migration drift check.
- Static collection.
- Gunicorn import as `vmail`.
- Ingestion as `vmail`.
- Nginx config test.
- HTTPS response.
- Login response.
- Health live/ready.
- Static asset response.
- `.env` exposure returns 404.
- ACME challenge delivery.
- HTTP-to-HTTPS redirect.
- Real external inbound email.
- Live browser update.
- Auto-read.
- User isolation.
- Rollback rehearsal.

---

# 15. UI AND RESPONSIVENESS

Preserve the existing responsive design.

Support at minimum:

- 320px mobile width
- 375px
- 768px
- 1024px
- 1366px
- 1920px
- 2560px

No field, button, table, menu, notification, badge, modal, or confirmation control may be clipped, overlapped, hidden, or unreachable.

User-management tables must reflow or scroll safely.

Notification toasts must not block essential controls.

Keyboard navigation and focus visibility must remain functional.

Use semantic labels and accessible status messaging.

---

# 16. DEPLOYMENT AND ROLLBACK

## 16.1 No direct experimental editing on production

Do not develop directly inside `/opt/vibmail/app`.

Create an isolated release workspace.

## 16.2 Pre-deployment backup

Before upgrade, capture:

- Application source
- `vibmail_app` database
- Required `vibmail` mail-server tables/schema state
- Nginx site configuration
- Systemd service files
- Environment-file metadata without disclosing secrets
- Static files
- Attachments metadata
- Maildir inventory/count
- Current migration plan
- Current service status
- Current mailbox/message counts
- Current live Nginx hotfix config

## 16.3 Deployment order

1. Verify release hash and manifest.
2. Verify backup.
3. Stop only services required by the approved deployment plan.
4. Stage source.
5. Install pinned dependencies.
6. Normalize virtualenv permissions.
7. Run least-privilege import gate.
8. Run migration pre-check.
9. Apply migrations.
10. Verify mail-server schema.
11. Synchronize mailboxes safely.
12. Verify Maildir.
13. Verify Postfix contract.
14. Collect static files.
15. Run Django deploy checks.
16. Run test smoke gates.
17. Restart/reload application services.
18. Validate Nginx.
19. Reload Nginx only after successful config test.
20. Execute browser and real-inbound acceptance tests.
21. Audit logs.
22. Roll back immediately if any mandatory gate fails.

## 16.4 Rollback

Rollback must restore:

- Previous source
- Previous application database state
- Previous Nginx configuration
- Previous systemd files if changed
- Previous static assets
- Service availability

Rollback must not delete mail received during the deployment window.

Mailbox/Maildir data protection is mandatory.

---

# 17. REQUIRED DELIVERY PACKAGE

Deliver:

1. Full production-ready source tree
2. Versioned ZIP: `VIB_MAIL_v1.2.0_TEAM_ACCESS_LIVE_INBOX.zip`
3. SHA-256 file
4. Complete manifest with file sizes and hashes
5. Changelog
6. Architecture update
7. Database migration documentation
8. Upgrade guide from v1.1.2
9. Rollback guide
10. Administrator guide
11. Ordinary-user guide
12. User-management guide
13. Live-notification behavior guide
14. Security audit report
15. Performance audit report
16. Test report
17. Coverage report
18. Deployment verification report
19. Known-issues report, which must state “None” only when true
20. Clean package with no secrets, caches, logs, database dumps, Maildir messages, generated artifacts, or environment files

---

# 18. FINAL FORENSIC AUDIT

Before delivery:

1. Build.
2. Run the complete test suite.
3. Run lint.
4. Run Bandit.
5. Run Django checks.
6. Run migration drift check.
7. Run shell syntax checks.
8. Verify package cleanliness.
9. Verify manifest.
10. Verify ZIP hash.
11. Audit authorization route by route.
12. Audit destructive actions.
13. Audit real-time endpoint leakage.
14. Audit password-change prohibition.
15. Audit database migration.
16. Audit Nginx live-hotfix preservation.
17. Audit MariaDB compatibility.
18. Audit performance.
19. Audit rollback.
20. Re-run all checks after every fix.

Do not deliver after finding an unresolved defect.

Repeat fix, test, and audit until all mandatory gates pass.

---

# 19. FINAL ACCEPTANCE GATE

The release status may be **PASS** only when all of the following are true:

- All requested features are complete.
- All existing approved features remain functional.
- Administrator and ordinary-user roles are separated.
- Ordinary users see only assigned mailboxes.
- Shared-mailbox assignment works.
- Shared user accounts remain possible.
- User add/edit/delete works.
- Password change/update is unavailable to ordinary users.
- Delete permissions are controlled by the administrator.
- Unauthorized deletion is impossible.
- Duplicate mailbox creation is impossible.
- Live inbox updates work without reload.
- New-email notification works.
- Auto-read works on message open.
- Mark-unread remains functional.
- Branding is changed to MailStack.
- Footer wording is correct.
- Existing emails and Maildirs are preserved.
- Real inbound mail still works.
- Postfix/Dovecot remain operational.
- Nginx duplicate-host defect does not return.
- ACME and HTTPS remain operational.
- No authorization leak exists.
- No secret is exposed.
- No migration error exists.
- No known runtime error exists.
- No unfinished code, placeholder, stub, or TODO remains.
- Rollback is verified.
- Final package integrity passes.

If any item fails, final status must be **FAIL**, not partial pass.

---

# 20. PROHIBITED ACTIONS

Do not:

- Remove receive-only architecture.
- Add outbound sending.
- Add public registration.
- Add public password reset.
- Add user self-service password change.
- Replace MariaDB.
- Modify the existing mail-server schema through Django migrations.
- Remove Postfix/Dovecot integration.
- Change existing Maildir locations.
- Physically purge deleted messages/mailboxes in this release.
- Reuse deleted mailbox local parts.
- Expose all mailboxes to ordinary users.
- Trust UUID secrecy as authorization.
- Add unapproved Redis/Celery/WebSocket infrastructure.
- Remove security headers.
- Reintroduce duplicate Nginx proxy headers.
- Remove the ACME challenge route.
- Hard-code secrets.
- Log passwords or tokens.
- Skip tests.
- Reduce test coverage below the required threshold.
- Deliver partial code.
- Deliver pseudo-code.
- Deliver placeholders.
- Claim production readiness without real verification.

---

# FINAL IMPLEMENTATION COMMAND

Implement MailStack v1.2.0 exactly according to this specification, using the verified v1.1.2 release plus the current live production Nginx hotfix as the immutable baseline.

Preserve all existing approved functionality.

Complete the implementation, migrations, tests, security audit, performance audit, deployment assets, documentation, release packaging, manifest, hashes, upgrade verification, real-inbound verification, and rollback verification.

Deliver only after every mandatory acceptance gate passes.
