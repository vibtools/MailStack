# Public release checklist

## Completed automated gates

- [x] Complete AGPL-3.0 license text and dependency notices added
- [x] No known real secrets, private keys, databases, Maildir data, attachments, logs, backups, or personal identifiers
- [x] Full application and contact-service tests pass
- [x] Coverage threshold passes
- [x] Ruff and Bandit pass
- [x] Django system and migration checks pass
- [x] Every shell script passes `bash -n`
- [x] Installer valid/invalid plan tests pass
- [x] Deployment templates render with no unresolved tokens
- [x] Release manifest, ZIP integrity, safe paths, executable mode, and checksum verify
- [x] Online dependency audit is configured as a blocking CI gate

## Required human/release-owner gates

- [ ] Copyright ownership and third-party license compatibility confirmed by the release owner
- [ ] Clean Ubuntu Server 24.04 installation tested on an isolated VPS
- [ ] External inbound mail, login, authorization, live updates, safe HTML, and attachments manually verified
- [ ] DNS, PTR/rDNS, SPF, DKIM, DMARC, firewall, backups, and monitoring reviewed for the target deployment

Until the unchecked gates pass, publish the package as a **release candidate**, not as a proven production release.
