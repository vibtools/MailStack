# MailStack 1.3.5.5 - Release Verification Reliability

## Purpose

`1.3.5.5` completes the release verification and documentation maintenance needed for the
current MailStack source baseline.

## Included corrections

- Removed the release archive verifier's global-IP literal scan so semantic version values and
  normal documentation content are not treated as network addresses.
- Preserved archive path, checksum, private-key, blocked-file, email-domain, and canonical ZIP
  metadata checks.
- Synchronized the publishing guide, documentation manifest, forensic inventory, and release
  workflow records to `1.3.5.5`.

## Compatibility

No Postfix, Dovecot, LMTP, Maildir routing, outbound mail, authentication, or database architecture
change is included.

## Qualification evidence

Release metadata and package version are synchronized to `1.3.5.5`. The release archive build and
verification gates pass, and the focused release workflow contract suite passes seven tests.
