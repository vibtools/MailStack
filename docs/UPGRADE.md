# Upgrade policy and controlled upgrade tool

MailStack clean installation and existing-server upgrade are separate operations. Do **not** rerun
`install.sh` over an existing production deployment to move between releases.

PHASE-004C adds a fail-closed source/runtime upgrade mechanism for an already installed MailStack
server. The tool changes application/public-site source and Python dependencies only. It deliberately
preserves `/etc/vibmail`, Postfix, Dovecot, Nginx, systemd, TLS, Maildir, MariaDB data, and existing
host configuration unless a future separately reviewed migration explicitly changes those contracts.

> PHASE-004C provides and source-qualifies the mechanism. The first real existing-VPS execution is a
> separate PHASE-004D acceptance activity and is not claimed by this document.

## Required release inputs

Use only the deterministic release assets published for the target version:

```text
mailstack-X.Y.Z-source.zip
mailstack-X.Y.Z-source.zip.sha256
```

Both files are mandatory. The upgrade verifier checks the SHA-256 filename binding, ZIP integrity,
canonical archive metadata, the complete `SOURCE_MANIFEST.sha256`, version/package-version agreement,
and the current-to-target version direction before extracting any source.

The target must be newer than the installed version. Same-version reinstall and downgrade are
rejected by the generic upgrade path.

## Pre-upgrade preparation

1. Review the target release notes and any migration notes.
2. Confirm MariaDB, Postfix, Dovecot, Nginx, Gunicorn, ingestion, and the public contact service are healthy.
3. Copy the deterministic ZIP and checksum to a root-only location on the server.
4. Keep an independent off-host backup and the currently installed release artifact available.
5. Run the command in a resilient `tmux` or `screen` session during an approved maintenance window.

The current application verifier is executed before any mutation. Configuration syntax checks for
Postfix, Dovecot, and Nginx must also pass.

## Upgrade command

From an installed release that contains the PHASE-004C tooling:

```bash
sudo /opt/vibmail/app/scripts/upgrade.sh \
  --archive /root/releases/mailstack-X.Y.Z-source.zip \
  --checksum /root/releases/mailstack-X.Y.Z-source.zip.sha256 \
  --confirm-upgrade
```

If the verified target introduces new Django migration files, the command stops before mutation and
requires explicit review/acknowledgement:

```bash
sudo /opt/vibmail/app/scripts/upgrade.sh \
  --archive /root/releases/mailstack-X.Y.Z-source.zip \
  --checksum /root/releases/mailstack-X.Y.Z-source.zip.sha256 \
  --allow-migrations \
  --confirm-upgrade
```

Existing migration files may not be removed or modified by the target archive. Either condition is a
blocking integrity failure.

## What the upgrade does

The tool acquires the non-blocking `/run/lock/vibmail-upgrade.lock`, verifies the current deployment,
verifies and stages the target release, creates a rollback snapshot under
`/var/backups/vibmail/upgrades/`, and runs the maintained consistent backup command **before** source
mutation.

The consistent data backup may briefly stop mail-facing services in order to capture the existing
backup contract. After that backup completes and the original service state is restored, the source
mutation window stops only Gunicorn, ingestion, and the public contact worker. Postfix and Dovecot
remain active so accepted inbound messages can continue to land in Maildir while ingestion is paused.

The tool then:

- atomically stages verified source outside `/opt/vibmail/app`;
- replaces application source while preserving runtime/environment state outside the source tree;
- converges the existing Python virtual environment to the target production requirements and runs
  `pip check`;
- applies approved migrations and validates schema, Postfix, Maildir, counters, static assets, and
  Django deployment checks;
- creates a new versioned public-site release and switches the `current` symlink only after rendering
  and dependency installation succeed;
- updates `/etc/vibmail/installation.json` with previous/target version and verified source SHA-256;
- validates Postfix, Dovecot, and Nginx configuration without rewriting those configurations;
- restarts the application/contact workers and runs the maintained application verifier plus local
  HTTPS acceptance checks.

Success prints `MAILSTACK_UPGRADE=PASS`, the source SHA-256, the rollback snapshot path, and the
coordinated data-backup path.

## Failure and rollback behavior

For an upgrade with **no new migrations**, a failure after source mutation triggers automatic
application/runtime rollback from the pre-upgrade snapshot and restores the previous public-site
pointer. The previous release requirements are reinstalled before services are restarted.

If a migration-capable upgrade fails after schema mutation begins, automatic source rollback is
intentionally refused. The tool prints:

```text
UPGRADE_ROLLBACK=MANUAL_SCHEMA_RECONCILIATION_REQUIRED
```

and identifies both the source snapshot and coordinated data backup. This avoids silently pairing
old source with an unproven forward database schema or restoring a database snapshot that could
discard mail accepted after the backup.

For a reviewed source/runtime rollback when no schema change occurred:

```bash
sudo /opt/vibmail/app/scripts/rollback_upgrade.sh \
  --snapshot /var/backups/vibmail/upgrades/TIMESTAMP-from-X-to-Y \
  --confirm-rollback
```

A snapshot that records new migrations fails closed unless `--accept-forward-schema` is explicitly
provided after review. Even with that acknowledgement, the rollback command never restores MariaDB
or Maildir automatically. A true schema/data rollback must use the coordinated backup and the
reviewed restore/reconciliation procedure in `docs/BACKUP_RESTORE.md`.

## Preserved host contracts

The generic PHASE-004C upgrade path does not rewrite:

- `/etc/vibmail` secrets or environment files;
- Postfix or Dovecot configuration;
- Nginx configuration;
- systemd units;
- Let's Encrypt certificates or renewal hooks;
- `/var/vmail` Maildir data;
- MariaDB databases except for explicitly approved Django migrations;
- DNS, MX, PTR/rDNS, firewall, provider, or n8n configuration.

A release that requires one of those changes needs a separately reviewed migration procedure rather
than silently extending this generic source/runtime upgrader.

## Post-upgrade acceptance

After a real upgrade, retain the snapshot until all acceptance checks complete. At minimum verify:

1. all seven MailStack-related services are active;
2. login and authorization boundaries;
3. mailbox list/message rendering and attachments;
4. Postfix unknown-recipient rejection;
5. real external inbound SMTP → LMTP → Maildir → ingestion → browser visibility;
6. public contact delivery;
7. backup creation after the upgrade;
8. restart/reboot recovery.

The first real existing-server execution of this PHASE-004C mechanism belongs to PHASE-004D.
