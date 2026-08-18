# MailStack 1.3.3 PHASE-005A correction notes

## Scope

MailStack 1.3.3 is the corrected PHASE-005A development candidate built from the immutable published
`v1.3.1` baseline after the first `1.3.2` qualification attempt failed. The compact inbox and unified
safe message reader remain the approved UI change. This correction is limited to qualification
hygiene, live-poller backward compatibility, version/release metadata, tests, and synchronized
documentation/forensic manifests.

## Corrected qualification findings

- Removes the accidental empty root file `85%` created by Windows CMD output-redirection parsing of
  explanatory text containing `>=85%`.
- Corrects the PHASE-005A Ruff `I001` import-order findings and regenerates the source inventory.
- Records GitHub Actions run `32128090322` as a failed `1.3.2` branch qualification at the
  source-safety inventory gate; downstream CI gates did not qualify that SHA.

## Live-update compatibility

The server continues to redirect ordinary authenticated navigation away from `/messages/live/`, so
raw JSON is not presented as an application page. Background polling accepts the new explicit
`X-MailStack-Live-Request: 1` header and also the legacy `Accept: application/json` signature used by
the previously released JavaScript. This compatibility path prevents live polling from breaking for
browsers that retain the seven-day immutable static cache across an application upgrade.

## Preserved boundaries

No database model or migration, parser/sanitizer policy, authorization, mailbox lifecycle, message
state/delete semantics, attachment authorization, ingestion, Postfix/Dovecot LMTP, Maildir, MariaDB,
public-site/contact, installer, deployment template, backup/restore, or PHASE-004 upgrade/rollback
semantics are changed. No compose, reply, forward, sent, draft, IMAP, POP3, or public registration
capability is added.

## Qualification boundary

`1.3.3` is a development candidate until the corrected delta passes the isolated Python 3.12 local
qualification and a new GitHub branch CI run, followed by PR, main CI, tag, automated release, and
owner acceptance. Existing live-VPS upgrade remains deferred until that release qualification is
complete.
