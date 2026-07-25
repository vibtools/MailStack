# MailStack roadmap

This roadmap is directional. Security, data integrity and backward compatibility take priority over dates.

## Release candidate exit criteria

- Complete a clean Ubuntu Server 24.04 installation on an isolated VPS
- Pass the online dependency vulnerability audit in CI
- Verify DNS, TLS issuance and renewal, inbound SMTP and LMTP delivery
- Verify unknown-recipient and disabled-mailbox rejection
- Verify login, mailbox isolation, safe HTML, attachments, live updates and contact delivery
- Complete backup, restore and restart-recovery acceptance
- Confirm source copyright ownership and third-party license compatibility

## Documentation baseline

- Preserve `MAILSTACK-1.3.0-RC1-DOCS-BASELINE-001` as the starting point for future phases
- Require a phase record, changelog update and affected user-guide update with maintained feature changes
- Keep the generated user-document index and manifest deterministic and CI-enforced

## 1.3 stable

- Promote the verified release candidate without feature removal
- Publish reproducible release assets and checksums
- Publish sanitized screenshots and an operator walkthrough
- Add structured release provenance and SBOM generation

## 1.4 planned

- Improved operator diagnostics and observability
- Guided DNS/deliverability validation
- Expanded integration and long-running reliability tests
- Optional administrative API design, subject to a separate security review
- Accessibility and localization improvements

## Future research

- Multi-node and high-availability architecture
- Queue and ingestion scaling for larger mailbox volumes
- Optional outbound transactional delivery with strict relay controls
- External object storage for attachments

No roadmap item authorizes removing, disabling or simplifying an existing feature. Breaking changes require an explicit major-version design and migration plan.
