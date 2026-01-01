 # Guardian Bot — API Reference (Full)

This document is a developer reference for the REST and WebSocket APIs implemented by the Guardian Bot backend and dashboard. It lists every registered route (as of the running dev server), required permissions, request/response shapes, and usage examples you can use to wire the frontend or write tests.

Base URL (dev): http://127.0.0.1:8001

Authentication/Authorization summary
- Most API endpoints require an Authorization header: `Authorization: Bearer <token>`.
- The token returned by `/auth/telegram` in this project is a mock token of the form `mock-jwt-token-<tg_user_id>`; replace with a real JWT in production.
- Superadmin-only endpoints are under `/api/v1/*` and require elevated privileges (see `verify_superadmin`).
- Group-scoped endpoints use per-group permissions enforced by `verify_group_permission(group_id, permission, current_user)`.

Error handling quick guide
- 200: OK (successful response)
- 201: Created (resource created)
- 400: Bad Request (validation error)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (permission denied)
- 404: Not Found
- 500: Internal Server Error

---

## Summary of registered routes (high level)

The running app exposes the following logical groups of endpoints:

- Authentication: `/auth/telegram`, `/api/v1/auth/token`, `/api/v1/auth/refresh`
- Group APIs: `/api/groups/{group_id}/...` (bans, blacklist, rules, automod, welcome, members, chat, commands)
- Admin / Superadmin APIs: `/api/v1/...` (admin management, global stats, group admin management)
- WebSocket: `/ws/logs/{group_id}` (real-time logs)
- Static dashboard: `/` and `/dashboard`

Below is a detailed reference for each endpoint (path, method, auth, params, body, response shape, examples).

---

## Authentication

### POST /auth/telegram
- Purpose: Validate Telegram login widget data and return a mock token and user object.
- Auth: none
- Request JSON (TelegramAuthData):
  - id (int) — Telegram user id
  - first_name (string)
  - username (string, optional)
  - photo_url (string, optional)
  - auth_date (int, unix timestamp)
  - hash (string) — Telegram widget hash
- Response 200:
  - { token: "mock-jwt-token-<id>", user: { id, first_name, username, photo_url } }
- Errors: 401 invalid auth data, 500 internal

Example:
```json
POST /auth/telegram
{
  "id": 12345,
  "first_name": "Alice",
  "auth_date": 1700000000,
  "hash": "..."
}
```

Response:
```json
{
  "token": "mock-jwt-token-12345",
  "user": { "id": 12345, "first_name": "Alice" }
}
```

Notes: In this repo `src/web/auth.py` implements the router. In production swap the mock token with real JWT issuance.

---

## Health & Static

### GET /
- Purpose: Serve the main dashboard page (static)
- Auth: none

### GET /health
- Purpose: Health check
- Auth: none
- Response: { status: "ok", timestamp: "...", service: "guardian-bot-api", version: "2.1.0" }

---

## Frontend helper

### GET /api/frontend/groups
- Purpose: Return a lightweight list of groups used by the dashboard's group selector.
- Method: GET
- Auth: Authorization recommended
- Response: { data: [ { group_id, title, member_count, is_premium } ], total, page, per_page }

---

## Group-scoped API — /api/groups/{group_id}
Common notes:
- `group_id` is the Telegram group id (use negative ints for channels/groups: e.g. -1001234567890)
- Most endpoints require `Authorization: Bearer <token>` and a permission check like `verify_group_permission(group_id, GroupPermission.X, current_user)`.

### GET /api/groups/{group_id}
- Purpose: Get group configuration and summary stats.
- Auth: logged-in admin (superadmin or group admin with view permissions)
- Response: group config object with fields like `welcome_msg`, `anti_spam`, `helpline_group_id`, `stats: { members, bans, warnings }`.

### Auto-moderation

GET /api/groups/{group_id}/automod
- Purpose: Get auto-moderation configuration
- Auth: manage_auto_mod or equivalent
- Response: AntiSpamConfig object

PUT /api/groups/{group_id}/automod
- Purpose: Update auto-moderation configuration
- Auth: manage_auto_mod
- Body: Auto-moderation config (JSON)
- Response: { status: "success", config: { ... } }

### Bans

GET /api/groups/{group_id}/bans
- Purpose: List banned users in the group
- Auth: manage_bans or superadmin
- Query params: optional page/limit
- Response: { data: [ BanSchema ], total }

POST /api/groups/{group_id}/commands/ban
- Purpose: Ban a user (calls Telegram API and persists ban)
- Auth: manage_bans
- Body: { user_id: int, reason?: string }
- Response: { status: "success", user_id }

POST /api/groups/{group_id}/commands/unban
- Purpose: Unban a user (Telegram unban + remove DB record)
- Auth: manage_bans
- Body: { user_id: int, reason?: string }
- Response: { status: "success", user_id }

---

### Blacklist (media)

GET /api/groups/{group_id}/blacklist
- Purpose: List blacklisted media items (stickers/GIFs)
- Auth: manage_blacklist
- Response: [ BlacklistedItemSchema ]

POST /api/groups/{group_id}/blacklist
- Purpose: Add media to blacklist
- Auth: manage_blacklist
- Body: { file_unique_id, file_id, type: 'sticker'|'gif'|'sticker_pack', pack_name?: string }
- Response: { status: "success", id }

GET /api/groups/{group_id}/blacklist/preview/{item_id}
- Purpose: Return preview URL for a blacklisted item
- Auth: manage_blacklist
- Response: { url: "https://..." }

DELETE /api/groups/{group_id}/blacklist/{item_id}
- Purpose: Remove a blacklisted item
- Auth: manage_blacklist
- Response: { status: "success" }

---

### Chat & replies

GET /api/groups/{group_id}/chat
- Purpose: Fetch recent chat history (persisted via `add_chat_message`)
- Auth: view permission or superadmin
- Query params: limit, before, after
- Response: [ ChatMessageSchema ]

POST /api/groups/{group_id}/chat/reply
- Purpose: Send a reply via bot and persist it
- Auth: appropriate send permission
- Body: { user_id: int, user_name: string, text: string }
- Response: { status: "success", message_id }

---

### Members

GET /api/groups/{group_id}/members
- Purpose: Paginated member listing (search, filters)
- Auth: manage_members or superadmin
- Query: page, per_page, search
- Response: { data: [ MemberSchema ], total, page, per_page }

---

### Rules

GET /api/groups/{group_id}/rules
- Purpose: List rules
- Auth: manage_rules or view
- Response: [ RuleSchema ]

POST /api/groups/{group_id}/rules
- Purpose: Create rule
- Auth: manage_rules
- Body: { title: string, text: string, enabled?: bool }
- Response: { status: "success", rule_id }

PUT /api/groups/{group_id}/rules/{rule_id}
- Purpose: Update rule
- Auth: manage_rules
- Body: rule fields
- Response: { status: "success" }

DELETE /api/groups/{group_id}/rules/{rule_id}
- Purpose: Delete rule
- Auth: manage_rules
- Response: { status: "success" }

---

### Welcome messages

GET /api/groups/{group_id}/welcome
- Purpose: Get welcome configuration
- Auth: manage_bot_config or view
- Response: { welcome_msg, enabled }

PUT /api/groups/{group_id}/welcome
- Purpose: Update welcome configuration
- Auth: manage_bot_config
- Body: { welcome_msg: string, enabled?: bool }
- Response: { status: "success" }

---

### Moderation commands (other)

POST /api/groups/{group_id}/commands/kick
- Body: { user_id, reason }
- Auth: manage_members

POST /api/groups/{group_id}/commands/mute
- Body: { user_id, duration_minutes, reason }
- Auth: manage_members

POST /api/groups/{group_id}/commands/warn
- Body: { user_id, reason }
- Auth: manage_warns or manage_members
- Response: { warnings: n, action: 'warned'|'banned' }

POST /api/groups/{group_id}/commands/pin
POST /api/groups/{group_id}/commands/unpin
POST /api/groups/{group_id}/commands/purge
- These perform their respective Telegram actions and log the operation.

---

## Admin / Superadmin (`/api/v1`)

All `/api/v1` endpoints require Authorization: Bearer <access_token>. Many are superadmin-only.

### POST /api/v1/auth/token
- Purpose: obtain access/refresh tokens (OAuth2/password). See `src/web/superadmin_api.py` for details.

### POST /api/v1/auth/refresh
- Purpose: refresh tokens

### GET /api/v1/my-groups
- Purpose: list groups available to current admin (superadmins see all)

### GET /api/v1/my-permissions/{group_id}
- Purpose: return the caller's permissions for the group

### Admin management (superadmin)
- GET/POST/PUT/DELETE on `/api/v1/superadmin/admins` — create/update/list/delete admin accounts
- PATCH `/api/v1/superadmin/admins/{user_id}/telegram` — set Telegram id for admin

### GET /api/v1/groups/{group_id}/bans
- Admin-facing bans listing (same data as `/api/groups/{group_id}/bans` but with v1 auth flows)

### GET /api/v1/groups/{group_id}/recent-logs
- Purpose: recent moderation logs (limit param supported)

---

## WebSocket — real-time logs

URL: ws://{host}/ws/logs/{group_id}?token=<token>
- Auth: token passed as query param (raw token) — the websocket handler decodes and verifies the token.
- After authentication, server pushes log entries: { admin_id, action, user_id, reason, timestamp }

---

## Examples (curl / JS)

Authenticate (mock):
```bash
curl -X POST http://127.0.0.1:8001/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"id":12345,"first_name":"Alice","auth_date":1700000000,"hash":"..."}'
```

List bans for a group:
```bash
curl -H "Authorization: Bearer mock-jwt-token-12345" \
  http://127.0.0.1:8001/api/groups/-100123456789/bans
```

Unban a user:
```bash
curl -X POST -H "Authorization: Bearer mock-jwt-token-12345" \
  -H "Content-Type: application/json" \
  -d '{"user_id":98765,"reason":"Appeal accepted"}' \
  http://127.0.0.1:8001/api/groups/-100123456789/commands/unban
```

WebSocket (JS):
```js
const ws = new WebSocket('ws://127.0.0.1:8001/ws/logs/-100123456789?token=mock-jwt-token-12345');
ws.onmessage = (e) => console.log('log', JSON.parse(e.data));
```

---

## Notes, verification & next steps

- I generated this reference by querying the running FastAPI app's registered routes and reading handlers. Keep `src/models/*` Pydantic models in sync so `/openapi.json` is fully descriptive.
- Recommended follow-ups:
  - Replace mock auth with proper JWT issuance (so tokens include admin id and scopes).
  - Expand response models with Pydantic schemas where missing so OpenAPI docs are complete.
  - Add small pytest smoke tests for: auth, list groups, list bans, unban flow, recent-logs, websocket handshake.
  - Consider changing WebSocket auth to use Authorization header instead of query param for security.

---

If you want, I will commit this file into `docs/` (done) and mark the API reference task completed; I can also generate an OpenAPI export or Postman collection next.
- Auth: admin of group or superadmin
- Response example:

{
  "group_id": -1003447608920,
  "group_name": "Bot Testing",
  "member_count": 42,
  "ban_count": 1,
  "messages_today": 127,
  "online_count": 5
}

### GET /api/groups/{group_id}/members?skip=0&limit=20&q=search

- Purpose: paginated members list
- Auth: admin or superadmin
- Query params:
  - skip (int) — offset
  - limit (int) — page size
  - q (string, optional) — simple search applied to username/full_name
- Response (200):

{
  "total": 124,
  "items": [
    {"id": "692a...", "user_id": 12345, "full_name": "Alice", "username": "alice", "status": "member", "join_date": "2025-12-01T12:00:00Z", "last_active": "2025-12-13T10:20:00Z", "message_count": 34},
    ...
  ]
}

Errors:
- 401 Unauthorized if no token
- 403 Forbidden if caller not allowed for this group

### GET /api/groups/{group_id}/bans

- Response: list of bans (see `BanSchema` above)

### GET /api/groups/{group_id}/chat?limit=100

- Purpose: return recent chat messages for the group (dashboard chat panel)
- Auth: admin or superadmin
- Response: array of `ChatMessageSchema` items:
  - user_id, user_name, text, is_admin (bool), is_deleted (bool), created_at (ISO)

### POST /api/groups/{group_id}/chat/reply

- Purpose: Send a reply message (bot posts) — request is proxied to bot or stored as chat message
- Auth: admin
- Body: ChatMessageRequest
  - user_id: int
  - user_name: str
  - text: str
- Response: { "ok": true, "message_id": 123456 }

### Blacklist endpoints

GET /api/groups/{group_id}/blacklist
- Response: array of BlacklistedItemSchema

POST /api/groups/{group_id}/blacklist
- Body: BlacklistItemRequest: { file_unique_id, file_id, type, pack_name }
- Response: { "ok": true }

DELETE /api/groups/{group_id}/blacklist/{item_id}
- Response: { "ok": true }

GET /api/groups/{group_id}/blacklist/preview/{item_id}
- Response: preview data for the blacklisted item (image URL, metadata)

### Rules

GET /api/groups/{group_id}/rules
- Response: list of `RuleSchema` (text, position, created_at)

POST /api/groups/{group_id}/rules
- Body: RuleCreateRequest (text, position optional)
- Response: created RuleSchema

PUT /api/groups/{group_id}/rules/{rule_id}
- Body: RuleUpdateRequest (text, position)
- Response: updated RuleSchema

DELETE /api/groups/{group_id}/rules/{rule_id}
- Response: { "ok": true }

### Auto-moderation

GET /api/groups/{group_id}/automod
- Response: AutoModerationConfig

PUT /api/groups/{group_id}/automod
- Body: AutoModerationConfig
- Response: { "ok": true }

### Welcome message

GET /api/groups/{group_id}/welcome
- Response: WelcomeConfig (welcome message, enabled, etc.)

PUT /api/groups/{group_id}/welcome
- Body: WelcomeConfig
- Response: { "ok": true }

### Scan messages (analytics)

POST /api/groups/{group_id}/scan
- Purpose: trigger server-side message scan/analysis
- Body: ScanMessagesRequest (options)
- Response: { "scanned": 123, "results": {...} }

### GET /api/groups/{group_id}/stats

- Response model: `StatsResponse` — includes counts and derived metrics used by dashboard

### GET /api/groups/{group_id}/logs

- Response: array of `ModerationLog` entries (admin_id, user_id, action, reason, timestamp, etc.)

### Moderation command endpoints (POST)

These endpoints accept command-specific request models. They perform actions via the bot and also log the action in the DB.

- POST /api/groups/{group_id}/commands/ban
  - Body: BanUserRequest { user_id, reason }
  - Response: { "ok": true }

- POST /api/groups/{group_id}/commands/kick
  - Body: KickUserRequest
  - Response: { "ok": true }

- POST /api/groups/{group_id}/commands/mute
  - Body: MuteUserRequest { user_id, duration_minutes, reason }
  - Response: { "ok": true }

- POST /api/groups/{group_id}/commands/warn
  - Body: WarnUserRequest { user_id, reason }
  - Response: { "ok": true }

- POST /api/groups/{group_id}/commands/purge
  - Body: PurgeMessagesRequest { count }
  - Response: { "deleted": <n> }

- POST /api/groups/{group_id}/commands/pin
  - Body: PinMessageRequest { message_id, disable_notification }
  - Response: { "ok": true }

- POST /api/groups/{group_id}/commands/unpin
  - Body: { message_id }
  - Response: { "ok": true }

---

## Frontend helper endpoints

### GET /api/frontend/groups (legacy)

- Purpose: older frontend helper; may return groups optimized for the dashboard. Prefer `/api/v1/my-groups`.

### GET /api/v1/my-groups

- Purpose: used by dashboard to show only groups the logged-in admin can manage.
- Auth: admin token required.

Response example:

{
  "items": [ { "group_id": -100..., "group_name": "...", "member_count": 42 }, ... ]
}

---

## WebSocket: real-time logs

### ws://{host}/ws/logs/{group_id}

- Purpose: stream real-time moderation/log events for a group via Redis pub/sub.
- Auth: currently not enforced in the handler — a token query param is suggested (implementation note). Add `?token=<jwt>` and validate on handshake.
- Behavior: subscribes to Redis channel `group_logs:{group_id}` and forwards message.data to connected clients. Message payloads are expected to be JSON strings.

Example message received on websocket (text):

{"id":"693c10a6...","admin_id":123,"user_id":456,"action":"ban","reason":"spam","timestamp":"2025-12-13T10:20:00Z","group_id":-100...}

Notes & TODOs:
- Authenticate the websocket handshake — accept token param or use secure subprotocols.
- Ensure Redis `settings.REDIS_URL` is reachable.

---

## Common request/response patterns & error codes

- 200 OK — successful GET/POST (usually returns JSON)
- 201 Created — resource creation (admins/rules)
- 400 Bad Request — invalid parameters or validation errors
- 401 Unauthorized — missing or invalid JWT
- 403 Forbidden — insufficient permissions (not superadmin or not group admin)
- 404 Not Found — resource not found
- 500 Internal Server Error — server-side error (check logs `/tmp/uvicorn.log` during dev)

All datetime values are returned in ISO 8601 strings. All MongoDB `_id` fields are normalized to `id` (string) in endpoints that return document lists to avoid serialization issues.

---

## Quick examples

Fetch dashboard groups (frontend):

Request headers:

Authorization: Bearer <access_token>

GET /api/v1/my-groups

Response:

[
  {"group_id": -1003447608920, "group_name": "Bot Testing", "member_count": 42}
]

Fetch members (paginated):

GET /api/groups/-1003447608920/members?skip=0&limit=20
Authorization: Bearer <access_token>

Response:

{
  "total": 42,
  "items": [ { "id":"692a...", "user_id": 123, "full_name":"Alice" }, ... ]
}

Ban a user (admin action):

POST /api/groups/-1003447608920/commands/ban
Authorization: Bearer <access_token>
Body JSON: { "user_id": 12345, "reason": "Spam" }

Response: { "ok": true }

---

## Implementation notes & follow-ups

- The docs above reflect the endpoints implemented in `src/web/api.py` and `src/web/superadmin_api.py` and DB helpers in `src/services/database.py`.
- WebSocket authentication is currently missing — add token validation on handshake before using in production.
- Some frontend files still contain mock charts/time-series that should be wired to server-side endpoints for analytics.
- Add example Postman collection (JSON) in a follow-up if you want an importable collection.

If you'd like, I can:
- generate a Postman collection JSON / OpenAPI specification from the routes,
- add example curl commands for each endpoint,
- or implement websocket handshake authentication and update the docs with details.

---

Generated by the codebase audit on 2025-12-13.

---

## Additional reference: Permissions, Admin APIs, Audit & WebSocket auth

The following sections document recent additions implemented in the codebase: permission enums, admin-permissions management endpoints, audit logging behavior, and secure websocket handshake.

### Permission models (server-side)

Defined in `src/models/permissions.py`.

- GlobalPermission (enum):
  - manage_superadmins, view_all_groups, manage_all_groups, view_system_stats, manage_system_settings
- GroupPermission (enum):
  - view_group, manage_members, manage_admins, manage_blacklist, manage_rules, manage_welcome, manage_auto_mod, view_logs, manage_settings, manage_warns, manage_bans

These are used by the admin UI and server-side authorization checks.

### Admin Permissions API (new)

All routes are under `/api/v1` and require Authorization: Bearer <access_token>.

1) GET /api/v1/groups/{group_id}/admins
- Description: List admin members for the group and their assigned permissions.
- Auth: superadmin or group admin with `manage_admins` permission.
- Response: array of objects: { user_id, full_name, username, permissions: ["manage_members","view_logs"], status }

2) PUT /api/v1/groups/{group_id}/admins/{admin_id}/permissions
- Description: Replace permission set for the admin in the given group (upsert).
- Auth: superadmin or group admin with `manage_admins` permission.
- Body: JSON array of permission strings (must be values from GroupPermission)
- Response: { status: "success", message: "Permissions updated successfully" }

3) GET /api/v1/my-permissions/{group_id}
- Description: Query the caller's permissions for the group. Returns full permission list for superadmins.
- Auth: any logged-in admin (valid access token)
- Response: { group_permissions: ["manage_members","view_logs"] }

Notes:
- The server stores per-admin permissions in the `admin_permissions` collection (documents contain telegram_id, group_id, permissions array, updated_at).

### Audit logging

Purpose: track all admin actions and provide an audit trail.

- Logs are persisted to `audit_logs` collection via `src/services/database.insert_audit_log` and `src/services/audit.log_admin_action`.
- Middleware in `src/web/api.py` will attempt to create audit entries for requests under `/api/v1` when an Authorization header is present. The middleware is non-blocking in case logging fails.

Audit log entry example:

{
  "admin_id": "693c1d0dfd2f1216aa917425",
  "action": "POST_/api/v1/groups/-1003447608920/admins/123/permissions",
  "target_id": "123",
  "group_id": -1003447608920,
  "details": { "url": "https://...", "method": "PUT", "body": ["manage_members","view_logs"] },
  "timestamp": "2025-12-13T11:20:30.123456",
  "ip_address": "203.0.113.5",
  "user_agent": "Mozilla/5.0 ..."
}

Retention, redaction and access controls for audit_logs are left to deployment configuration and are recommended for production.

### WebSocket authentication (updated)

The logs websocket at `/ws/logs/{group_id}` now requires a JWT token on the query string: `/ws/logs/{group_id}?token=<jwt>`.

- Server-side behavior:
  - Decodes & verifies token using same secret and algorithms as REST auth (via `src/services/auth.get_current_user`).
  - Superadmins can subscribe to any group.
  - Non-superadmin users must have a `telegram_id` in their admin user doc and be a group admin (members.status == "admin").
  - After authorization the server subscribes to Redis channel `group_logs:{group_id}` and forwards messages to the client.

Client example (JavaScript):

```js
const ws = new WebSocket(`ws://localhost:8001/ws/logs/${groupId}?token=${accessToken}`);
ws.onmessage = (ev) => console.log('log:', JSON.parse(ev.data));
ws.onopen = () => console.log('connected');
ws.onclose = (e) => console.log('closed', e);
```

If the handshake fails the server will close the connection with a 4401/4403 close code and a reason.

### Database: new/important collections

- `admin_permissions` — stores per-admin permissions for groups: { telegram_id, group_id, permissions: [..], updated_at }
- `audit_logs` — stores audit entries (see example above)

Make sure your MongoDB user has write permissions to create these collections during startup.

### Example curl sequences

1) Get tokens

```bash
curl -X POST http://localhost:8001/api/v1/auth/token \
  -d "username=superadmin" -d "password=supersecurepassword"
```

Response contains `access_token`.

2) List groups visible to current admin

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8001/api/v1/my-groups
```

3) Get group admins

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8001/api/v1/groups/-1003447608920/admins
```

4) Update admin permissions

```bash
curl -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '["manage_members","view_logs"]' \
  http://localhost:8001/api/v1/groups/-1003447608920/admins/123/permissions
```

---

If you want, I can now:
- generate an OpenAPI spec covering the new admin-permissions endpoints and websocket security note,
- create a minimal integration test that requests a token and exercises the admin-permissions endpoints,
- or update the frontend to call the new `/api/v1/my-permissions/{group_id}` and permission-management endpoints.

