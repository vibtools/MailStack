# Configuration

Production configuration is loaded from `/etc/vibmail/vibmail.env`. Mandatory values include a high-entropy Django secret, trusted hosts/origins, MariaDB application database credentials, and the fixed MailStack identity/storage values.

Production requires:

```text
DB_ENGINE=mariadb
DB_NAME=vibmail_app
DB_HOST=127.0.0.1
DB_PORT=3306
MAILSERVER_INTEGRATION_ENABLED=true
MAILSERVER_DB_NAME=vibmail
MAIL_DOMAIN=vibmail.my
MAIL_STORAGE_ROOT=/var/vmail
ATTACHMENT_STORAGE_ROOT=/var/lib/vibmail/attachments
```

The application DB account must have schema rights on `vibmail_app` only and the narrow cross-schema grants defined in `deployment/mariadb/create_vibmail_app_database.sql.template`.
