# Troubleshooting

## Installer plan fails

Run `./install.sh --help`, verify the domain/hostnames are distinct and below the mail domain, and provide a valid public IP. Use `--plan` before any privileged installation.

## TLS issuance fails

Confirm public DNS resolves to the server, ports 80/443 are reachable, no conflicting Nginx site owns the hostnames, and the ACME webroot is writable.

## External mail is not received

Check provider port-25 policy, firewall rules, MX records, Postfix logs and lookup results. Verify the mailbox is active and unknown recipients are rejected. If Postfix accepts the recipient but defers LMTP with `451 4.3.0` and Dovecot reports that a static userdb cannot verify user existence, verify the deployed Dovecot static userdb contains `allow_all_users=yes`; Postfix SQL lookup remains the recipient-validation boundary.

If a message is already deferred after correcting the LMTP configuration, validate Dovecot first and then retry the queue with `postqueue -f`; do not delete queued mail as a first response.

## Mail reaches Maildir but not the web inbox

Check `vibmail-ingestion`, the configured Maildir path, filesystem ownership, ingestion lock and application logs. Run the mailbox-storage and schema verification commands. In 1.3.0-rc.2 the official one-shot dry-run verifier can run while the live ingestion worker remains active; a real second ingestion worker must still be rejected by the exclusive lock.

## Login works but mailbox is empty

Confirm the user has a mailbox membership and the mailbox status is active. Object-level access intentionally hides unassigned mailboxes.

## Contact form fails

Check `vibmail-public-contact`, local Postfix, the protected contact environment file, rate-limit state and Nginx proxy logs. Never paste the environment file into a public issue.

## Restore fails

Do not bypass archive or checksum validation. Confirm the backup set is complete, the target paths are safe and the documented service-state procedure was followed.

See `mailbox-app/docs/TROUBLESHOOTING.md` for application-specific checks.


## Installer fails during Django startup with `/var/log/vibmail` permission denied

MailStack 1.3.0-rc.2 does not change the host-wide `/var/log` mode. Confirm `/var/log` is a real traversable system directory and `/var/log/vibmail` is owned by the `vmail` runtime with its expected restricted mode. Do not make `/var/log` globally restrictive as an application-specific hardening step.

## Repair reports inconsistent bootstrap state

Do not delete an existing administrator or mail-server row to force repair through. `--repair` intentionally preserves complete objects but rejects mixed application/mail-server/filesystem state for system mailboxes and rejects a requested administrator name that does not match an existing valid administrator. Inspect the partial state and restore from the installer backup or a verified application backup as appropriate.
