# API and route reference

MailStack does not expose a public REST API in this release. The supported interfaces are server-rendered web routes, health endpoints and the public contact endpoint.

## Application routes

| Area | Typical route | Access |
|---|---|---|
| Login/logout | `/accounts/login/`, `/accounts/logout/` | public/authenticated |
| Dashboard | `/` | authenticated |
| Mailboxes | `/mailboxes/` | authenticated, object scoped |
| Mailbox administration | `/mailboxes/create/`, status/delete routes | authorized administrators |
| Messages | `/messages/`, detail/read/delete routes | authenticated, object scoped |
| Live updates | `/messages/live/` | authenticated, membership filtered |
| User management | `/accounts/users/` | MailStack administrators |
| Health | `/health/` | service probe |
| Readiness | `/ready/` | service/database probe |

Route names and exact patterns are defined in `mailbox-app/config/urls.py` and each app's `urls.py`.

## Public contact endpoint

`POST /api/contact/` accepts a JSON contact submission protected by a one-time CSRF token, SameSite cookie, honeypot, timing checks, size limits and rate limits. The service sends only a fixed local notification through `/usr/sbin/sendmail`.

## Compatibility rule

New programmatic APIs require explicit authentication, authorization, rate-limit, privacy and backward-compatibility design. Existing web routes must not be repurposed as undocumented APIs.
