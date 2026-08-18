# Release process

1. Confirm copyright ownership and third-party license compatibility.
2. Confirm every maintained feature phase has a completed `documents/phases/PHASE-NNN-*.md` record.
3. Run `python scripts/manage_documents.py check`, `python scripts/test_documents.py`, and the feature documentation policy.
4. Run `python scripts/forensic_audit.py --root . --full`.
5. Run the online dependency audit in CI.
6. Test a clean installation on an isolated Ubuntu Server 24.04 LTS VPS.
7. Verify external inbound SMTP, login, authorization boundaries, live updates, safe HTML, and attachment downloads.
8. Build with `python scripts/build_release.py --root . --version 1.3.0-rc.5`.
9. Verify the ZIP and checksum with `python scripts/verify_release.py`.
10. Publish the source ZIP, checksum, release notes, user-document manifest, and exact Git commit/tag.

A release is not promoted from release candidate to production-ready until the clean-VPS acceptance test passes.
