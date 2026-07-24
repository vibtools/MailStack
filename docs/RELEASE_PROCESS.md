# Release process

1. Confirm copyright ownership and third-party license compatibility.
2. Run `python scripts/forensic_audit.py --root . --full`.
3. Run the online dependency audit in CI.
4. Test a clean installation on an isolated Ubuntu Server 24.04 LTS VPS.
5. Verify external inbound SMTP, login, authorization boundaries, live updates, safe HTML, and attachment downloads.
6. Build with `python scripts/build_release.py --root . --version 1.3.0-rc.1`.
7. Verify the ZIP and checksum with `python scripts/verify_release.py`.
8. Publish the source ZIP, checksum, release notes, and exact Git commit/tag.

A release is not promoted from release candidate to production-ready until the clean-VPS acceptance test passes.
