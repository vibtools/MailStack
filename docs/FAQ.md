# Frequently asked questions

## Is MailStack a complete replacement for Gmail or Microsoft 365?

No. The reference deployment is a receive-only shared mailbox system. It intentionally does not provide IMAP, POP3, user SMTP submission, calendars or outbound campaigns.

## Can multiple users access one mailbox?

Yes. Administrators assign mailbox memberships, and message access is filtered by those memberships.

## Does it support multiple mail domains?

One configurable mail domain is supported per reference installation. Multi-domain operation is not qualified in this release.

## Can I install it on Debian or another Ubuntu version?

The automated installer supports clean Ubuntu Server 24.04 LTS only. Other platforms require a reviewed manual port and full acceptance testing.

## Does it send email?

Hosted mailboxes are receive-only. The isolated public contact service can submit a fixed notification through local Postfix.

## Is Docker supported?

No official container deployment is included in this release because SMTP, LMTP, Maildir ownership, systemd and TLS integration require a separately audited design.

## Is the release production-ready?

It is a release candidate. Automated gates pass, but clean-VPS and external-mail acceptance remain mandatory before stable promotion.

## Where can I find more Vib Tools projects?

See https://dev.vib.tools/. Free subdomain registration is available separately at https://ygit.net/.
