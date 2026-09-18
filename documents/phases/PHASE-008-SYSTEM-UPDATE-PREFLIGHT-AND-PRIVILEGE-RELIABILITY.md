---
document_id: phase-008-system-update-preflight-and-privilege-reliability
title: System Update Preflight and Privilege Reliability
document_type: phase
audience: mailstack-administrators-and-maintainers
status: active
version: 1.3.5.3
last_reviewed: 2026-09-18
phase_id: PHASE-008
---

# PHASE-008: System Update preflight and privilege reliability

## Objective

Make the administrator System Update workflow operationally honest and safe on a hardened
Ubuntu deployment. The web application must detect readiness before an update, explain a
blocking condition without pretending that installation started, and delegate root-only
upgrade execution without weakening the Gunicorn service hardening.

## Scope

The existing release download, source archive, checksum, manifest, backup, migration, and
rollback contracts remain authoritative. `mailbox-app/scripts/upgrade.sh` remains the only
component that performs the upgrade. This phase changes the hand-off boundary around it:

- Add a read-only preflight endpoint and compact result model covering the application
  identity, required paths and permissions, required commands/services, writable runtime
  status path, free space, and the configured root updater path.
- Block the Install action unless the preflight result is ready and the requested release
  assets are official and complete.
- Replace web-process `sudo` escalation with a root-owned, systemd-managed updater worker.
  Gunicorn writes a narrowly structured request into the updater request directory; the
  worker validates ownership, permissions, URL-derived temporary paths, and the fixed
  `upgrade.sh` command before execution.
- Keep `NoNewPrivileges=true`, capability dropping, filesystem confinement, and
  `RestrictSUIDSGID=true` on the Gunicorn service. The worker receives root privileges only
  because its unit is root-owned and its command is fixed.
- Permit only non-destructive, explicitly allowlisted remediation if a future installer
  integration can prove it safe. This phase does not edit sudoers, disable systemd
  hardening, run arbitrary shell input, alter firewall/SSH policy, or perform database,
  Maildir, migration, or destructive cleanup automatically.

## User-visible behavior

The System Update page exposes a preflight status with `Ready`, `Blocked`, or `Manual action
required`. A blocked result disables installation and identifies the failed check. A ready
result enables the existing confirmation dialog. During execution, the existing status file
and progress/log behavior remain the source of truth.

## User-facing changes

Administrators will see the update readiness result before the install confirmation. When a
deployment is missing the root updater unit or another required prerequisite, the page gives
the failed check and stops the install request instead of displaying a misleading progress
state.

## How to use

Open **System Update**, run the release check, and review the preflight result. Install is
available only when the result is `Ready`. If it is blocked, apply the documented manual
deployment repair, reload the page, and run preflight again.

## Compatibility

The feature is compatible with the existing single-node Ubuntu 24.04 deployment and release
archive format. Existing deployments that have not installed the updater worker fail closed
with a manual-action message instead of attempting `sudo` from Gunicorn. No receive-only,
Postfix, Dovecot, Maildir, authentication, or message-reader behavior changes.

## Security

The request directory and status file are runtime state under `/run/vibmail`. Requests are
created with restrictive permissions and contain only server-validated release URLs and paths.
The worker rejects symlinks, unexpected owners or modes, path traversal, non-GitHub release
origins, concurrent jobs, and any command other than the fixed upgrade script invocation.

## Implementation sequence

1. Define reusable preflight checks and expose an admin-only `preflight` endpoint.
2. Add the root updater worker and systemd unit, then render/install its runtime directories
   and enable it alongside the existing MailStack services.
3. Change `start_update` to require a successful preflight and enqueue a validated request
   rather than invoking `sudo`.
4. Add the preflight result panel and install gating to the existing System Update page.
5. Add focused regression tests for readiness, blocked conditions, request validation,
   privilege separation, concurrent updates, and preservation of the existing update flow.
6. Update the administrator documentation and changelog, synchronize managed documentation,
   regenerate the forensic inventory, and run the final validation cycle once all edits are
   complete.

## Verification

The final qualification must pass focused System Update tests, Django checks, targeted Ruff
and compile checks, deployment/template and installer contracts, documentation checks, UI
foundation checks when templates change, inventory generation/check, the essential and
repository forensic audits, and `git diff --check`. The required forensic result is
`BLOCKING_FINDINGS=0` and `FORENSIC_AUDIT=PASS`.

## Documentation impact

This phase updates the administrator guidance for preflight results, blocked installations,
worker installation, and manual recovery. It does not claim that a deployment is upgradeable
until the root updater unit and its runtime permissions are present.
