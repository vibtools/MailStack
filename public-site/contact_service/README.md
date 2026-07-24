# MailStack Public Contact Service

Isolated WSGI service for the configured public website.

## Endpoints

- `GET /csrf/`
- `POST /`
- `GET /health/`

Nginx exposes these endpoints under `/api/contact/`.

## Required environment

- `CONTACT_DATABASE_PATH`
- `CONTACT_HASH_SECRET`
- `CONTACT_ADMIN_RECIPIENT`
- `CONTACT_FROM_ADDRESS`
- `CONTACT_PUBLIC_ORIGIN`
- `CONTACT_SENDMAIL_PATH`

## Security controls

- One-time CSRF token bound to an HttpOnly SameSite cookie
- Secure cookie requirement
- Strict JSON size and content-type checks
- Server-side field validation
- Honeypot and form-duration checks
- IP and email rate limiting
- Fixed notification recipient
- Header-injection protection
- SQLite WAL persistence
- Audit status for pending, sent and failed notifications
