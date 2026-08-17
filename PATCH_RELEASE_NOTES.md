# MailStack 1.3.0-rc.2 PHASE-003 Delta Patch

This patch is valid only against the frozen `1.3.0-rc.1` baseline at commit
`edb11c198b7b21a6765a2f3f8fbd0f997d6b07b1` / baseline ZIP SHA-256
`78aebfa70fae8e1f70d1c7f32876d35171d1e0030445e7b7e9ff7228ac51cfce`.

## In-scope fixes

1. Preserve host-wide `/var/log` permissions and validate the dedicated MailStack log path.
2. Isolate installer-launched Django commands from stale parent-shell environment variables.
3. Prepare the mailbox provisioning runtime lock directory before bootstrap.
4. Make reviewed partial-install repair idempotent for valid bootstrap objects.
5. Persist newly created initial administrator credentials before later installer phases.
6. Fix Dovecot static-userdb LMTP delivery with `allow_all_users=yes` while retaining Postfix recipient validation.
7. Make one-shot dry-run ingestion verification live-worker compatible and non-mutating.
8. Add SSH/PuTTY resilient-session guidance and installer warning.
9. Qualify the known MariaDB/Django uniqueness warnings without a schema migration.
10. Synchronize the staging hotfixes into the canonical source and bump to `1.3.0-rc.2`.

## Scope preservation

No UI page, route, authorization model, application feature, outbound mail function, database migration, dependency, service name, or legacy runtime identifier is intentionally changed. No source file is deleted.

## Apply

Verify the baseline first, then overlay the source paths from this ZIP onto the repository root. The four `PATCH_*` files are package metadata, not canonical source files; remove them from the repository working tree before committing if the ZIP was extracted directly into the repository root. Run the documented verification gates before deployment.
