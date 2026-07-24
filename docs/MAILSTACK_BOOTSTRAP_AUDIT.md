# MailStack repository bootstrap audit

**Audit date:** 2026-07-24  
**Source baseline:** `v1.3.0-rc.1`, commit `292f1eefc91f1e079d65491f464fb9d77603b4a7`  
**Target repository:** `vibtools/MailStack`

## Scope

The audit covered both uploaded ZIP archives, archive integrity, file inventories, source-manifest integrity, public branding, repository metadata, release tooling, Python and shell syntax, installer/template/operations contracts, contact-service tests, compatibility identifiers, and Windows-first-commit behavior.

## Findings corrected in this bootstrap

1. Canonical repository URLs pointed to the former repository.
2. Public product identity still used the former product name across documentation, templates, metadata, UI copy, and release artifacts.
3. `SOURCE_MANIFEST.sha256` made the checked-in forensic inventory permanently stale because the inventory generator did not exclude it.
4. Windows ZIP creation removed shell executable metadata. Installer tests directly executed `install.sh`, and release packaging depended on host executable bits.
5. An uncontrolled `VibMail` replacement would break the contact-form CSRF protocol by changing `X-VibMail-CSRF` without changing the WSGI key `HTTP_X_VIBMAIL_CSRF`.
6. Release archive and workflow artifact names still used the old public product name.

## Compatibility decision

The bootstrap changes public identity only. It preserves `VIBMAIL_*`, `vibmail-*` services, `/etc/vibmail`, database identifiers, legacy `vibmail.my` defaults, `X-VibMail-*` headers, and the internal `VibMail` JavaScript namespace.

## Verification completed

- Both uploaded ZIPs passed ZIP CRC/path-safety checks and contained identical 346-file trees.
- The original 345-entry source manifest matched every maintained file.
- Python syntax passed for all Python source files.
- Shell syntax passed for all 13 shell programs.
- Documentation, deployment-template, installer-contract, operations-contract, public-site rendering, and contact-service test gates passed on the source baseline after restoring executable permissions in the audit workspace.
- The final tree passes its non-dependency repository forensic gate.

## Verification not independently completed

The Django/pytest/Ruff/Bandit suite could not be re-executed in the audit container because the exact locked development dependencies were unavailable from the isolated package index. GitHub Actions on Ubuntu 24.04 and Python 3.12 remains the authoritative first-commit gate. Clean-VPS SMTP/LMTP acceptance and online vulnerability review also remain release-candidate gates.
