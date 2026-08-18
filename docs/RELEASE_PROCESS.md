# Release process

1. Confirm copyright ownership and third-party license compatibility.
2. Confirm every maintained feature phase has a completed `documents/phases/PHASE-NNN-*.md` record.
3. Run `python scripts/manage_documents.py check`, `python scripts/test_documents.py`, and the feature documentation policy.
4. Run `python scripts/forensic_audit.py --root . --full`.
5. Run the online dependency audit in CI.
6. Test a clean installation on an isolated Ubuntu Server 24.04 LTS VPS.
7. Verify external inbound SMTP, login, authorization boundaries, live updates, safe HTML, and attachment downloads.
8. Build with `python scripts/build_release.py --root . --version 1.3.2` and verify the ZIP/checksum with `python scripts/verify_release.py`.
9. Merge the intended release commit to `main` and require a successful `main` push CI run for the exact SHA.
10. Create the matching `v<version>` tag on the current `main` head and push that tag. Do not create a release manually first.
11. The tag workflow validates tag/version/package identity, exact `main` head, successful `main` CI, and release absence; it then builds/verifies the deterministic archive and creates the GitHub Release with ZIP/SHA assets.
12. Verify the published release classification and attached checksum. RC versions must be pre-releases; stable versions are normal/latest releases.

`workflow_dispatch` is intentionally build/validation-only. Release automation never edits or clobbers an existing release. A version-marked source baseline is not a production-ready release until the clean-VPS and remaining operational acceptance gates pass.
