# MailStack 1.3.4-rc.2 — PHASE-006 reader-fidelity continuation candidate

## Purpose

`1.3.4-rc.2` is the owner-approved PHASE-006 continuation pre-release identity for controlled
acceptance of the high-fidelity safe HTML reader correction. It retains the RC1 reader-integrity,
existing-message repair, and Gunicorn runtime protections while restoring a bounded, sanitized subset
of sender presentation CSS. The frozen production baseline remains published/live-verified `v1.3.3`;
`v1.3.4-rc.1` remains immutable historical PHASE-006 pre-release evidence.

This pre-release does not mark PHASE-006 complete. Branch/main CI, exact-main tag publication,
controlled upgrade, repair/backfill evidence, reader acceptance, health checks, and bounded log
observation remain blocking.

## Included corrections

- preserve safe inline CSS and bounded sanitized `<style>`/responsive `@media` rules through an
  explicit presentation-only allowlist;
- keep CSS URLs/imports/fonts, remote tracking/resources, active positioning/effects, scripts, event
  handlers and unsafe URL schemes blocked;
- preserve safe `<style>` content from `<head>` while continuing to suppress title/metadata/scripts
  and arbitrary non-display head text;
- retain blocked-remote-image removal, sandbox/no-referrer isolation and plain-text fallback;
- retain bounded, dry-run-first existing-message body repair from preserved Maildir source while
  preserving message identity/state/source/attachments;
- retain the Gunicorn control-interface closure without weakening `ProtectSystem=strict`;
- pin deterministic CSS parsing with `tinycss2==1.5.1`;
- advance the pinned Django 5.2 LTS runtime from 5.2.16 to security-fix release 5.2.17 and synchronize
  active exact-version deployment/security-test contracts;
- remove Bandit B105 false positives through semantics-only CSS parser local-variable naming rather
  than suppressing the security rule.

## Qualification evidence

The combined RC2 implementation/dependency candidate before release-identity promotion passed local
qualification on Python 3.12.8 with 223 tests passed and one Windows symbolic-link capability skip,
93.03% coverage, focused reader/repair/security/auth/deployment suites PASS, Ruff PASS, Bandit PASS,
Django system check PASS, migration drift NONE, dependency consistency PASS, `pip-audit` with no known
vulnerabilities, documentation/design/installer/operations/release/upgrade gates PASS, and standard
plus full forensic audit with zero blocking findings.

This release-identity promotion must pass the same local gates again, then branch CI, PR/main CI and
exact-main tag publication before controlled live deployment and acceptance.

## Compatibility

No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization redesign, outbound
mail capability, iframe/CSP weakening, repair-architecture change, installer-flow change, or PHASE-007
broad UI redesign is included.

## Live acceptance sequence

Use the maintained upgrader with the official deterministic ZIP/checksum, verify services and health,
run repair dry-run first, review counters, run only the approved bounded mutation, verify representative
inline-style/style-block/table/responsive messages plus malicious/remote CSS rejection, confirm
plain-text/attachments/state preservation and idempotence, and observe logs for continued absence of
the previously repeated Gunicorn control-server read-only-filesystem finding.
