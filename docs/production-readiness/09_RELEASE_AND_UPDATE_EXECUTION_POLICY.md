# Release and Update Execution Policy

## Current upgrade capability

MailStack v1.3.3 now contains the generic existing-server upgrade tooling required for normal future releases.
The unusual bootstrap sequence used to move the older `1.3.0-rc.1` production server to v1.3.3 should not be
repeated for ordinary future upgrades.

## Standard future upgrade contract

After a future deterministic release archive and matching checksum are present on the server, the supported
upgrade shape is:

```bash
sudo /opt/vibmail/app/scripts/upgrade.sh \
  --archive /root/releases/mailstack-X.Y.Z-source.zip \
  --checksum /root/releases/mailstack-X.Y.Z-source.zip.sha256 \
  --confirm-upgrade
```

`--allow-migrations` is used only after explicit review when the verified target contains new migrations.

## What the maintained upgrader is expected to automate

- service/config prechecks;
- current application verification;
- deterministic archive/checksum/manifest/version validation;
- migration-history comparison;
- source rollback snapshot;
- coordinated data backup;
- staged source replacement;
- dependency convergence;
- migration command/contract checks;
- static collection;
- public-site release switch;
- service restart;
- final application and HTTP verification;
- safe source/runtime rollback in eligible no-new-migration failure cases;
- final upgrade identity report.

## Resilient terminal rule

Production upgrade runs must occur inside `tmux` or another approved resilient session so an operator terminal
disconnect does not terminate the server-side upgrade process.

## Single-command auto-update goal

A true command such as:

```bash
sudo update-mailstack <version>
```

that downloads the release assets and then invokes the maintained upgrader is **not currently part of the
frozen baseline**. It is a potential future operational enhancement, not part of PHASE-006/007 unless the owner
explicitly adds it to scope.

Until such a wrapper is approved and implemented, the normal process is still short:

1. obtain official archive + checksum;
2. invoke the single maintained `upgrade.sh` command above;
3. review PASS output and post-upgrade acceptance.

## Production deployment rule for the two planned phases

- Never hot-edit `/opt/vibmail/app` as the primary deployment method.
- Build/qualify source in repository workflow first.
- Publish/prepare deterministic artifact.
- Verify exact SHA.
- Use maintained upgrade tooling.
- Capture rollback snapshot/data backup paths.
- Run phase-specific live acceptance.
- Update `03_UPDATE_PHASE_COMPLETION_LOG.md` before continuing.

## Failure handling

If upgrade fails:
- do not immediately re-run;
- classify whether mutation started;
- inspect `UPGRADE_FAILURE`, `UPGRADE_FINDING`, `UPGRADE_ROLLBACK` and snapshot paths;
- verify installed source/version/services/health before next action;
- do not manually restore MariaDB/Maildir unless evidence requires it and the owner explicitly approves the
  recovery plan.
