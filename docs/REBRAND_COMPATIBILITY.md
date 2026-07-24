# Rebrand compatibility policy

## Purpose

The initial MailStack repository bootstrap changes public product identity, documentation, repository metadata, release archive naming, and user-facing copy while preserving established runtime contracts.

This is a compatibility-first migration.

## Identifiers intentionally preserved

The following identifiers remain unchanged during the bootstrap:

- `VIBMAIL_*` environment variables;
- `vibmail-*` systemd service and socket names;
- `/etc/vibmail` and related deployment paths;
- existing MariaDB schema, account, and view identifiers;
- existing log, lock, Maildir, and attachment paths;
- the `mailbox-app` source directory;
- the `vibmail.my` legacy deployment compatibility contract;
- compatibility protocol headers such as `X-VibMail-CSRF` and `X-VibMail-Request-ID`;
- the internal browser JavaScript namespace `VibMail`.

## Why they are preserved

Renaming runtime identifiers in the first public commit could break:

- deployed environment files;
- systemd units and operational commands;
- Nginx, Postfix, and Dovecot integration;
- database grants and SQL views;
- backup and restore archives;
- upgrade and rollback procedures;
- monitoring and automation;
- legacy installations.

## Future migration rule

A runtime identifier migration requires a separately approved release plan with:

1. complete old-to-new mapping;
2. migration and rollback scripts;
3. backup and restore compatibility;
4. service alias or transition support;
5. upgrade tests from every supported release;
6. clean-install tests;
7. operator documentation;
8. forensic, security, and performance re-audit.

No runtime identifier may be renamed through an uncontrolled global search and replace.


## Protocol compatibility guard

Public copy is rebranded to MailStack, but protocol and integration identifiers are not renamed. In particular, the contact form continues to send `X-VibMail-CSRF`, which maps to the WSGI key `HTTP_X_VIBMAIL_CSRF`. Renaming only one side would break CSRF validation. Any future protocol-header migration requires dual-read/dual-write compatibility and tests.
