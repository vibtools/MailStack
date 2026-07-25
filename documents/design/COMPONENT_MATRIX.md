---
document_id: ui-component-matrix
title: MailStack UI Component Matrix
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-25
---

# MailStack UI component matrix

## Purpose

Define reusable components before page-by-page implementation so visual rules, interaction,
security, and responsive behavior remain consistent.

## Scope

The matrix covers components visible across the imported designs and components required to make
those designs production-ready. PHASE-002 implements only shared shell and baseline control
normalization. Backend feature authorization and page-specific workflows remain authoritative.

## Approved baseline

| Component | Implementation status | Required behavior |
|---|---|---|
| Authenticated app shell | Implemented in PHASE-002 | Sidebar, top bar, current route, responsive drawer, keyboard focus |
| Unauthenticated shell | Implemented in PHASE-002 | Local branding, sign-in content only, no private navigation |
| Brand lockup | Implemented in PHASE-002 | Canonical local SVG, decorative mark handling, visible product name |
| SVG icon sprite | Implemented in PHASE-002 | Local symbols, decorative `aria-hidden`, unique IDs |
| Account menu | Implemented in PHASE-002 | Identity context, Escape close, outside-click close, POST logout |
| Navigation drawer | Implemented in PHASE-002 | Backdrop, Escape close, focus move/return, inert hidden sidebar |
| Desktop sidebar collapse | Implemented in PHASE-002 | Local browser preference, accessible pressed state, no server data |
| Buttons and form controls | Foundation normalization implemented | 44 px target, focus state, existing form behavior preserved |
| Page header | Shared foundation implemented; page refinement pending | Title, description, primary action, responsive stacking |
| KPI card | Page phase pending | Label, value, supporting text, accessible status |
| Status badge | Existing behavior preserved; redesign pending | Text or icon in addition to color |
| Data table | Page phase pending | Sorting, pagination, responsive list conversion where required |
| Search and filters | Existing behavior preserved; redesign pending | Server-side query, clear state, keyboard operation |
| Searchable multi-select | Future reviewed component | Search, selected chips, clear action, large-list support |
| Context menu | Page phase pending | Permission-aware actions, focus management, Escape close |
| Confirmation dialog | Page phase pending | Object identity, destructive wording, managed focus |
| Message list row | Inbox phase pending | Sender, subject, preview, read state, time, attachment indicator |
| Reading pane | Security-focused phase pending | Normalized HTML, plain text, isolated original layout |
| Attachment card | Message phase pending | Filename, type, size, security notice, authorized download |
| Alerts and toasts | Existing behavior preserved | Success, warning, error, live region without focus theft |
| Loading and empty states | Page phase pending | Stable layout, recovery action, no false success |

## Change control

A page patch must use shared components unless a reviewed exception is documented. Component API,
state, accessibility, or security changes require focused tests and updates to this matrix and the
UI foundation. Planned components remain non-functional until their corresponding backend and
security contracts are approved.
