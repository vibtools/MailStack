# DNS and delivery prerequisites

Before installation, create DNS records for the public, application, and mail hostnames. The mail domain must have an MX record pointing to the configured mail hostname, and that mail hostname must resolve directly to the VPS public address. HTTP CDN proxying must not be used for SMTP.

Inbound TCP ports 25, 80, and 443 must reach the server. The installer checks DNS unless `--skip-dns-check` is explicitly supplied. Skipping the check does not remove the requirement; it only postpones validation.

For reliable contact-form notifications and general outbound system mail, configure accurate PTR/rDNS, SPF, DKIM, and DMARC outside the base receive-only installer. Provider policies can still reject outbound notifications. The team mailbox receive path itself does not require SMTP submission or IMAP/POP3.
