---
document_id: documentation-policy
title: Documentation Policy
document_type: documentation-policy
audience: contributors-and-maintainers
status: active
version: 1.3.3
last_reviewed: 2026-08-18
---

# MailStack documentation policy

## Documentation baseline

The root `documents/` directory is the maintained user-documentation baseline. It contains the
user manual, task-based how-to guide, administrator guide, baseline record, policy, and phase
history. Engineering and operator reference material remains under `docs/`. Maintained UI foundation,
screen catalog, component, responsive, accessibility, future-roadmap, and implementation-status
records are stored under `documents/design/`, while immutable PNG references and their manifest
are stored under `design/`. All sets are part of the release source and deterministic forensic
inventory.

## Mandatory feature workflow

Every maintained runtime, deployment, or repository-tooling phase must update a
`documents/phases/PHASE-NNN-*.md` record and `CHANGELOG.md`. A change to user-visible application or
public-site behavior must also update at least one canonical guide: `USER_MANUAL.md`,
`HOW_TO_USE.md`, or `ADMIN_GUIDE.md`. Phase records must describe scope, user changes, usage,
compatibility, verification, and documentation impact.

Create the next phase document before implementation:

```bash
python scripts/manage_documents.py new-phase \
  --phase-id PHASE-002 \
  --title "Feature title" \
  --summary "What the phase changes for users"
```

The generated record is intentionally marked `draft` and cannot pass the release documentation
gate until completed and changed to `active` or `historical`.

## Automated synchronization

After editing documentation, run:

```bash
python scripts/manage_documents.py sync
python scripts/manage_documents.py check
```

The synchronization command deterministically rebuilds `documents/README.md` and
`documents/DOCUMENTATION_MANIFEST.json` from Markdown front matter and content hashes. The check
command validates required metadata, required sections, unique document and phase identifiers,
version alignment, unresolved markers, draft status, index freshness, and manifest freshness.

## CI enforcement

CI runs documentation synchronization checks, documentation contract tests, the feature-change
policy, general Markdown link validation, the forensic source audit, and the deterministic release
build. The feature policy compares the base and head commits. Runtime or deployment changes without
a phase record and changelog fail. User-facing changes without a canonical guide update also fail.
Generated document and design manifests, indexes, and forensic inventory files do not satisfy the
substantive documentation requirement by themselves. A design-asset change requires a phase record
and changelog even when no runtime page is implemented.

For local verification of a commit:

```bash
python scripts/check_documentation_policy.py --base HEAD^ --head HEAD
python scripts/test_documents.py
python scripts/manage_designs.py --root . check
python scripts/test_designs.py
python scripts/test_ui_foundation.py
python scripts/forensic_audit.py --root . --full
```
