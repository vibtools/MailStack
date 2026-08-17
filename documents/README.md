# MailStack user documentation

The `documents/` directory is the canonical user-facing documentation baseline for MailStack.
Every maintained feature phase must update its phase record and, when behavior changes, the
relevant user manual, how-to guide, or administrator guide.

## Documentation workflow

```bash
python scripts/manage_documents.py new-phase \
  --phase-id PHASE-004 \
  --title "Feature title" \
  --summary "What the phase changes for users"

# Complete the generated phase document and update the affected guides.
python scripts/manage_documents.py sync
python scripts/manage_documents.py check
python scripts/check_documentation_policy.py --base HEAD^ --head HEAD
```

`sync` regenerates this index and `DOCUMENTATION_MANIFEST.json`. CI fails when generated
content is stale, a phase document remains in draft state, or a feature change lacks the
required documentation update.

## Maintained documents

<!-- AUTO-DOCUMENT-INDEX:START -->
| Document | Type | Audience | Status | Version |
|---|---|---|---|---|
| [MailStack Administrator Guide](ADMIN_GUIDE.md) | Admin Guide | mailstack-administrators | active | 1.3.0-rc.2 |
| [MailStack Baseline](BASELINE.md) | Baseline | maintainers-and-operators | active | 1.3.0-rc.2 |
| [MailStack Accessibility Specification](design/ACCESSIBILITY_SPECIFICATION.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack Future UI Roadmap](design/FUTURE_UI_ROADMAP.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack Responsive Specification](design/RESPONSIVE_SPECIFICATION.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack UI Component Matrix](design/COMPONENT_MATRIX.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack UI Foundation](design/UI_FOUNDATION.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack UI Implementation Status](design/IMPLEMENTATION_STATUS.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack UI Screen Catalog](design/SCREEN_CATALOG.md) | Design Reference | designers-developers-and-maintainers | active | 1.3.0-rc.2 |
| [Documentation Policy](DOCUMENTATION_POLICY.md) | Documentation Policy | contributors-and-maintainers | active | 1.3.0-rc.2 |
| [How to Use MailStack](HOW_TO_USE.md) | How To | mailbox-users-and-administrators | active | 1.3.0-rc.2 |
| [Documentation and Feature Baseline](phases/PHASE-000-BASELINE.md) | Phase | users-operators-and-maintainers | active | 1.3.0-rc.2 |
| [Installation, Recovery and Inbound Delivery Reliability](phases/PHASE-003-INSTALLATION-RECOVERY-AND-INBOUND-DELIVERY-RELIABILITY.md) | Phase | users-operators-and-maintainers | active | 1.3.0-rc.2 |
| [Shared UI Foundation and Application Shell](phases/PHASE-002-SHARED-UI-FOUNDATION-AND-APPLICATION-SHELL.md) | Phase | users-operators-designers-and-maintainers | active | 1.3.0-rc.2 |
| [UI Design Intake Baseline](phases/PHASE-001-UI-DESIGN-INTAKE-BASELINE.md) | Phase | users-operators-designers-and-maintainers | active | 1.3.0-rc.2 |
| [MailStack User Manual](USER_MANUAL.md) | User Manual | mailbox-users | active | 1.3.0-rc.2 |
<!-- AUTO-DOCUMENT-INDEX:END -->

## Scope boundary

The files in this directory explain supported product behavior and operator workflows. The
engineering, architecture, security, deployment, and release references remain in `../docs/`.
When these sources disagree, the implementation and verified release contracts are authoritative,
and both documentation sets must be corrected in the same change.
