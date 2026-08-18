---
document_id: phase-002-shared-ui-foundation-and-application-shell
title: Shared UI Foundation and Application Shell
document_type: phase
audience: users-operators-designers-and-maintainers
status: active
version: 1.3.2
last_reviewed: 2026-08-18
phase_id: PHASE-002
---

# PHASE-002: Shared UI foundation and application shell

## Objective

Implement the frozen MailStack design tokens, responsive application shell, navigation, account
controls, and shared interaction foundation without changing page business logic.

## Scope

This phase adds a self-hosted CSS foundation, a responsive authenticated sidebar and top bar, an
unauthenticated sign-in shell, a local SVG icon sprite, a runtime copy of the canonical MailStack
logo, and minimal JavaScript for drawer, collapse, account-menu, focus-return, and persisted desktop
navigation state.

The existing dashboard, mailbox, user, inbox, and message page templates remain page-specific and
are not redesigned in this phase. Models, migrations, URLs, forms, permissions, mail delivery,
ingestion, storage, database contracts, deployment templates, and future-feature routes are out of
scope.

## User-facing changes

Authenticated users receive a consistent MailStack application frame with a desktop sidebar,
responsive mobile navigation drawer, sticky top bar, account menu, visible receive-only notice,
and current-route highlighting. Administrators continue to see **User management**; ordinary users
do not. The notification permission action remains available only when the browser reports an
undecided notification permission.

The sign-in page uses the same local brand asset and design tokens without exposing authenticated
navigation. Existing page content and all supported actions continue to render inside the new
shell.

## How to use

1. Sign in through the configured MailStack application URL.
2. Use the left navigation to open **Dashboard**, **Mailboxes**, or **Create mailbox**.
3. Administrators may also open **User management**.
4. On desktop widths of 1200 pixels or more, use the sidebar control to collapse or expand the
   navigation. The preference is stored in the current browser only.
5. On tablet or mobile widths, use the menu button to open the navigation drawer. Close it with the
   backdrop, the Escape key, or a navigation selection.
6. Open the account menu in the top bar and use the POST-protected **Log out** action when finished.

## Compatibility

The phase preserves all existing routes, authorization checks, CSRF protection, live polling,
browser notifications, copy controls, tabs, destructive-action confirmations, and the global
`VibMail` JavaScript namespace. It retains all legacy runtime identifiers and does not add outbound
mail, reply, forward, sent, drafts, spam, IMAP, POP3, public signup, settings, teams, domains, logs,
or other planned features.

There are no database migrations, configuration changes, package dependencies, external fonts,
CDN assets, or third-party JavaScript additions. Cross-platform audit hardening closes every
contact-service SQLite connection deterministically, retains the Maildir `0700` assertion on POSIX
systems without treating Windows mode emulation as POSIX, and adds standalone contact-service
Ruff/Bandit gates. Source-release generation now writes canonical POSIX ZIP metadata and stored
entries for every member, eliminating host and zlib byte-stream variance between Windows and Linux.
Rollback consists of restoring the prior base template and JavaScript, removing
the new foundation stylesheet and local static assets, and reverting those audit-only hardening
changes.

## Verification

The dependency-free UI foundation contract suite validates required files, frozen tokens,
responsive breakpoints, accessibility hooks, current-route-only navigation, local SVG integrity,
icon completeness, template control-flow balance, preserved runtime markers, and prohibited unsafe
JavaScript constructs. Django functional tests validate administrator, ordinary-user, login,
mailbox, message, and create-mailbox shell behavior under the existing authorization model.

Local qualification collected 196 Django tests: 195 passed and one Windows-only symbolic-link
case was skipped; coverage was 94.99 percent against an 85 percent minimum. Seven focused shell
functional tests and eight dependency-free shell contracts passed. Contact-service regression tests
also verify that SQLite connections are unusable after context exit, preventing Windows temporary
file cleanup failures.

The phase must also pass documentation synchronization and policy checks, design-intake checks,
forensic inventory, template validation, installer and operations contracts, source forensic audit,
mailbox and standalone contact-service Ruff/Bandit gates, Django checks, migration-drift checks,
deterministic release build, canonical ZIP metadata verification, byte-for-byte cross-platform
release-hash verification, and GitHub Actions before qualification.

## Documentation impact

Updated the user manual, how-to guide, administrator guide, frozen foundation and component
references, responsive and accessibility specifications, implementation status, changelog,
engineering test/security/performance/forensic reports, folder structure, screenshot guidance,
CI workflow, documentation contracts, forensic audit, and deterministic inventory. Added this phase
record, the runtime foundation assets, dependency-free contract tests, and Django functional tests.
