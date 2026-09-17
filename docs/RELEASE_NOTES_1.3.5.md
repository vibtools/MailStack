# MailStack 1.3.5 - System Update UX and Bug Fixes

## Purpose

`1.3.5` delivers targeted bug fixes to the Admin Panel System Update page,
improving reliability and enforcing the correct confirmation-modal flow before
any update is triggered. No database migrations, architecture changes, or new
dependencies are introduced.

## Included corrections

- fix: "Install Update" button now always opens the confirmation modal before
  triggering the backend update; previously it bypassed the modal and called
  triggerUpdate() directly, violating the intended UX contract;
- fix: aggressive alert() on initial page-load update_status failure replaced
  with inline error display, consistent with the rest of the page error handling.

## Compatibility

No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization
redesign, outbound mail capability, or installer-flow change is included.

## Qualification evidence

Passes forensic audit with BLOCKING_FINDINGS=0 and FORENSIC_AUDIT=PASS.
