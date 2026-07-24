# MailStack 1.2.1 security hotfix

Version 1.2.1 is the installable security-hotfix release for the v1.2.0 Team Access, Live Inbox, and Branding feature set.

## Dependency corrections

- Upgraded `bleach` from 6.3.0 to 6.4.0 for the current sanitizer security fixes.
- Upgraded `python-dotenv` from 1.2.1 to 1.2.2 for the symlink-handling security correction.
- Preserved Django 5.2.15.

## Bleach email-linkification advisory scope

The remaining Bleach advisory `GHSA-g75f-g53v-794x` applies only when untrusted text is processed with email linkification enabled (`parse_email=True`). MailStack does not enable that mode. The only `Linker` call explicitly sets `parse_email=False`, and regression coverage confirms ordinary URLs are linked while email addresses are not automatically converted to `mailto:` links.

The online dependency-audit script validates this source-level invariant using the Python AST before applying the narrowly scoped advisory exception. Any future Linker call or change to `parse_email` causes the audit to fail.

## Release rule

The rejected v1.2.0 archive must not be installed. Only the hash-verified v1.2.1 release may proceed to the online dependency audit, preflight, backup, and supervised production upgrade.
