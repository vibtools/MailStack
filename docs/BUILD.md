# Build and release guide

## Development environment

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r mailbox-app/requirements/development.txt
```

## Verification

```bash
python scripts/check_docs.py
python scripts/forensic_audit.py --root . --full
```

## Deterministic release build

```bash
python scripts/build_release.py --root .
python scripts/verify_release.py \
  dist/mailstack-1.3.0-rc.2-source.zip \
  --checksum dist/mailstack-1.3.0-rc.2-source.zip.sha256
```

The builder normalizes archive timestamps, preserves executable permissions, writes a source manifest, excludes generated/runtime artifacts and emits a SHA-256 checksum.

## Stable promotion

Do not change the version to `1.3.0` until every required human gate in `docs/PUBLIC_RELEASE_CHECKLIST.md` passes.
