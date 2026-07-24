# MailStack v1.2.1 Known Issues and Acceptance Limitations

## Known application defects

None identified after the v1.2.1 security-hotfix regression and forensic audit cycle.

## Accepted dependency scope decision

Bleach 6.4.0 is the current security-fix release. `GHSA-g75f-g53v-794x` concerns email linkification only when `parse_email=True`. MailStack explicitly sets `parse_email=False`; the online audit script verifies that invariant through AST inspection before applying the scoped exception.

## Live acceptance still required

These are deployment gates, not known application defects:

1. Run the online dependency audit on the VPS.
2. Verify the v1.2.1 manifest and ZIP hash after upload.
3. Execute read-only preflight.
4. Create and verify the complete production backup.
5. Perform the supervised upgrade and post-deployment verification.
6. Repeat real inbound-email, live notification, copy, user-isolation, auto-read, delete-permission, and rollback-readiness tests.

Final live status remains pending until every item in `V1_2_1_ACCEPTANCE_CHECKLIST.md` passes.
