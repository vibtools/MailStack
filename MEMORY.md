# MailStack Permanent Project Memory

This document serves as the persistent AI memory for the MailStack project. It must be read at the start of any session and updated immediately when significant architectural, feature, or workflow changes occur.

## Tech Stack & Dependencies
*   **Operating System:** Designed for Ubuntu 24.04+ (deployment via bash scripts).
*   **Mail Transfer Agent (MTA):** Postfix (handles SMTP and internal delivery via LMTP).
*   **IMAP/POP3 Server:** Dovecot (handles LMTP from Postfix, and provides IMAP/POP3 access to users).
*   **Mail Authentication:** OpenDKIM (generates and verifies DKIM signatures for outbound/inbound mail).
*   **Database:** MariaDB (stores mail domains, mailboxes, aliases, and application data).
*   **Backend Application:** Django (Python 3.12+). Runs via Gunicorn.
*   **Web Server / Reverse Proxy:** Nginx (serves public static content, Django static/attachment files, and proxies Gunicorn).
*   **SSL/TLS:** Let's Encrypt / Certbot (for both Nginx HTTPS and Postfix/Dovecot TLS).
*   **Frontend (App):** HTML templates via Django, Bootstrap/custom CSS.

## Core Architecture & File Organization
*   **`install.sh`**: The primary single-node deployment script. It provisions users (`vmail`), packages, databases, and configures the entire stack natively without Docker.
*   **`deployment/templates/`**: Configuration templates for services (Nginx, Postfix, Dovecot, Systemd). These templates use `{{VAR}}` syntax, rendered dynamically by `scripts/render_template.py`.
*   **`mailbox-app/`**: The Django application.
    *   **`config/`**: Django settings (e.g., `production.py`).
    *   **`apps/ingestion/`**: Handles email parsing/processing logic.
    *   **`manage.py`**: Django management script.
*   **`public-site/`**: Contains static assets for the public-facing landing page/documentation.
*   **`/var/vmail/`**: Target directory on deployed servers where Dovecot stores maildir format emails.
*   **`/run/vibmail/`**: Runtime directory on deployed servers containing the Gunicorn socket.

## Current Active Features and Workflow
*   **System Users (Dynamic):** The deployment creates a system user `vmail`. Its dynamic UID/GID are resolved and injected into Postfix/Dovecot configurations to prevent permission mismatches (`first_valid_uid=10`, `static:$VMAIL_UID`).
*   **Gunicorn Socket Permissions:** Nginx accesses Gunicorn via `/run/vibmail/gunicorn.sock`. Gunicorn runs under systemd with `UMask=0007` so Nginx (`www-data` group) can access the socket.
*   **OpenDKIM Integration:** OpenDKIM automatically generates 2048-bit RSA keys during `install.sh` and links with Postfix as a milter to sign outbound mail securely.
*   **Development Workflow:** Any template updates (like Nginx `app.conf.tpl` or `99-vibmail.conf.tpl`) must be validated against `install.sh` to ensure correct rendering.
*   **Auto-Update System:** Implemented via GitHub Actions (`.github/workflows/auto_release.yml`) and a Dashboard UI page. Administrators can trigger an upgrade, which polls GitHub for the latest release, downloads the source/checksum zip files, and spawns the `sudo /opt/vibmail/app/scripts/upgrade.sh` script via a `sudoers.d` rule allowing the `vmail` user passwordless execution of the upgrade script. `upgrade.sh` reports JSON progress to `/tmp/vibmail_update_status.json`, polled by the frontend via AJAX.
*   **Design System & Typography:** The UI uses design tokens extracted from the Licora project for layout density, spacing, and sizing. Default font stack is `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto...`. Specific styles applied to Page Headers (16px/24px) and Tables (Items 12px, Headers 10px). **Architecture Note:** `foundation.css` acts as the base design system and MUST be loaded *before* `app.css` to prevent base resets from overriding specific component styles. `app.css` must not contain any generic `:root` or `body` resets.
---

> **Note to AI Agents:** Review this file when joining a context to understand the project architecture, particularly the specific permission structures (like `vmail` and OpenDKIM groups) established in the MailStack.
