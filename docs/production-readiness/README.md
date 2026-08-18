# MailStack Production-Readiness Documentation Pack

**Documentation baseline:** MailStack `v1.3.3`
**Prepared:** 2026-08-18
**Purpose:** Freeze the production-update plan before any further runtime/UI implementation.

This directory is a planning and forensic control pack. It does not itself change MailStack runtime behavior.
It exists so the next implementation work proceeds in a fixed order, with an explicit baseline, defect register,
phase roadmap, completion log, error-handling register, actual-working-state register, acceptance gates, and
change-control policy.

## Canonical baseline for the next update

The next implementation cycle must use the **published and live-verified MailStack v1.3.3 release** as the
canonical source baseline:

- Release/tag: `v1.3.3`
- Published commit: `21dff33219afab3819e7bd1ae1e0a0cc2e7d3698`
- Published tree: `74682033f3164a6a0069a381ae5a38661aad1669`
- Official release source archive: `mailstack-1.3.3-source.zip`
- Official release source SHA-256: `9e2016ce486f1e1f7e30361c73fa50ff73e7c9c72f87dd0941c1a9b5ed2e9964`
- Live installed version: `1.3.3`
- Live marker previous version: `1.3.0-rc.1`
- Live source fidelity gate: PASS

The separately uploaded `MailStack_v1.3.3_Baseline.zip` is retained as historical/candidate evidence only.
Its freeze record identifies it as an owner-frozen candidate and its SHA-256 differs from the published release
asset. It must not silently replace the published/live-verified baseline for implementation.

## Documents

1. `00_OFFICIAL_BASELINE_FREEZE.md` — baseline identity and freeze boundary.
2. `01_PRODUCTION_READINESS_FORENSIC_REPORT.md` — production-readiness defect report and required corrections.
3. `02_TWO_PHASE_A_TO_Z_ROADMAP.md` — complete update roadmap, limited to two implementation phases.
4. `03_UPDATE_PHASE_COMPLETION_LOG.md` — persistent phase completion and next-work ledger.
5. `04_ERROR_HANDLING_REGISTER_AND_PLAN.md` — existing error handling plus required additions.
6. `05_ACTUAL_IMPLEMENTATION_STATUS.md` — what actually works now, after each phase, and what remains.
7. `06_UI_DESIGN_REFERENCE_AND_DEFECT_MATRIX.md` — screenshot audit plus VibTools/Licora reference extraction.
8. `07_PRODUCTION_ACCEPTANCE_GATE.md` — release blocking acceptance criteria.
9. `08_CHANGE_CONTROL_AND_SCOPE_LOCK.md` — strict baseline/scope lock for implementation.
10. `09_RELEASE_AND_UPDATE_EXECUTION_POLICY.md` — release/upgrade execution policy and future single-command goal.
11. `10_TEST_AND_ACCEPTANCE_MATRIX.md` — deterministic test matrix across functionality, UI, security and operations.
12. `11_EXISTING_MESSAGE_REPAIR_AND_BACKFILL_PLAN.md` — safe repair plan for already-indexed broken HTML emails.

## Status language

- `[CONFIRMED]` — directly supported by current source, live output, or supplied screenshots.
- `[INFERRED]` — conclusion strongly supported by evidence but not yet reproduced under a focused test.
- `[UNKNOWN]` — evidence is insufficient; implementation must not guess.
- `[CONFLICT]` — two evidence sources disagree and the authoritative source is explicitly selected.
- `BLOCKER` — production acceptance cannot close while this remains unresolved.
- `OPEN` — must be investigated or explicitly dispositioned before final acceptance.

## Execution rule

No application/runtime implementation starts until this planning pack is owner-approved. Once approved,
implementation proceeds only in the order defined by the two-phase roadmap. The completion log is updated at
the end of every phase before the next phase starts.
