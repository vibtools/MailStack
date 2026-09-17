# MailStack 1.3.5.2 - Revision Release

## Purpose

`1.3.5.2` is a revision release that extends the release and upgrade tooling to
support four-component MailStack versions while preserving existing application
and System Update behavior.

## Included changes

- release identity, source archive, and upgrade validation now accept and order
  four-component versions such as `1.3.5.2`;
- release metadata and package version are synchronized to `1.3.5.2`.
- inventory generation, forensic auditing, and source packaging consistently exclude
  local-only private reference material from CI comparisons and public archives.

## Compatibility

No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization
redesign, outbound mail capability, or installer-flow change is included.
