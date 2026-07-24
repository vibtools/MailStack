# MailStack 1.2.1 safe upgrade guide

## Preconditions

- Use the signed/hash-verified 1.2.1 release directory.
- Confirm the current production backup can be read and its checksums pass.
- Do not edit `/opt/vibmail/app` experimentally.
- Keep `mail.vibmail.my`, Postfix, Dovecot, and the existing certificates unchanged.

## Controlled order

1. Run `bash scripts/audit_dependencies_v1_2_1.sh` from the isolated release directory while network access is available.
2. Run `sudo bash scripts/preflight_v1_2_1.sh --source /absolute/release/vib_mail_mvp`.
3. Run the existing full backup script and record the resulting backup directory.
4. Record current application/Maildir counts and service state.
5. Stop only `vibmail-ingestion` and `vibmail-gunicorn` for the application cutover. Mail delivery may continue into Maildir.
6. Deploy source using `scripts/deploy_application.sh`.
7. Install the release systemd units and Nginx app site only after backups exist.
8. Run `nginx -t`; restore the previous app site immediately if it fails.
9. Restart Gunicorn and ingestion.
10. Run `scripts/verify_v1_2_1.sh`.
11. Perform the manual acceptance checklist, including a real inbound message and two-user isolation test.

`scripts/upgrade_v1_2_1.sh` implements the same guarded sequence, but the recommended first production execution is supervised step-by-step.
