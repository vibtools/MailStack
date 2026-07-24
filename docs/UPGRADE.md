# Upgrade policy

1. Back up both MariaDB schemas, `/var/vmail`, attachments, environment files, mail configuration, Nginx configuration, systemd units, and certificates.
2. Verify the backup checksum on another machine.
3. Review release notes and migrations.
4. Stage the new source outside `/opt/vibmail/app`.
5. Run tests, source-safety audit, and release verification.
6. Use the versioned application upgrade scripts or a reviewed maintenance procedure; the clean-install path must not be used to overwrite an unreviewed production stack.
7. Run migration, Postfix-view, Maildir, health, login, authorization, live-update, attachment, and real inbound-mail acceptance tests.
8. Roll back immediately if a mandatory gate fails.

Legacy v1.2.1 upgrade and rollback documents remain under `mailbox-app/docs/` for existing MailStack deployments.
