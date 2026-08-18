# Production-Readiness Forensic Report

## Executive disposition

MailStack `v1.3.3` is successfully installed and operational at the server/core level, but the application is
**not yet production-ready from an end-user UI/message-reading perspective**.

### Current high-level disposition

| Area | Status | Production meaning |
|---|---|---|
| v1.3.3 installation identity | PASS | Correct published source is deployed |
| Database / migration readiness | PASS | No pending migration issue observed |
| Postfix / Dovecot / Nginx config | PASS | Core mail/web configuration checks passed |
| Core health endpoints | PASS | Live and ready endpoints returned healthy state |
| Application verifier | PASS | Maintained verification passed after upgrade |
| Backup / rollback evidence | PASS | Upgrade backup and rollback snapshots verified |
| HTML email reader | **BLOCKER** | Raw CSS appears in message body; mail can be unreadable |
| Existing affected messages | **BLOCKER** | Persisted sanitized bodies will not self-heal |
| Mailbox compactness | FAIL | Desktop/mobile density does not meet approved target |
| Responsive shell | FAIL | Collapsed/mobile presentation remains inconsistent |
| Authenticated footer | FAIL | Public/promotional links leak into internal workspace |
| Gunicorn log finding | OPEN | `Control server error: [Errno 30] Read-only file system` observed |
| Final real inbound E2E after UI corrections | PENDING | Must be rerun after defects are fixed |

## Evidence basis

This report combines:

- the frozen MailStack v1.3.3 source baseline;
- the live upgrade and post-upgrade verification outputs;
- supplied desktop and mobile screenshots;
- VibTools Web UI v2.1.2 design documentation;
- Licora v5.5.0 UI implementation/audit documentation as a structural implementation reference.

The reference products are used for **structure, typography, density, responsive patterns and component
discipline only**. MailStack retains its own branding, light theme and product color system.

## Finding PR-001 — HTML email sanitizer leaks CSS text

**Severity:** Critical / BLOCKER
**State:** [CONFIRMED]

Current `mailbox-app/apps/ingestion/parser.py` uses Bleach with `strip=True`. The safe-tag set excludes
`style`, while the cleaner is allowed to strip disallowed tags. In the supplied Harpoon email screenshot,
CSS rules such as `#outlook a`, `.ReadMsgBody`, `.ExternalClass`, and table/content rules are visibly emitted
as message text.

The current sanitizer also rejects the `style` attribute. That restriction is security-conscious, but the
combination means complex marketing/transactional emails can lose intended layout while style-block text
remains user-visible.

### Required correction

- remove `head`, `style`, `script`, `noscript`, metadata and other non-body active/style content **with their
  contents where appropriate** before the normal safe-HTML sanitization pass;
- preserve the existing deny-by-default sanitizer posture;
- do not enable JavaScript, event attributes, arbitrary CSS or unrestricted remote content;
- maintain safe link protocol validation and attachment isolation;
- add fixtures reproducing the supplied Harpoon-style email and similar style-heavy HTML emails;
- verify rendered output contains readable content and **zero raw style-block CSS**.

## Finding PR-002 — Already-indexed messages will not automatically repair

**Severity:** Critical / BLOCKER
**State:** [CONFIRMED]

Current ingestion checks `(mailbox, source_file_key)` first and returns `duplicate` for an already-indexed
Maildir item. Therefore, changing only the parser/sanitizer fixes **future ingestion** but does not rewrite the
stored `sanitized_html_body` for existing messages.

### Required correction

Implement a controlled, idempotent repair/backfill command that:

- reads the original Maildir source already associated with each message;
- re-parses using the corrected parser;
- updates only approved parser-derived body/metadata fields;
- preserves message UUID, database identity, read/unread state, deletion state, mailbox membership, audit
  identity, source key and attachment records unless an explicitly reviewed attachment repair is required;
- supports dry-run, mailbox targeting, bounded batch size and clear result counters;
- records warnings/errors without deleting source mail;
- can be safely re-run.

See `11_EXISTING_MESSAGE_REPAIR_AND_BACKFILL_PLAN.md`.

## Finding PR-003 — Visible protected-rendering banner is intrusive

**Severity:** Major UX
**State:** [CONFIRMED]

The message template prints `Protected rendering · remote and active content are blocked.` above every HTML
message. The underlying security controls are valid, but a permanent warning strip consumes prime reading
space and makes normal mail feel like an error state.

### Required correction

- remove the permanent banner from the normal reading path, or reduce it to an unobtrusive info affordance if
  the owner later chooses to retain one;
- **retain** HTML sanitization, iframe sandboxing, no-referrer behavior, attachment authorization and active
  content blocking;
- security state must remain testable even if it is no longer visually loud.

## Finding PR-004 — Remote image stripping creates broken-image residue

**Severity:** Major UX
**State:** [CONFIRMED from source + screenshot]

The sanitizer only allows image `src` values beginning with approved `data:image/...;base64,` prefixes.
External image sources are rejected. The screenshot shows a broken image/`intercom` residue at the bottom of
the message.

### Required correction

Do not simply allow unrestricted remote images. Instead, ensure rejected remote images do not render as broken
UI. Safe options include removing the unusable image node while preserving meaningful alt text, or rendering a
compact blocked-image placeholder. The implementation must not introduce remote tracking fetches by default.

## Finding PR-005 — Shared UI geometry is materially larger than the reference contract

**Severity:** Major UX
**State:** [CONFIRMED]

Current MailStack foundation values include:

- base UI font size: `1rem` / approximately `16px`;
- sidebar width: `256px`;
- collapsed sidebar width: `80px`;
- topbar height: `72px`.

VibTools Web UI v2.1.2 compact structural references define:

- primary UI text: `13px`;
- sidebar width: `196px`;
- topbar height: `44px`;
- small/medium buttons: `28px` / `32px`;
- small/medium inputs: `30px` / `34px`;
- compact card padding: `10px 12px`;
- small/control/card radii: `6px / 8px / 12px`;
- flat, border-driven cards rather than broad decorative elevation.

### Required correction

Create a MailStack compact token mapping that adopts the **structural scale** while preserving MailStack light
colors, semantic colors and branding. Page code must consume shared tokens/components rather than inventing new
sizes per screen.

## Finding PR-006 — Mailboxes desktop list is too heavy

**Severity:** Major UX
**State:** [CONFIRMED]

The current Mailboxes page is a seven-column traditional table with separate `Open inbox`, `Disable`, and
`Delete` actions. It is visually heavy for large mailbox counts and exposes too many simultaneous action
controls.

### Required correction

- reduce row height and typography;
- make mailbox address the clear primary item;
- compact Status / Messages / Unread / Last received presentation;
- demote Created metadata;
- consolidate row actions into a compact shared action area/menu while preserving permissions and POST/CSRF
  contracts;
- preserve search/status filter behavior and pagination.

## Finding PR-007 — Mobile Mailboxes layout is excessively tall

**Severity:** Major UX
**State:** [CONFIRMED]

At a 400px responsive viewport the current table-to-card transformation creates large vertical records with
labels for every column and multiple full-size action buttons. This is technically responsive but not compact.

### Required correction

- use a purpose-built compact mobile mailbox card/list pattern;
- keep address/status/unread/last-received in the first visual region;
- move secondary metadata/action controls into a compact secondary row/menu;
- no horizontal viewport overflow;
- no loss of accessibility labels or destructive-action confirmation.

## Finding PR-008 — Sidebar collapsed state is visually unfinished

**Severity:** Major UX
**State:** [CONFIRMED]

The supplied collapsed-shell screenshot shows an over-wide icon rail and large unused vertical/left visual
space. Current tokens allocate an `80px` collapsed sidebar, larger than required for the shown icons.

### Required correction

- align collapse geometry with the compact structural reference;
- preserve tooltips/accessible labels for icon-only navigation;
- keep active-state clarity;
- desktop collapse and mobile off-canvas drawer must be separate, coherent behaviors;
- Escape/backdrop/navigation close behavior must remain reliable on mobile.

## Finding PR-009 — Authenticated footer contains non-operational public links

**Severity:** Major UX
**State:** [CONFIRMED]

The authenticated base template exposes `Source code`, `Open-source hub`, and `Free subdomains` in the
operational workspace. The supplied screenshot marks this region as undesirable.

### Required correction

Remove public/promotional footer links from authenticated operational pages. Retain only a minimal product
identity footer if required, or allow the workspace to end without a persistent footer. This is a presentation
change only; configured URLs do not need to be deleted from backend settings unless separately approved.

## Finding PR-010 — Message reader composition is oversized

**Severity:** Major UX
**State:** [CONFIRMED]

The current reader uses a tall fixed/clamped iframe (`460px` to `800px`, around `65vh`) and large header/body
spacing. In combination with broken HTML, this produces a large unusable reading surface and pushes attachments
and footer far down the page.

### Required correction

- compact sender/routing/action header;
- readable body width and natural content flow;
- avoid an unnecessarily tall empty/scroll-within-scroll surface;
- attachment section directly follows the message body;
- keep safe iframe isolation where HTML is rendered.

## Finding PR-011 — Create mailbox form is spatially inefficient

**Severity:** Medium UX
**State:** [CONFIRMED]

The form occupies a small left card with a large unused page region. The native size-8 multi-select is tall and
visually dated.

### Required correction

- compact content width and page spacing;
- compact input sizing based on shared tokens;
- improved assigned-user selector presentation without changing submitted field names/semantics;
- preserve local-part validation, uniqueness/reservation behavior and admin-only assignment rules.

## Finding PR-012 — User-management table requires density and responsive correction

**Severity:** Major UX
**State:** [CONFIRMED]

The screenshot shows overly large typography/spacing and poor metadata separation (for example username and
Created metadata visually collide). The table has many operational columns and row actions.

### Required correction

- compact shared table typography/padding;
- clearer username/created hierarchy;
- status/role chips use subtle compact styles;
- action consolidation;
- responsive strategy that does not produce an unreadable horizontal table or excessively tall generic cards;
- preserve admin restrictions, mailbox counts and permissions.

## Finding PR-013 — Add/Edit User form is oversized

**Severity:** Medium UX
**State:** [CONFIRMED]

The form uses large field heights, large vertical gaps and a visually heavy password help block.

### Required correction

- compact form tokens and section rhythm;
- retain Django validation text and password policy;
- preserve autocomplete semantics and all form field names;
- assigned-mailbox and destructive-permission controls remain permission-accurate.

## Finding PR-014 — Gunicorn read-only-filesystem control-server error

**Severity:** Operational OPEN
**State:** [CONFIRMED log finding; root cause UNKNOWN]

Live logs showed:

`Control server error: [Errno 30] Read-only file system`

The v1.3.3 systemd unit intentionally uses `ProtectSystem=strict` with explicit `ReadWritePaths` for runtime,
logs, attachments and Maildir. The exact path Gunicorn is attempting to use has not yet been captured in the
provided evidence, so the root cause must not be guessed.

### Required correction process

- reproduce/capture the full Gunicorn control-server path/context;
- determine whether the source is Gunicorn 25.1 runtime behavior, service configuration, or host-specific
  environment;
- if repo-owned, make the narrowest systemd/command/config correction that preserves confinement;
- if harmless and upstream-only, formally document the disposition with evidence rather than silently ignore it;
- zero repeated control-server filesystem errors during the final bounded observation window.

## Finding PR-015 — Direct live endpoint guard needs authenticated browser acceptance

**Severity:** Acceptance gap
**State:** [PARTIALLY CONFIRMED]

Unauthenticated `/messages/live/` correctly redirects to login. v1.3.3 source contains a direct-navigation guard
and supports background JSON requests. Final production acceptance still requires authenticated browser proof
that direct top-level navigation does not show raw JSON while the live poller continues to receive JSON.

## Production-ready definition

MailStack is production-ready only when both implementation phases complete and every blocker/required gate in
`07_PRODUCTION_ACCEPTANCE_GATE.md` passes. Server health alone is not sufficient if users cannot reliably read
received email.
