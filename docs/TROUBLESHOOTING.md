# Troubleshooting

## Installer plan fails

Run `./install.sh --help`, verify the domain/hostnames are distinct and below the mail domain, and provide a valid public IP. Use `--plan` before any privileged installation.

## TLS issuance fails

Confirm public DNS resolves to the server, ports 80/443 are reachable, no conflicting Nginx site owns the hostnames, and the ACME webroot is writable.

## External mail is not received

Check provider port-25 policy, firewall rules, MX records, Postfix logs and lookup results. Verify the mailbox is active and unknown recipients are rejected.

## Mail reaches Maildir but not the web inbox

Check `vibmail-ingestion`, the configured Maildir path, filesystem ownership, ingestion lock and application logs. Run the mailbox-storage and schema verification commands.

## Login works but mailbox is empty

Confirm the user has a mailbox membership and the mailbox status is active. Object-level access intentionally hides unassigned mailboxes.

## Contact form fails

Check `vibmail-public-contact`, local Postfix, the protected contact environment file, rate-limit state and Nginx proxy logs. Never paste the environment file into a public issue.

## Restore fails

Do not bypass archive or checksum validation. Confirm the backup set is complete, the target paths are safe and the documented service-state procedure was followed.

See `mailbox-app/docs/TROUBLESHOOTING.md` for application-specific checks.
