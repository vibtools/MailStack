# MailStack UI design intake

This directory preserves the approved MailStack UI reference archive without activating any
unimplemented feature. The intake is identified as `MAILSTACK-UI-DESIGN-INTAKE-001` and is anchored to the
CI-qualified documentation-governance commit `068097056cecdd18f39fd304d579563b7b43c491`.

## Structure

```text
design/
├── README.md
├── DESIGN_MANIFEST.json
└── intake/
    └── original/        Immutable source PNG files, preserved byte-for-byte
```

The source archive contained 25 valid PNG files and passed CRC, path-safety, decode, dimension,
and exact-duplicate checks before import. Original filenames are retained under
`design/intake/original/`; stable screen IDs and corrected display names are recorded in the
manifest rather than changing source bytes.

## Integrity workflow

```bash
python scripts/manage_designs.py --root . check
python scripts/test_designs.py
```

`check` validates PNG structure and chunk CRC values, exact file hashes, dimensions, unique
screen IDs, classification values, immutable-source paths, summary counts, and manifest
synchronization. `sync` may update technical file metadata after an explicitly approved source
replacement; it does not alter classification, scope, or implementation status.

## Implementation boundary

A PNG is a visual contract, not authorization to add backend behavior. Current-screen references
may be implemented page by page only after the shared UI foundation is approved. Planned and
future-review screens remain inactive until a separate phase defines models, routes, permissions,
security boundaries, migrations, tests, documentation, and rollback behavior.

See the maintained specifications under [`../documents/design/`](../documents/design/).
