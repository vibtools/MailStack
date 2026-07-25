# MailStack 1.3.0 RC1 release notes

## Purpose

Version 1.3.0 RC1 converts the verified private deployment source into a configurable, publicly documented, reproducibly packaged open-source release candidate while preserving the approved v1.2.1 mailbox application behavior.

## Added

- Ubuntu 24.04 one-command installer
- configurable mail, application, mail-server, and public hostnames
- MariaDB/Postfix/Dovecot/Nginx/systemd/environment templates
- public-site rendering for the configured domain
- complete AGPL-3.0 license text, licensing rationale and public governance/security documents
- Django 5.2.16 LTS security maintenance pin with exact-version deployment and CI verification
- GitHub CI, release workflow, Dependabot, CODEOWNERS, issue and pull-request templates
- source secret scanning, documentation validation, forensic file/symbol inventory, template validation and installer/operations contract tests
- SEO-oriented repository metadata, reusable project logo, deterministic source ZIP, manifest, checksum and verifier
- custom-domain migration and tests
- consistent configurable backup/restore tooling

## Hardened

- strict production setting validation
- SQL identifier validation and least-privilege column grants
- Postfix invoker-view privileges
- LMTP-only Dovecot service identity
- hostname collision and installer argument validation
- HSTS policy consistency
- backup consistency, archive validation, and service-state restoration
- release scanner self-protection and generated-artifact rejection

## Compatibility

- Existing `vibmail.my` defaults, application data model, URLs, templates, static assets, tests, migration history, and legacy maintenance assets are retained.
- No functional baseline source file was deleted.
- Existing v1.2 backup sets without contact-state archives remain restorable by the updated restore script.

## Release qualification

Repository CI, the online dependency audit, deterministic release build, release verification and clean-clone verification pass at commit `1e1737edea2e6c922265a15d8584b56671820c65`. The release remains an **RC** until a complete clean Ubuntu 24.04 live installation, inbound SMTP/LMTP, backup/restore and operational acceptance campaign passes.

## Documentation baseline

MailStack also preserves the complete UI reference archive as `MAILSTACK-UI-DESIGN-INTAKE-001` and freezes
`MAILSTACK-UI-FOUNDATION-001`. The intake adds no runtime feature; it provides immutable design assets,
screen classification, future-scope boundaries, and automated integrity gates for later page-by-page redesign.

MailStack now includes a root `documents/` user-documentation hub with a complete user manual,
task-based how-to guide, administrator guide, protected baseline record, mandatory per-phase
records, deterministic index and manifest generation, documentation contract tests, and CI
change-policy enforcement. This framework does not change runtime application behavior.
