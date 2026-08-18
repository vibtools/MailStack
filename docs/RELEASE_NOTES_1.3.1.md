# MailStack 1.3.1 source-baseline notes

## Scope

MailStack 1.3.1 is the owner-requested source-baseline mark that consolidates PHASE-004A forensic/
documentation finalization, PHASE-004B fail-closed tag-to-GitHub-Release automation, and PHASE-004C
controlled existing-server source/runtime upgrade and rollback tooling. It does not introduce a new
mailbox/UI feature, outbound mail capability, database model/migration, route, authorization change,
Postfix/Dovecot routing change, installer rewrite, DNS/TLS change, or live VPS mutation.

## PHASE-004C CI correction

GitHub Actions run `32097491341` tested PHASE-004C commit
`47e62bb6c0acd0216fb261f47f85959655b489e0`. Source safety, documentation/design/UI contracts,
forensic inventory, deployment/installer/operations/release-workflow contracts, the PHASE-004C
upgrade/archive/rollback contracts, and the dependency vulnerability audit all passed. Ruff then
reported four E501 line-length findings and one SIM102 nested-`if` finding in the new upgrade archive
verifier. The 1.3.1 correction changes only statement/control-expression layout for those five
findings; the archive integrity, version ordering, migration detection, safe extraction, error text,
and fail-closed semantics are preserved.

## Upgrade/rollback mechanism

The PHASE-004C upgrader requires a deterministic source ZIP and matching SHA-256, verifies canonical
ZIP/source-manifest integrity, rejects same-version/downgrade and historical migration rewrites,
requires explicit acknowledgement for new migrations, acquires a non-blocking runtime lock, and
creates both a source/runtime snapshot and the maintained consistent data backup before mutation.
After that backup, Postfix and Dovecot remain active while Gunicorn, ingestion, and the contact worker
are replaced. No-new-migration failures can restore source/runtime automatically. Migration-capable
failures after schema mutation begins require reviewed reconciliation; MariaDB and Maildir are never
silently restored by the standalone rollback command.

## Release automation

The PHASE-004B release workflow remains fail-closed. A publishing tag must match `VERSION` and
`project.version`, point to the exact current `main` head, have successful exact-SHA `main` push CI,
and have no existing GitHub Release. Manual workflow dispatch remains validation/build-only.

## Qualification boundary

The `1.3.1` version mark and deterministic baseline ZIP are not, by themselves, a production-ready
or published stable-release claim. A fresh GitHub CI run for the correction commit is required before
remote qualification. The first real existing-VPS use of the PHASE-004C mechanism remains PHASE-004D,
and clean-host, backup/restore, restart/reboot, legal/ownership, and final release-owner acceptance
remain separate gates before publication as production-ready.
