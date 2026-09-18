# MailStack 1.3.5.4 - Site Settings and Branding Reliability

## Purpose

`1.3.5.4` promotes the Admin Site Settings implementation and its production
branding/media contracts to the current release.

## Included corrections

- Persisted Site Settings now drive application and public-site branding, contact,
  footer, privacy, and source-link values.
- Branding uploads validate image content types and are served, backed up, and
  restored through the production media contract.
- Public settings API CORS is restricted to the configured public origin.

## Compatibility

No Postfix, Dovecot, LMTP, Maildir routing, outbound mail, or authentication
architecture change is included.

## Qualification evidence

Release metadata and package version are synchronized to `1.3.5.4`.
