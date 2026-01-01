# Guardian Bot — API Reference (Full)

This is the authoritative developer reference for the Guardian Bot backend and dashboard as implemented in this repository. It documents REST and WebSocket routes, required permissions, request/response shapes, examples, and the cross-process contract used to keep the web dashboard and the Telegram bot synchronized.

Base URL (dev): http://127.0.0.1:8001

Last updated: 2025-12-17

Quick summary:
- Auth: mock JWT in dev (`mock-jwt-token-<tg_user_id>`) from `/auth/telegram`. Replace with real JWTs in production.
- WebSocket auth uses a token query param: `?token=<jwt>` (server decodes & verifies it during handshake).
- Cross-process sync: Actions taken via REST publish a JSON action event to Redis channel `guardian:actions` so a running bot process can pick them up and apply Telegram-side effects; conversely, bot-side commands call the same server service to persist state and publish audit logs.

---

## Authentication & Permissions

- Most routes require an Authorization header: `Authorization: Bearer <token>`.
- Superadmin routes live under `/api/v1/*` and require elevated privileges.
- Group-scoped permissions are enforced by `verify_group_permission(group_id, permission, current_user)`.

Permission enums (reference):
- GroupPermission: view_group, manage_members, manage_admins, manage_blacklist, manage_rules, manage_welcome, manage_auto_mod, view_logs, manage_settings, manage_warns, manage_bans
- GlobalPermission: manage_superadmins, view_all_groups, manage_system_settings, view_system_stats

Error handling quick guide:
- 200: OK
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

All datetime values are ISO 8601 strings. MongoDB `_id` fields are normalized to `id` (string) in responses.

---

## High-level route groups

- Authentication: `/auth/telegram`, `/api/v1/auth/token`, `/api/v1/auth/refresh`
- Group APIs: `/api/groups/{group_id}/...` (bans, blacklist, rules, automod, welcome, members, chat, commands)
- Admin / Superadmin APIs: `/api/v1/...` (admins, my-groups, my-permissions)
- WebSocket: `/ws/logs/{group_id}` (real-time logs)
- Static dashboard: `/` and `/dashboard`

---

## Authentication

### POST /auth/telegram
- Purpose: Validate Telegram login widget payload in dev and return a mock token and user object.
- Auth: none
- Body (TelegramAuthData):
  - id (int)
  - first_name (string)
  - username (string, optional)
  - photo_url (string, optional)
  - auth_date (int)
  - hash (string)
- Response 200:
  - { token: "mock-jwt-token-<id>", user: { id, first_name, username?, photo_url? } }

Example:
```
POST /auth/telegram
{ "id": 12345, "first_name": "Alice", "auth_date": 1700000000, "hash": "..." }
```

Response:
```
{ "token": "mock-jwt-token-12345", "user": { "id": 12345, "first_name": "Alice" } }
```

Notes: In production replace this with real JWT issuance (see `src/services/auth.py`).

---

## Health & Static

### GET /
- Purpose: Serve static dashboard page
- Auth: none

### GET /health
- Purpose: Health check
- Auth: none
- Response: { status: "ok", timestamp: "...", service: "guardian-bot-api", version: "2.1.0" }

---

## Group-scoped API — /api/groups/{group_id}

Common notes:
- `group_id` is the Telegram group id (use negative ints for supergroup ids: e.g. -1001234567890). Tests may pass string-like ids; the server accepts strings but production callers should use integers.
- Most endpoints require `Authorization: Bearer <token>` and a permission check.

### GET /api/groups/{group_id}
- Purpose: Get group configuration and summary stats.
- Auth: logged-in admin (superadmin or group admin with view permissions)
- Response: group config object (welcome_msg, anti_spam, helpline_group_id, stats)

### Automod
GET /api/groups/{group_id}/automod — Get auto-moderation config (manage_auto_mod)
PUT /api/groups/{group_id}/automod — Update auto-moderation config (manage_auto_mod)

### Bans
GET /api/groups/{group_id}/bans — list bans (manage_bans)
POST /api/groups/{group_id}/commands/ban — ban a user and persist it (manage_bans)
POST /api/groups/{group_id}/commands/unban — unban user and remove ban record (manage_bans)

### Blacklist (media)
GET /api/groups/{group_id}/blacklist — list blacklisted items (manage_blacklist)
POST /api/groups/{group_id}/blacklist — add blacklisted item (manage_blacklist)
GET /api/groups/{group_id}/blacklist/preview/{item_id} — preview URL (manage_blacklist)
DELETE /api/groups/{group_id}/blacklist/{item_id} — remove (manage_blacklist)

### Chat & replies
GET /api/groups/{group_id}/chat — fetch recent chat
POST /api/groups/{group_id}/chat/reply — send a reply (bot posts) and persist message (manage_members/send)

### Members
GET /api/groups/{group_id}/members — paginated member listing (manage_members)

### Rules
GET /api/groups/{group_id}/rules — list rules
POST /api/groups/{group_id}/rules — create rule (manage_rules)
PUT /api/groups/{group_id}/rules/{rule_id} — update rule (manage_rules)
DELETE /api/groups/{group_id}/rules/{rule_id} — delete rule (manage_rules)

### Welcome messages
GET /api/groups/{group_id}/welcome — get welcome config (manage_bot_config)
PUT /api/groups/{group_id}/welcome — update welcome (manage_bot_config)

### Moderation commands (HTTP endpoints that both persist state and trigger Telegram-side effects)

All moderation command endpoints call a shared service `perform_mod_action(...)` (see `src/services/mod_actions.py`). The service does DB updates, writes an audit log, and publishes a global Redis action event so a running bot process can apply the Telegram-side effect.

- POST /api/groups/{group_id}/commands/ban
  - Body: { user_id: int, reason?: string }
  - Auth: manage_bans
  - Response: { ok: true, user_id }

- POST /api/groups/{group_id}/commands/unban
  - Body: { user_id: int, reason?: string }
  - Auth: manage_bans
  - Response: { ok: true, user_id }

- POST /api/groups/{group_id}/commands/kick
  - Body: { user_id: int, reason?: string }
  - Auth: manage_members

- POST /api/groups/{group_id}/commands/mute
  - Body: { user_id: int, duration_minutes?: int, reason?: string }
  - Auth: manage_members

- POST /api/groups/{group_id}/commands/unmute
  - Body: { user_id: int }
  - Auth: manage_members

- POST /api/groups/{group_id}/commands/warn
  - Body: { user_id: int, reason?: string }
  - Auth: manage_warns
  - Response: { warnings: n, action: 'warned'|'banned' }

- POST /api/groups/{group_id}/commands/purge
  - Body: { count: int }
  - Auth: manage_members
  - Response: { deleted: <n> }

- POST /api/groups/{group_id}/commands/pin
  - Body: { message_id: int, disable_notification?: bool }
  - Auth: manage_members
  - Response: { ok: true }

- POST /api/groups/{group_id}/commands/unpin
  - Body: { message_id?: int }
  - Auth: manage_members
  - Response: { ok: true }

Notes about pin/unpin: When invoked from the web, prefer supplying `message_id` in the request body (if you want to pin a specific message). If called without `message_id` the bot will attempt to pin the last pinned/known message if it can discover one. For deterministic behavior include `message_id` when calling from the UI.

---

## Admin / Superadmin (`/api/v1`)

All `/api/v1` endpoints require Authorization: Bearer <access_token>. Many are superadmin-only.

### POST /api/v1/auth/token
- Purpose: obtain access/refresh tokens (dev/test flows) — see `src/web/superadmin_api.py`.

### POST /api/v1/auth/refresh
- Purpose: refresh tokens

### GET /api/v1/my-groups
- Purpose: list groups visible to the current admin (superadmins see all)

### GET /api/v1/my-permissions/{group_id}
- Purpose: return the caller's permissions for the group (useful for UI toggles and feature gating)

### Admin Permissions API

1) GET /api/v1/groups/{group_id}/admins
- List admin members for the group and their assigned permissions. Auth: superadmin or group admin with `manage_admins`.

2) PUT /api/v1/groups/{group_id}/admins/{admin_id}/permissions
- Replace permission set (upsert). Body: JSON array of permission strings (values from GroupPermission). Auth: superadmin or group admin with `manage_admins`.

Response example for these endpoints: { status: "success", message: "Permissions updated successfully" }

### Other v1 admin endpoints
- GET /api/v1/groups/{group_id}/bans — admin-facing bans list
- GET /api/v1/groups/{group_id}/recent-logs — recent moderation logs (limit param)

---

## WebSocket — real-time logs

URL: ws://{host}/ws/logs/{group_id}?token=<token>

- Auth: JWT token provided as query param. The server decodes and verifies the token in the handshake.
- Behavior: subscribes to Redis channel `group_logs:{group_id}` and forwards JSON log payloads to connected clients.
- Message payload example:
```
{"id":"693c10a6...","admin_id":123,"user_id":456,"action":"ban","reason":"spam","timestamp":"2025-12-13T10:20:00Z","group_id":-1001234567890}
```

Close codes: The server may close the handshake with 4401 / 4403 reasons when auth fails.

Security note: Query-string tokens are acceptable for browsers but consider switching to a subprotocol or an Authorization header for stronger security.

---

## Bot commands (Aiogram handlers)

These are the Telegram-side admin commands implemented in `src/bot/handlers.py`. When a running bot instance receives a command it performs Telegram API calls and also invokes the shared server service to persist state and publish audit logs.

Implemented commands (admin-only):

- /ban <user_id|reply> — Ban user (calls `perform_mod_action` then attempts telegram.kick_chat_member).
- /unban <user_id|reply> — Unban user (server unbans + removes DB ban record).
- /kick <user_id|reply> — Kick user.
- /mute <minutes|reply> — Restrict user for duration.
- /unmute <user_id|reply> — Remove restrictions.
- /warn <user_id|reply> [reason] — Issue warning; service may auto-ban after threshold.
- /purge <count> — Delete recent messages (if bot has permission).
- /pin (reply) — Pin the replied message.
- /unpin — Unpin message (optionally by message_id when provided via UI).
- /promote <user_id|reply> — Promote a member to admin (tries multiple Telegram API methods for compatibility).
- /demote <user_id|reply> — Demote admin to regular member.

Handler behavior notes:
- The handlers try to perform the Telegram API calls only when a real Bot instance is available (this keeps tests lightweight). If Telegram API fails the handler returns a descriptive message but still persists/logs the action where applicable.
- All handlers call `perform_mod_action(...)` so actions are always persisted and published for other processes (web/dashboard) to see.

---

## Cross-process contract: web ↔ bot synchronization

Goal: actions performed from the web dashboard should be applied by the bot to the Telegram group (if a bot process is running) and actions performed by the bot should be visible in the web dashboard.

Mechanism implemented:

1) Shared service `perform_mod_action(group_id, admin_id, action_type, target_user, reason=None, duration_minutes=None)` (in `src/services/mod_actions.py`) performs DB updates (bans, member updates, warnings), writes an audit log (`log_admin_action`), and publishes a global Redis action event to channel `guardian:actions`.

2) `log_admin_action(...)` still publishes group-specific logs for the real-time websocket channel `group_logs:{group_id}`, but it now also publishes an action event to `guardian:actions` so any running bot process can pick it up to apply Telegram-side effects.

3) Bot process (see `src/bot/main.py`) starts a background Redis subscriber task on startup that subscribes to `guardian:actions`. Incoming events are JSON objects describing the action; the bot maps the action to an appropriate Telegram API call (ban/unban/kick/mute/unmute/promote/demote/pin/unpin) and attempts the call best-effort.

4) If the bot cannot apply the Telegram-side effect (e.g., API error, missing permissions) it logs the failure but does not roll back the server-side state. This design keeps the server state authoritative and allows retries / manual correction.

Action event JSON contract (published to `guardian:actions`):
```
{
  "action_id": "<uuid>",
  "group_id": -1001234567890,
  "action": "ban",           // one of: ban, unban, kick, mute, unmute, warn, pin, unpin, promote, demote
  "target_user_id": 98765,
  "admin_id": 12345,
  "reason": "spam",
  "duration_minutes": 60,     // optional, for mute
  "metadata": { "message_id": 5555 } // optional, for pin/unpin
}
```

Bot listener behavior:
- Subscribes to `guardian:actions` and attempts the Telegram-side effect.
- It tries multiple API method names (for example, `promote_chat_member` vs `promoteChatMember`) to be resilient across aiogram versions.
- Failures are logged and non-fatal.

Design trade-offs and guarantees:
- The server DB is authoritative: actions are persisted immediately by `perform_mod_action`.
- The bot applies Telegram-side effects best-effort after the server persisted the action (eventual consistency).
- To ensure deterministic pin/unpin behavior include `metadata.message_id` when calling from web.

---

## Examples

Authenticate (mock):
```
curl -X POST http://127.0.0.1:8001/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"id":12345,"first_name":"Alice","auth_date":1700000000,"hash":"..."}'
```

List bans for a group:
```
curl -H "Authorization: Bearer mock-jwt-token-12345" \
  http://127.0.0.1:8001/api/groups/-100123456789/bans
```

Unban a user:
```
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

Trigger a pin from the web (recommended with message_id):
```
curl -X POST -H "Authorization: Bearer mock-jwt-token-12345" \
 -H "Content-Type: application/json" \
 -d '{"message_id":5555, "disable_notification":true}' \
 http://127.0.0.1:8001/api/groups/-100123456789/commands/pin
```

If a bot process is running it will receive the `guardian:actions` event and attempt to pin `message_id` 5555 in the Telegram group.

---

## Webhook / Event simulation for local dev

If you want to test end-to-end in CI or dev without a real Redis server or Telegram bot, consider these options:

- Use a lightweight Redis test container (recommended for end-to-end CI) and run a short-lived bot process in the same pipeline.
- For unit tests, mock `src/services/redis_client.get_redis()` and `aiogram.Bot` methods; unit tests in this repo already use AsyncMock-heavy patterns.

---

## Recommended follow-ups

- Add small smoke tests (pytest) for: auth, list groups, ban/unban flow, recent-logs websocket handshake.
- Add an end-to-end test that spins up Redis in a test container and a fake bot process to validate web→redis→bot roundtrip.
- Harden the bot action listener with retries, exponential backoff, and a dead-letter log for events that consistently fail.
- Replace the mock Telegram auth with proper JWT issuance and include scopes/permissions in tokens for stronger security.
- Consider moving WebSocket auth to use Authorization header or a subprotocol for better security.

---

## Implementation notes (where to look in repo)

- `src/web/api.py` — main REST routes and group endpoints.
- `src/web/superadmin_api.py` — v1 admin endpoints and auth/token flows.
- `src/services/auth.py` — token encode/decode and helper guards.
- `src/services/mod_actions.py` — shared service performing DB updates and audit log + publish to Redis.
- `src/services/audit.py` — audit log writer and publisher (publishes to `group_logs:{group_id}` and `guardian:actions`).
- `src/services/redis_client.py` — Redis connect/publish helpers and `RedisPubSubManager`.
- `src/bot/handlers.py` — aiogram handlers and admin commands.
- `src/bot/main.py` — bot startup, Redis listener `_start_redis_action_listener`, lifecycle hooks.

---

If you want, I can:
- commit this file to the repo (done), update the project's README to link it, and create a small Postman collection or OpenAPI export,
- or create a minimal end-to-end pytest that spins up Redis and a fake bot to validate the web→redis→bot path. Tell me which you'd like next.

-- Generated from codebase audit and recent changes (2025-12-17)
