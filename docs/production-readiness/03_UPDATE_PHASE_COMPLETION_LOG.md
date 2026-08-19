# Update Phase Completion Log

## Purpose

This is the single progress ledger for the two-phase production-readiness update. It must be updated immediately
when a phase changes state so implementation cannot become unordered or ambiguous.

## Overall progress

| Metric | Current value |
|---|---|
| Frozen baseline | MailStack `v1.3.3` |
| PHASE-006 live-acceptance target | MailStack `v1.3.4-rc.2` pre-release |
| Planned implementation phases | **2** |
| Completed phases in this production-readiness cycle | **0 / 2** |
| Remaining phases | **2 / 2** |
| Current implementation state | PHASE-006 RC2 implementation/dependency candidate locally qualified; release-identity requalification, GitHub CI and live acceptance pending |
| Runtime implementation started | Yes — PHASE-006 |
| Production-ready acceptance | Not yet |

## Phase status ledger

| Phase | State | What must be completed | Completion evidence |
|---|---|---|---|
| PHASE-006 | **RC2 LOCALLY QUALIFIED / LIVE PENDING** | Reader integrity, safe existing-message repair, runtime error closure, high-fidelity safe CSS reader regressions | Pre-promotion RC2: 223 passed, 1 capability skip, 93.03% coverage; Ruff/Bandit/pip-audit/full-forensic PASS |
| PHASE-007 | **PENDING / BLOCKED BY PHASE-006** | Compact UI system, responsive refinement, final CI/live/E2E acceptance | Not yet recorded |

---

# PHASE-006 completion record

## Status

**RC2 IMPLEMENTATION QUALIFIED LOCALLY / RELEASE-IDENTITY REQUALIFICATION AND LIVE ACCEPTANCE PENDING**

## Baseline at phase start

Must equal the official v1.3.3 frozen identity documented in `00_OFFICIAL_BASELINE_FREEZE.md`.

## Approved scope

- HTML sanitizer/rendering correction.
- Remote-image graceful blocked-state handling.
- Removal of intrusive visible protected-rendering banner while retaining security.
- Existing-message repair/backfill tooling.
- Reader fallback/error handling.
- Gunicorn read-only-filesystem control-server finding closure/disposition.
- Authenticated live-endpoint navigation regression.
- Focused tests and live reader acceptance.

## Features/fixes actually completed

- RC1 sanitizer prevents raw non-display/active content from leaking into visible message body output;
- RC2 preserves a bounded sanitized presentation-only CSS subset, including safe inline/style-block and responsive `@media` rules, while denying CSS resource loading and active behavior;
- blocked remote image nodes are omitted rather than rendered as broken residue;
- permanent protected-rendering banner removed while sandbox/no-referrer remain;
- controlled existing-message body repair command added with dry-run, targeting, limits and explicit confirmation;
- repair preserves message identity/state/source/attachments and updates only parser-derived body fields;
- unused Gunicorn control interface disabled without weakening systemd filesystem confinement;
- focused PHASE-006 regression coverage added;
- Django 5.2 LTS security pin advanced from 5.2.16 to 5.2.17 with exact-version deployment/test contracts synchronized;
- Bandit B105 CSS-parser naming false positives removed without disabling or suppressing the security rule.

## Files changed

The RC2 candidate spans the approved reader/dependency/deployment-contract tests plus current release
documentation and generated metadata. The exact candidate path set is enforced by the forensic inventory
and Git diff; PHASE-007 implementation remains untouched.

## Tests/evidence

RC1 implementation commit `90175b7a4549cb67d874692081bd5b0484eddccc` passed GitHub Actions CI run `32183300485`; the qualified RC1 work was later squash-merged as `212ccaf7fab94e1b42ef2a57afb7bdfee673667e` and tagged `v1.3.4-rc.1`. Controlled RC1 reader acceptance exposed the remaining presentation-fidelity defect.

The combined RC2 implementation/dependency candidate before release-identity promotion passed locally on Python 3.12.8: focused reader/repair/security/auth/deployment suites PASS; full suite `223 passed, 1 skipped`; coverage `93.03%`; Ruff PASS; Bandit PASS; Django system check PASS; migration drift NONE; dependency consistency PASS; `pip-audit` reported no known vulnerabilities; documentation/design/installer/operations/release/upgrade gates PASS; standard and full forensic audits PASS with zero blocking findings. RC2 release-identity requalification, GitHub CI and controlled live acceptance remain pending.

## Known residual findings after phase

GitHub branch/main CI, exact-main tag publication and controlled production reader acceptance remain outstanding; no local application/security blocker is currently recorded.

## Phase completion decision

`PENDING — controlled live acceptance still required`

## Remaining after PHASE-006

When PHASE-006 becomes complete, exactly one phase remains: PHASE-007.

---

# PHASE-007 completion record

## Status

**PENDING / BLOCKED BY PHASE-006**

## Approved scope

- compact shared MailStack light-theme token mapping;
- shell/sidebar/topbar refinement;
- authenticated footer cleanup;
- Mailboxes desktop/mobile compact redesign;
- Inbox compact refinement;
- compact message-reader refinement;
- Create mailbox compact form;
- User management compact table/list;
- Add/Edit user compact forms;
- responsive/accessibility/error-state styling;
- final CI, upgrade, production UI, inbound E2E and stability acceptance.

## Features/fixes actually completed

None yet.

## Files changed

None. PHASE-007 implementation has not started.

## Tests/evidence

Not applicable. PHASE-007 remains blocked until PHASE-006 controlled live acceptance is complete.

## Known residual findings after phase

Not yet assessed.

## Phase completion decision

`PENDING`

## Remaining after PHASE-007

Target: `0` production-readiness phases remaining. Any later work is a separately owner-approved scope and must
not be silently appended to this cycle.

---

# Mandatory update procedure for this log

At each phase completion:

1. Record exact baseline/source commit at phase start.
2. Replace `PENDING` with `COMPLETE` only after all blocking gates pass.
3. List every user-visible feature/fix actually delivered.
4. List important non-user-visible reliability/error/security changes.
5. List exact changed files or link the phase manifest.
6. Record test counts/results and live evidence.
7. Record unresolved findings explicitly.
8. Recalculate completed/remaining phase counts.
9. Write the exact next phase scope before starting it.
10. Do not start the next phase while the prior phase is still ambiguous or partially logged.
