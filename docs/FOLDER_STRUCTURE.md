# Repository structure

```text
.github/                    CI, release workflow and contribution templates
deployment/templates/       Rendered server configuration templates
design/                     Immutable UI PNG intake and deterministic design manifest
  intake/original/          Byte-preserved original UI and logo reference files
documents/                  User manual, how-to, admin guide, phase history and generated manifest
  design/                   UI foundation, catalog, components, responsive, accessibility and roadmap
  phases/                   Mandatory per-phase user and compatibility records
docs/                       Public architecture, operations and release documentation
mailbox-app/                Django team mailbox application
  apps/                     Accounts, audit, core, dashboard, ingestion, mailboxes and messages
  config/                   Django settings and URL/WSGI/ASGI entry points
  deployment/               Legacy-compatible deployment assets
  requirements/             Pinned runtime and development dependencies
  scripts/                  Backup, restore, deploy, health and verification tools
  static/                   Application CSS, JavaScript, local brand assets and SVG icon sprite
    brand/                  Runtime copy of the canonical MailStack logo
    css/                    Existing page CSS and the frozen shared foundation layer
    icons/                  Self-hosted shared SVG symbol sprite
  templates/                Django HTML templates
  tests/                    Unit, integration, functional, reliability and security tests
public-site/                Static site and isolated contact WSGI service
scripts/                    Repository audit, documentation, UI contracts, rendering, testing and release tools
install.sh                  Clean Ubuntu 24.04 installer
VERSION                     Canonical release version
```

Generated files such as virtual environments, databases, Maildir data, attachments, logs, backups, coverage output and release archives are excluded from version control and release packages.
