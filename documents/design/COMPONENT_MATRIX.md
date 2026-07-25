---
document_id: ui-component-matrix
title: MailStack UI Component Matrix
document_type: design-reference
audience: designers-developers-and-maintainers
status: active
version: 1.3.0-rc.1
last_reviewed: 2026-07-24
---

# MailStack UI component matrix

## Purpose

Define reusable components before page-by-page implementation so visual rules, interaction,
security, and responsive behavior remain consistent.

## Scope

The matrix covers components visible across the imported designs and components required to make
those designs production-ready. It excludes backend feature authorization.

## Approved baseline

| Component | Current target screens | Required behavior |
|---|---|---|
| App shell | Dashboard, mailboxes, users, inbox, future administration | Sidebar, top bar, active route, responsive drawer, keyboard focus |
| Page header | All authenticated screens | Title, description, primary action, responsive stacking |
| KPI card | Dashboard and future dashboard | Label, value, trend or supporting text, accessible status |
| Status badge | Dashboard, mailboxes, users, services | Text and icon in addition to color |
| Data table | Mailboxes, users, domains, teams, logs | Sorting, pagination, responsive list conversion, sticky header where useful |
| Search and filters | Mailboxes, users, inbox, logs | Server-side query, clear state, keyboard operation, visible active filters |
| Searchable multi-select | Create mailbox, create user, team management | Search, selected chips, clear action, large-list support |
| Context menu | Row actions and message actions | Permission-aware actions, focus management, escape close |
| Confirmation dialog | Delete and disable operations | Clear object identity, irreversible-action wording, focus trap |
| Message list row | Inbox | Sender, subject, preview, read state, time, attachment indicator |
| Reading pane | Inbox and message detail | Normalized HTML, plain text, isolated original layout, protected links |
| Attachment card | Message detail | Filename, type, size, security notice, authorized download |
| Alerts and toasts | All workflows | Success, warning, error, persistent details where recovery is required |
| Loading and empty states | All data screens | Stable layout, recovery action, no false success |

## Change control

A page patch must use shared components unless a reviewed exception is documented. Component API,
state, accessibility, or security changes require focused tests and updates to this matrix and the
UI foundation.
