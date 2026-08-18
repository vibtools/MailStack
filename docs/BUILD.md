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
  dist/mailstack-1.3.1-source.zip \
  --checksum dist/mailstack-1.3.1-source.zip.sha256
```

The builder normalizes archive timestamps, preserves executable permissions, writes a source manifest, excludes generated/runtime artifacts and emits a SHA-256 checksum.

## Automated GitHub publication

The deterministic builder remains the canonical artifact producer. After the intended release commit
is merged to `main` and exact-SHA `main` CI passes, push a matching `v<version>` tag. The release
workflow re-runs the release gate/full forensic/build/verification path, stores the verified Actions
artifact, and publishes the GitHub Release with the ZIP and `.sha256` asset.

Manual workflow dispatch validates/builds only. Tag/version/package mismatches, non-current-main tags,
missing successful `main` CI, and pre-existing releases fail closed.

## Stable promotion

The `1.3.1` source baseline is an unpublished version mark. Do not create or push a stable release tag until every required human/operational gate in `docs/PUBLIC_RELEASE_CHECKLIST.md` passes.
