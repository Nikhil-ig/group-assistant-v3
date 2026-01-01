# AI Agent Guide — Commands, APIs, Roles, and Implementation

This guide is written for automated coding agents and human contributors who will be adding features, debugging, or operating the Guardian Bot project. It describes every command, API, permission, role, model, handler mapping, and practical instructions for implementing, testing, and deploying changes.

NOTE: refer to `src/handlers/admin.py`, `src/web/api.py`, `src/web/superadmin_api.py`, and `src/services/database.py` as the canonical code locations for the features described here.

---

## Purpose and scope

This document's objective is to:

- Provide an exhaustive reference of bot commands and their short aliases, the handler files that implement them, expected inputs/outputs and permission checks.
- Document REST and WebSocket APIs (paths, required permissions, payload examples) as implemented in the repo.
- Define the role and permission model used by the platform and how to evaluate and modify permission mappings programmatically.
- Give a step-by-step recipe for adding new commands, APIs, or dashboard features that an AI agent can follow reliably.
- Provide test templates, edge-case checklists, and deployment verification steps.

Who should use this doc:
- AI coding agents implementing new handlers or refactors.
- Developers adding or updating API endpoints.
- SRE / DevOps verifying deployments and integrations.

---

## Quick repo pointers (canonical files)

- Bot handlers: `src/handlers/*.py` (primary: `src/handlers/admin.py`)  
- Web API: `src/web/api.py`  
- Superadmin API & auth: `src/web/superadmin_api.py`  
- Web static/dashboard: `src/web/static/` and `dashboard/`  
- DB/service layer: `src/services/database.py`  
- Auth helper for API: `src/services/auth.py`  
- Models (Pydantic/DB schemas): `src/models/*.py`  
- Utilities & filters: `src/utils/*`  

---

## Permission model (contract)

Contract (inputs/outputs):
- Input: (user_id, group_id, token) — goal: resolve permission level or assert a required permission.
- Output: Admin permission level (OWNER, SENIOR_ADMIN, MODERATOR, HELPER, VIEWER) or allow/deny.

Key functions to call:
- `get_user_permission_level(user_id: int, group_id: int, bot: Optional[Bot] = None)` — returns `AdminPermissionLevel`.
- `verify_group_permission(group_id: int, permission: GroupPermission, current_user: Dict)` — used by web API handlers.

Important mapping constants (from `src/handlers/admin.py` and `src/models/permissions.py`):
- `PERMISSION_MAPPING` — lists capabilities per AdminPermissionLevel.
- `LEVEL_RANK` — numeric ranking to compare levels.

Edge cases for permission checks:
- Missing mappings: if a stored DB permission uses a different string, normalize (lowercase) prior to compare.
- Telegram authoritative source vs DB: handlers often consult Telegram (via bot) then persist/upsert to DB.
- Superadmin bypass: superadmins set `is_superadmin` in `admin_users` and bypass group checks.

---

## Commands — Full catalog, handler mapping and examples

All bot commands are implemented as Aiogram handlers in `src/handlers/*` (primarily `admin.py` and `admin old.py`). Commands have short aliases defined in the `SHORT_COMMANDS` mapping.

Short alias mapping (from `admin.py`):
```
SHORT_COMMANDS = {
    "b": "ban",
    "k": "kick",
    "m": "mute",
    "w": "warn",
    "ub": "unban",
    "um": "unmute",
    "uw": "unwarn",
    "bl": "blacklist",
    "ubl": "unblacklist",
    "wl": "warnlist",
    "bls": "banlist",
    "st": "settings",
    "i": "info",
    "l": "logs",
    "r": "rules",
    "sc": "scan",
    "p": "purge",
    "ld": "lockdown",
    "sm": "slowmode",
    "as": "antispam",
    "rc": "restrict",
    "urc": "unrestrict",
    "rl": "restrictlist",
    "nm": "nightmode",
    "ra": "refresh_admins",
    "sa": "save_admins",
    "wlcm": "welcome",
    "rls": "rules",
    "lc": "logchannel",
    "unmute": "unmute",
    "unwarn": "unwarn"
}
```

Command table (concise):
- `/ban` (`/b`) — ban a user. Handler: `src/handlers/admin.py` (`cmd_ban` or similar). Permission: `manage_bans`.
- `/unban` (`/ub`) — unban a user. Handler: API & bot handler. Permission: `manage_bans`.
- `/mute` (`/m`) — mute user (duration optional). Permission: `manage_bans`.
- `/unmute` (`/um`) — unmute user. Permission: `manage_bans`.
- `/warn` (`/w`) — warn user. Permission: `manage_warns`.
- `/unwarn` (`/uw`) — remove warnings or specific warn. Permission: `manage_warns`.
- `/blacklist` (`/bl`) — add media to blacklist (reply to media). Permission: `manage_blacklist`.
- `/unblacklist` (`/ubl`) — remove item from blacklist. Permission: `manage_blacklist`.
- `/rules` (`/rls`) — list rules. Permission: `manage_rules` or view.
- `/settings` (`/st`) — open inline configuration UI. Permission: `manage_settings`.
- `/scan` (`/sc`) — run a content scan. Permission: `manage_members`.
- `/purge` (`/p`) — delete N messages. Permission: `manage_members`.
- `/lockdown` (`/ld`) — restrict posting for non-admins. Permission: `manage_settings`.
- `/antispam` (`/as`) — configure anti-spam thresholds. Permission: `manage_auto_mod`.
- `/welcome` (`/wlcm`) — set welcome message. Permission: `manage_welcome`.
- `/help` — contextual help (permission-aware). Handler: `cmd_help` in `admin.py`.

Implementation notes for command handlers:
- Always check permissions at the start of the handler — use `IsAdminFilter()` (Aiogram filter) or call `get_user_permission_level()`.
- Prefer reply-style targeting (i.e., `msg.reply_to_message.from_user.id`) to determine target user. If args are provided, resolve with `get_target_from_reply()` helper.
- Log every moderation action via `log_action()` or `add_log()` in `src/services/database.py`.
- If a command modifies group config (e.g., `/settings`, `/antispam`), call `update_group_config()` and notify dashboard via Redis pub/sub (helper: `notify_dashboard_of_action()`).

Example: basic `/ban` handler pseudo-flow
1. Resolve target user from reply or args.
2. Check permission `manage_bans`.
3. Call Telegram API to ban: `await bot.ban_chat_member(chat_id, target_id)`.
4. Persist ban in DB: `await add_ban(group_id, BanSchema(...))`.
5. Log action: `await add_log(group_id, LogSchema(...))`.
6. Notify dashboard: `await notify_dashboard_of_action(group_id, {...})`.

---

## APIs — endpoints, permissions, and payloads

This repository exposes two types of APIs: group-scoped APIs (`/api/groups/{group_id}/...`) and superadmin APIs (`/api/v1/...`). The FastAPI app is in `src/web/api.py`. Superadmin endpoints are in `src/web/superadmin_api.py`.

Authentication
- Superadmin endpoints require a JWT (OAuth2 password flow) — see `POST /api/v1/auth/token`.
- Group dashboard login can use the Telegram auth endpoint `POST /auth/telegram` which returns a mock token in development.

Important API groups

1. Group-scoped APIs: `/api/groups/{group_id}`
   - GET `/api/groups/{group_id}` — retrieve group config (permission: view_group)
   - GET `/api/groups/{group_id}/members` — paginated members (permission: manage_members)
   - GET `/api/groups/{group_id}/bans` — list bans (permission: manage_bans)
   - POST `/api/groups/{group_id}/commands/ban` — ban via API (permission: manage_bans)
   - POST `/api/groups/{group_id}/commands/unban` — unban via API (permission: manage_bans)
   - GET/PUT `/api/groups/{group_id}/automod` — get/set anti-spam config (permission: manage_auto_mod)
   - GET/POST `/api/groups/{group_id}/blacklist` — list/add blacklist items (permission: manage_blacklist)
   - GET `/api/groups/{group_id}/rules` — list rules (permission: manage_rules)
   - POST `/api/groups/{group_id}/chat/reply` — send message via bot.

2. Superadmin APIs (prefix `/api/v1`):
   - POST `/api/v1/auth/token` — obtain access/refresh tokens
   - POST `/api/v1/auth/refresh` — refresh tokens
   - GET `/api/v1/superadmin/stats` — platform stats (superadmin only)
   - GET/POST/PUT/DELETE `/api/v1/superadmin/admins` — manage admin accounts (superadmin only)
   - GET `/api/v1/groups/{group_id}/bans` — admin-facing bans listing
   - GET `/api/v1/my-groups` — list groups available to current admin
   - GET `/api/v1/my-permissions/{group_id}` — returns caller's permissions for group

3. WebSocket
   - `/ws/logs/{group_id}` — subscribe to real-time moderation logs. Token passed as query param for websocket handshake. Use `get_user_from_token_str()` (in `src/services/auth.py`) to decode token in websocket handlers.

Payload examples
- Ban request (POST): { "user_id": 98765, "reason": "Spam" }
- Automod update (PUT): { "threshold": 10, "window_sec": 5, "enabled": true }

Error responses
- 401 Unauthorized — invalid or missing token
- 403 Forbidden — insufficient permissions
- 400 Bad Request — validation errors
- 404 Not Found — resource not present
- 500 Internal Server Error — unexpected errors

---

## Data models (summary & mapping to DB)

Primary Pydantic models are in `src/models/*`:
- `GroupConfig`, `AntiSpamConfig`, `RuleSchema` (group.py)
- `MemberSchema`, `BanSchema`, `WarningSchema`, `ChatMessageSchema`, `BlacklistedItemSchema`, `LogSchema` (group.py)
- `PermissionSet` and `GroupPermission` (permissions.py)

DB storage: `src/services/database.py` contains helpers to read/update these models. Functions of interest:
- `get_group_config`, `update_group_config`, `create_group_if_missing`
- `get_members`, `get_bans`, `add_ban`, `remove_ban`
- `add_warning`, `remove_warnings`, `get_warnings`
- `add_to_blacklist`, `delete_blacklist_item`, `get_blacklist`
- `add_log`, `get_logs`

When modifying models
- Update Pydantic models in `src/models/*` and ensure corresponding DB accessors (serializers/deserializers) are updated.
- Add migration steps if you alter persistent SQL schema (project may use SQLAlchemy create_all in dev). For production, prefer Alembic migrations.

---

## How an AI agent should implement a new command (step-by-step)

Assumptions: AI agent has write access to repo and can run tests locally.

Task example: Add `/warn_and_maybe_ban` — warns user and auto-bans when warnings in last hour >= 3.

1. Design contract
   - Input: Message reply or args (target user), optional reason
   - Precondition: Sender must have `manage_warns` permission
   - Behavior: add warning, check recent warning count, if >= 3 and within configured interval -> ban user
   - Output: reply in chat with action summary; log to DB

2. Create handler
   - File: `src/handlers/admin.py` (near existing warn handlers)
   - Decorator: `@router.message(Command("warn_and_maybe_ban"), IsAdminFilter())` and apply `@rate_limit(limit=5, period=60)` as appropriate
   - Use helpers: `get_target_from_reply()`, `get_user_permission_level()`

3. Implement logic (pseudo):
```py
@router.message(Command("warn_and_maybe_ban"), IsAdminFilter())
@rate_limit(limit=5, period=60)
async def cmd_warn_and_maybe_ban(msg: Message, command: CommandObject):
    target_id, target_msg = await get_target_from_reply(msg, command)
    if not target_id: return await reply_and_cleanup(msg, "No target")
    perm = await get_user_permission_level(msg.from_user.id, msg.chat.id, msg.bot)
    if "manage_warns" not in PERMISSION_MAPPING[perm]:
        return await reply_and_cleanup(msg, "Insufficient permission")
    await add_warning(msg.chat.id, WarningSchema(user_id=target_id, admin_id=msg.from_user.id, reason=reason))
    recent = await get_warning_count(target_id, msg.chat.id, interval_seconds=3600)
    if recent >= 3:
        await add_ban(msg.chat.id, BanSchema(...))
        await msg.reply("User auto-banned due to warnings")
    else:
        await msg.reply("Warning added")
    await add_log(...)
```

4. Persist changes and update docs
   - Add command entry in `COMPLETE_PROJECT_DOCUMENTATION.md` and `docs/AI_AGENT_GUIDE_COMMANDS_APIS.md` (this file)

5. Tests
   - Unit test for handler logic: mock `get_warning_count` and `add_ban` to assert behavior.
   - Integration test (optional): use an Aiogram test harness or simulate DB layer using in-memory mocks.

6. Lint & run quick checks
   - Run `flake8`/`ruff` (if present) and unit tests.

7. Deploy
   - Merge to `dev` branch, run CI, then promote to `main` when green.

---

## Testing guidance (unit and integration)

Unit tests (pytest) patterns:
- Mock external dependencies (`bot`, `database` functions) using `pytest-mock` or builtin fixtures.
- Focus on pure logic: permission checks, DB call outcomes, branching logic.
- Example test structure for `/warn_and_maybe_ban`:
  - test_warn_adds_warning_and_no_ban_when_less_than_threshold
  - test_warn_triggers_auto_ban_when_threshold_reached
  - test_permission_denied_for_unauthorized_user

Integration tests:
- Start a test DB & Redis (docker compose test profile) or use in-memory test doubles.
- Use `mcp_pylance_mcp_s_pylanceRunCodeSnippet` for small scripts, or run tests via the terminal:
  - `pytest tests/test_admin.py::test_warn_flow -q`

Mocking Telegram API:
- For handler unit tests, stub `msg.bot` calls like `bot.ban_chat_member` and `bot.send_message`.
- For integration tests, use a sandbox Telegram bot token and an isolated test group (not recommended in CI).

Smoke test checklist (post-change):
- Lint passes
- Unit tests for changed modules pass
- Start `uvicorn src.web.api:app --reload` and confirm `/docs` loads
- Start bot and confirm it registers new command (check logs)

---

## Edge cases & pitfalls (must-check list)

1. Concurrency: multiple admins acting simultaneously — ensure DB operations are idempotent and updates use upserts where needed.
2. Partial failures: Telegram API call succeeds but DB write fails (or vice versa). Use compensating actions or alert logs.
3. Permission drift: stored DB permissions may not match Telegram status — handlers typically reconcile (upsert) when Telegram indicates admin status.
4. Negative group IDs: always use the group ID sent by Telegram; group IDs are negative ints for channels/groups.
5. Rate limits: Telegram API rate-limits actions (e.g., banning many users) — throttle or batch where possible.
6. Parsing command args: be defensive about missing args and non-numeric durations.
7. Time zones: datetime fields are stored in UTC — present in UI in user's timezone if required.
8. Blacklist items: `file_unique_id` is the canonical key — don't rely solely on `file_id` which can change.

---

## Security & best practices for AI agents

- Always validate inputs and sanitize strings before composing messages.
- Never embed secrets in code — use `.env` and `src/config/settings.py` to read configuration.
- When creating or modifying admin users, validate permission keys against the whitelist in `superadmin_api`.
- WebSocket auth: avoid passing tokens in query strings in production; prefer cookies or Authorization headers.
- Use HTTPS in production and rotate `API_SECRET_KEY` regularly.

---

## Deployment & CI checklist

Pre-deploy:
- Run linters (ruff/flake8), type checks (mypy, if enabled), unit tests.
- Ensure database migrations are prepared (Alembic) if schema changed.
- Verify Docker Compose services are healthy (Postgres, Redis).

On deploy:
- Migrate DB (if needed) — `alembic upgrade head` or run migration script.
- Restart services (uvicorn/gunicorn + bot process) and tail logs for errors.

Post-deploy verification:
- `/health` returns 200 and valid JSON.
- `/docs` loads and OpenAPI has new endpoints documented.
- Dashboard login works and shows updated group data.
- WebSocket connections can be established and stream logs.

Rollbacks:
- Keep a downtime window for DB migrations.
- If a change causes repeated failures, revert to previous release and investigate.

---

## Documentation & Handoff notes for AI agents

When an AI agent finishes implementing a change, it should:
1. Update this guide if any command/API behavior changed.
2. Add or update API docs under `docs/` (OpenAPI is generated from FastAPI docs).
3. Add unit tests and update `tests/` accordingly.
4. Provide a short summary PR description describing the changes, affected handlers, and recommended manual verification steps.

PR template checklist (for the agent to populate):
- [ ] Implemented feature or fix
- [ ] Added/updated unit tests
- [ ] Updated documentation (`docs/AI_AGENT_GUIDE_COMMANDS_APIS.md` and `COMPLETE_PROJECT_DOCUMENTATION.md`)
- [ ] Verified locally: bot + web API start, `/health` OK
- [ ] Notified stakeholders (if any)

---

## Quick reference: useful helper functions (where to call)

- `get_target_from_reply(msg, command)` — resolve a user id from reply/args; used by most moderation commands.
- `get_user_permission_level(user_id, group_id, bot)` — compute permission level.
- `reply_and_cleanup(...)` — replies and auto-deletes messages if configured.
- `safe_delete_message(...)`, `safe_edit_message(...)`, `safe_bot_edit_message(...)` — utility wrappers that handle Telegram errors gracefully.
- `notify_dashboard_of_action(group_id, action_data)` — publish to Redis and inform dashboard.
- DB service APIs: `add_ban`, `remove_ban`, `add_warning`, `get_warning_count`, `add_to_blacklist`, `get_blacklist`, `get_logs`, `add_log`.

---

## Example snippets (copyable)

1) Minimal Aiogram command handler skeleton
```py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.handlers.admin import rate_limit, IsAdminFilter

router = Router()

@router.message(Command("hello"), IsAdminFilter())
@rate_limit(limit=5, period=60)
async def cmd_hello(msg: Message):
    await msg.reply("Hello — this command is protected by IsAdminFilter and rate-limited")
```

2) Example curl: ban via API
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 98765, "reason": "Spam"}' \
  http://localhost:8001/api/groups/-100123456789/commands/ban
```

3) WebSocket example (JS)
```js
const ws = new WebSocket(`ws://localhost:8001/ws/logs/-100123456789?token=${token}`);
ws.onmessage = (e) => console.log('log', JSON.parse(e.data));
```

---

## Next steps for the AI agent (recommended immediate tasks)

1. Implement any missing handlers identified during scanning (e.g., stray tokens in files) and add unit tests.  
2. Add API tests that exercise `POST /api/groups/{group_id}/commands/ban` and `GET /api/groups/{group_id}/logs`.  
3. Convert any mock tokens to proper JWT test tokens in `tests/` fixtures.  
4. Add a PR that updates docs and test coverage.

---

## Contact & references

- Project high-level docs: `COMPLETE_PROJECT_DOCUMENTATION.md` (root).  
- API Reference: `docs/API_REFERENCE_FULL.md`  
- Superadmin docs: `docs/SUPERADMIN_API.md`  
- Bot entrypoint: `src/bot/main.py`  

---

This file was generated to provide a deep, actionable guide so that automated agents can implement features safely and consistently. If you want, I can now:
- Add unit test templates for the top 10 commands.  

- Convert the guide into a smaller quick-reference cheat-sheet.

### Commands API & CLI (runtime management)

A lightweight runtime commands API and CLI were added to allow operators to create/list/update/delete bot commands without deploying code. Key points:

- CLI: `scripts/manage_commands.py` (uses `BOT_WEB_API_BASE_URL` and `BOT_SERVICE_TOKEN`). When `BOT_SERVICE_TOKEN` is present the CLI sends `Authorization: Bearer <token>` headers for authenticated requests. The CLI supports `list`, `create`, `update`, and `delete` subcommands.

- Header authentication (preferred): the web API accepts `Authorization: Bearer <token>` for service-to-service calls. For backward compatibility the API also accepts a legacy `?token=<token>` query parameter — prefer header usage in automation.

- Auto-refresh via Redis: when the commands API creates/updates/deletes a command it publishes a JSON message on the `guardian:commands` Redis channel. Bot processes subscribe to this channel and will call their internal `set_bot_commands(bot)` helper to refresh the Telegram-visible command list automatically. This keeps multiple bot processes in sync without restarts.

Message example published by the API:
```json
{"type": "commands_updated", "action": "create|update|delete", "name": "<command_name>"}
```

This section documents the minimal operator workflow and the runtime notification contract.
