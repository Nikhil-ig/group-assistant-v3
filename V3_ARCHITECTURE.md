# V3 Complete Architecture Guide

Comprehensive overview of V3 structure, components, and how they work together.

## 📚 Table of Contents

1. [Directory Structure](#directory-structure)
2. [Core Concepts](#core-concepts)
3. [Component Overview](#component-overview)
4. [Data Flow](#data-flow)
5. [Adding Features](#adding-features)
6. [API Reference](#api-reference)
7. [Development Guide](#development-guide)

---

## Directory Structure

```
v3/
│
├── core/                      # Data models and type definitions
│   ├── __init__.py
│   └── models.py             # ActionPayload, ActionResult, enums
│
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py           # Config classes for dev/prod
│
├── services/                  # Business logic layer (6-step workflow)
│   ├── __init__.py
│   └── bidirectional.py      # BidirectionalService orchestrator
│
├── bot/                       # Telegram bot command handlers
│   ├── __init__.py
│   └── commands.py           # 8 commands + registration
│
├── api/                       # FastAPI REST endpoints
│   ├── __init__.py
│   └── endpoints.py          # 4 routes + models
│
├── frontend/                  # TypeScript/React
│   ├── bidirectionalService.ts   # TS service class
│   └── ModerationPanel.tsx       # React component
│
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── logging.py            # Logging setup
│   └── validators.py         # Input validation
│
├── main.py                    # Application initialization
├── .env.example              # Configuration template
├── V3_README.md              # Quick start guide
├── V3_SETUP_GUIDE.md         # Detailed setup
└── V3_ARCHITECTURE.md        # This file
```

---

## Core Concepts

### 1. ActionPayload (Unified Action Format)

**Purpose:** All actions from any source use the same data structure for consistency.

**Source:**  `core/models.py` → `ActionPayload` dataclass

**Structure:**
```python
@dataclass
class ActionPayload:
    action: ActionType              # What to do (BAN, MUTE, etc.)
    group_id: int                   # Telegram group ID
    user_id: int                    # User being moderated
    admin_id: int                   # Who is doing it
    reason: Optional[str]           # Why (optional)
    duration_hours: Optional[int]   # How long (for MUTE)
    source: ActionSource            # Where from (BOT, WEB, API)
    notification_mode: NotificationMode  # Who to notify
    timestamp: datetime
    metadata: Dict[str, Any]        # Extra data
```

**Example:**
```python
payload = ActionPayload(
    action=ActionType.BAN,
    group_id=-123456789,
    user_id=987654321,
    admin_id=111222333,
    reason="spam",
    source=ActionSource.WEB,
    notification_mode=NotificationMode.GROUP_AND_USER
)
```

### 2. ActionResult (Execution Result)

**Purpose:** Standard response format for all actions.

**Source:** `core/models.py` → `ActionResult` dataclass

**Structure:**
```python
@dataclass
class ActionResult:
    ok: bool                        # Success/failure
    source: ActionSource            # Where from
    timestamp: datetime
    action_id: Optional[str]        # Unique ID for tracking
    error: Optional[str]            # Error message if failed
    execution_time_ms: Optional[float]  # Performance metric
    metadata: Dict[str, Any]
```

**Example:**
```python
result = ActionResult(
    ok=True,
    source=ActionSource.WEB,
    timestamp=datetime.now(),
    action_id="act_abc123xyz",
    execution_time_ms=245.3
)
```

### 3. Enums

#### ActionType
```python
class ActionType(Enum):
    BAN = "BAN"          # Permanent ban
    UNBAN = "UNBAN"      # Remove ban
    MUTE = "MUTE"        # Restrict messages
    UNMUTE = "UNMUTE"    # Restore messages
    KICK = "KICK"        # Remove from group
    WARN = "WARN"        # Issue warning
```

#### ActionSource
```python
class ActionSource(Enum):
    BOT = "BOT"      # From /command in Telegram
    WEB = "WEB"      # From web dashboard
    API = "API"      # From API call
```

#### NotificationMode
```python
class NotificationMode(Enum):
    SILENT = "SILENT"                  # No notifications
    GROUP_ONLY = "GROUP_ONLY"         # Only send to group
    GROUP_AND_USER = "GROUP_AND_USER" # Both group and user DM
    USER_ONLY = "USER_ONLY"           # Only send to user
```

---

## Component Overview

### 1. Configuration Module (`config/`)

**Purpose:** Centralized settings management

**Files:**
- `settings.py` - Config classes
- `__init__.py` - Exports

**Key Classes:**

#### Config (Base)
All settings as class variables:
- Telegram settings (token, bot name)
- Database settings (MongoDB URI, database name)
- Cache settings (Redis URI)
- API settings (host, port, base URL)
- Authentication (JWT secret, algorithm)
- Logging (level, format, file path)
- Features (real-time sync, audit logging)
- Performance (timeouts, cache duration)

```python
from config.settings import get_config

# Automatic - uses ENVIRONMENT variable
config = get_config()

# Or specific
from config.settings import DevelopmentConfig
config = DevelopmentConfig()

# Validate all required settings
if not config.validate():
    raise RuntimeError("Invalid configuration")
```

**Usage:**
```python
# Access settings
config = get_config()
token = config.TELEGRAM_BOT_TOKEN
uri = config.MONGODB_URI
timeout = config.ACTION_TIMEOUT_SECONDS
```

### 2. Core Module (`core/`)

**Purpose:** Data models used throughout application

**Files:**
- `models.py` - All dataclasses and enums
- `__init__.py` - Exports

**Key Classes:**
- `ActionPayload` - Action data
- `ActionResult` - Execution result
- `ActionType` - Action enum
- `ActionSource` - Source enum
- `NotificationMode` - Notification enum

**Usage:**
```python
from core.models import ActionPayload, ActionType, ActionSource, NotificationMode

payload = ActionPayload(
    action=ActionType.BAN,
    group_id=-123456789,
    user_id=987654321,
    admin_id=111222333
)
```

### 3. Services Module (`services/`)

**Purpose:** Core business logic and orchestration

**Files:**
- `bidirectional.py` - Main service
- `__init__.py` - Exports

**Key Class: BidirectionalService**

The orchestrator that executes all actions through a 6-step workflow:

```python
class BidirectionalService:
    def __init__(self, bot, db, redis):
        self.bot = bot
        self.db = db
        self.redis = redis
        self.metrics = {...}
    
    async def execute_action(self, payload: ActionPayload) -> ActionResult:
        # Step 1: Validate input
        # Step 2: Execute on Telegram API
        # Step 3: Store in MongoDB
        # Step 4: Send notifications
        # Step 5: Broadcast via Redis
        # Step 6: Update metrics
        return result
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `execute_action()` | Main entry point - runs 6-step flow |
| `_validate()` | Check inputs are valid |
| `_execute_telegram_action()` | Call Telegram Bot API |
| `_store_in_database()` | Save to MongoDB audit log |
| `_send_notifications()` | Route notifications |
| `_broadcast_action()` | Publish to Redis |
| `_update_metrics()` | Track counts and rates |
| `get_metrics()` | Retrieve metrics |

**Usage:**
```python
from services.bidirectional import BidirectionalService
from core.models import ActionPayload, ActionType

service = BidirectionalService(bot, db, redis)

payload = ActionPayload(
    action=ActionType.BAN,
    group_id=-123456789,
    user_id=987654321,
    admin_id=111222333,
    reason="spam"
)

result = await service.execute_action(payload)
if result.ok:
    print(f"✅ Action completed in {result.execution_time_ms}ms")
else:
    print(f"❌ Error: {result.error}")
```

### 4. Bot Module (`bot/`)

**Purpose:** Telegram bot command handlers

**Files:**
- `commands.py` - All command handlers
- `__init__.py` - Exports

**Key Class: Commands**

Wraps all 8 bot commands with unified pattern:

```python
class Commands:
    def __init__(self, service: BidirectionalService):
        self.service = service
    
    async def ban(self, update, context):
        # Check admin → Parse args → Create payload → Execute → Reply
    
    async def unban(self, update, context):
        # Same pattern...
    
    # ... 6 more commands
    
    async def _check_admin(self, update, context):
        # Helper to verify user is admin
```

**All 8 Commands:**

| Command | Example | Description |
|---------|---------|-------------|
| `/ban` | `/ban 123456789 spam` | Ban permanently |
| `/unban` | `/unban 123456789` | Remove ban |
| `/mute` | `/mute 123456789 24 spam` | Restrict 24 hours |
| `/unmute` | `/unmute 123456789` | Restore messages |
| `/kick` | `/kick 123456789 spam` | Remove from group |
| `/warn` | `/warn 123456789 spam` | Issue warning |
| `/logs` | `/logs 20` | Show last 20 actions |
| `/stats` | `/stats` | Show statistics |

**Helper Function:**

```python
def register_commands(application, service):
    """Register all commands with bot"""
    commands = Commands(service)
    application.add_handler(CommandHandler("ban", commands.ban))
    # ... register others
```

**Usage:**
```python
from bot.commands import register_commands

register_commands(application, service)
# Now all 8 commands work in Telegram
```

### 5. API Module (`api/`)

**Purpose:** REST endpoints using FastAPI

**Files:**
- `endpoints.py` - All routes and models
- `__init__.py` - Exports

**Key Components:**

#### Request Models (Pydantic)
```python
class ModActionRequest(BaseModel):
    user_id: int
    reason: Optional[str] = None
    duration_hours: Optional[int] = None
    notify_group: bool = True
    notify_user: bool = False
    show_in_bot: bool = True
```

#### Response Models
```python
class ActionResultResponse(BaseModel):
    ok: bool
    source: str
    timestamp: str
    action_id: Optional[str]
    error: Optional[str]
    execution_time_ms: Optional[float]

class AuditLogsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    entries: List[AuditLogEntry]

class MetricsResponse(BaseModel):
    total_actions: int
    bot_actions: int
    web_actions: int
    action_breakdown: Dict[str, int]
    success_rate_percent: float
```

#### Routes (4 total)

| Route | Method | Purpose |
|-------|--------|---------|
| `/groups/{group_id}/actions/{action_type}` | POST | Execute action |
| `/groups/{group_id}/logs` | GET | Get audit logs |
| `/groups/{group_id}/metrics` | GET | Get metrics |
| `/groups/{group_id}/health` | GET | Health check |

**Usage:**
```python
from api.endpoints import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1")

# Run: uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 6. Frontend Module (`frontend/`)

**Purpose:** TypeScript/React integration

**Files:**
- `bidirectionalService.ts` - TS service class
- `ModerationPanel.tsx` - React component

#### bidirectionalService.ts

**Key Class: BidirectionalModerationServiceV3**

```typescript
class BidirectionalModerationServiceV3 {
    // Configuration
    private token: string = ''
    
    // Authentication
    setToken(token: string): void
    
    // Action methods
    async ban(groupId, userId, reason?, notifications?): Promise<ActionResult>
    async unban(groupId, userId, notifications?): Promise<ActionResult>
    async mute(groupId, userId, duration?, reason?, notifications?): Promise<ActionResult>
    async unmute(groupId, userId, notifications?): Promise<ActionResult>
    async kick(groupId, userId, reason?, notifications?): Promise<ActionResult>
    async warn(groupId, userId, reason?, notifications?): Promise<ActionResult>
    
    // Data fetch methods
    async getAuditLogs(groupId, limit?, offset?): Promise<AuditLogs>
    async getMetrics(groupId): Promise<Metrics>
    async healthCheck(groupId): Promise<boolean>
    
    // Helper method
    private async executeAction(...): Promise<ActionResult>
}

// Usage
const service = new BidirectionalModerationServiceV3()
service.setToken('jwt_token_here')

const result = await service.ban(123, 456, 'spam', {
    notifyGroup: true,
    notifyUser: false
})
```

#### ModerationPanel.tsx

**Key Component: ModerationPanel**

React component with:
- Action selection dropdown
- User ID input
- Reason textarea
- Duration input (for mute)
- 3 notification checkboxes
- Confirmation dialog
- Success/error alerts
- Execution time display

```typescript
export const ModerationPanel: React.FC<ModerationPanelProps> = ({
    groupId,
    onSuccess?
}) => {
    // State management
    // Form handlers
    // Action execution
    // Confirmation dialog
    // Results display
}

// Usage
<ModerationPanel
    groupId={123}
    onSuccess={(result) => console.log('Done', result)}
/>
```

### 7. Utils Module (`utils/`)

**Purpose:** Reusable utilities

**Files:**
- `logging.py` - Logging setup
- `validators.py` - Input validation
- `__init__.py` - Exports

#### logging.py

**Key Functions:**

```python
# Setup logger
logger = setup_logger(__name__, level="INFO", log_file="logs/bot.log")

# Action logger
action_logger = get_action_logger(__name__)
action_logger.action_executed('BAN', 123, 456, 789, 'spam')
action_logger.action_failed('BAN', 123, 456, 'error message')

# Performance logger
perf_logger = get_performance_logger(__name__)
perf_logger.action_timing('BAN', 245.5)
perf_logger.database_timing('insert', 120.3)
```

#### validators.py

**Key Functions:**

```python
# Individual validation
validate_user_id(123456789)          # ✅ OK
validate_group_id(-123456789)        # ✅ OK
validate_duration(24)                # ✅ OK
validate_reason("spam")              # ✅ OK
validate_action_type("BAN")          # ✅ OK

# Payload validation
valid, error = InputValidator.validate_action_payload(
    'BAN', -123, 456, 'spam'
)

# Quick checks
if is_valid_user_id(user_id):
    # Proceed
```

---

## Data Flow

### Flow 1: Telegram Command → Action

```
User types /ban 123456789 spam
    ↓
bot/commands.py → ban()
    ↓
  1. Check admin permissions
  2. Parse arguments (user_id, reason)
  3. Create ActionPayload with ActionSource.BOT
  4. Call service.execute_action(payload)
    ↓
services/bidirectional.py → execute_action()
    ↓
  1. Validate input
  2. Call Telegram Bot API (ban_chat_member)
  3. Store in MongoDB audit log
  4. Send group notification
  5. Send user DM (if enabled)
  6. Broadcast to Redis (for real-time)
  7. Update metrics
    ↓
  Return ActionResult with status
    ↓
bot/commands.py → reply to user in Telegram
    ↓
User sees ✅ Ban executed, Time: 245ms
```

### Flow 2: Web Dashboard → Action

```
User clicks "Ban" in dashboard
    ↓
frontend/ModerationPanel.tsx → handleExecute()
    ↓
  1. Validate inputs
  2. Show confirmation dialog
  3. Call bidirectionalService.ban()
    ↓
frontend/bidirectionalService.ts → ban()
    ↓
  Convert parameters to NotificationOptions
  Make POST request to /groups/{id}/actions/BAN
    ↓
api/endpoints.py → execute_action()
    ↓
  1. Validate request
  2. Create ActionPayload with ActionSource.WEB
  3. Call service.execute_action(payload)
    ↓
services/bidirectional.py → execute_action()
    ↓
  [Same 6-step flow as above]
    ↓
api/endpoints.py → return ActionResultResponse
    ↓
frontend/bidirectionalService.ts → return result
    ↓
frontend/ModerationPanel.tsx → display result
    ↓
User sees ✅ Success, Time: 245ms
```

### Flow 3: Direct API Call → Action

```
API client: POST /groups/123/actions/BAN
    ↓
api/endpoints.py → execute_action()
    ↓
  [Same as Web Dashboard flow]
```

---

## Adding Features

### Adding a New Action Type

**Step 1:** Update enum in `core/models.py`
```python
class ActionType(Enum):
    BAN = "BAN"
    TIMEOUT = "TIMEOUT"  # ← New
```

**Step 2:** Add handler in `services/bidirectional.py`
```python
elif payload.action == ActionType.TIMEOUT:
    await self.bot.restrict_chat_member(...)
```

**Step 3:** Add command in `bot/commands.py`
```python
async def timeout(self, update, context):
    # Check admin → Parse → Execute → Reply
```

**Step 4:** Register command
```python
def register_commands(application, service):
    # ... existing ...
    application.add_handler(CommandHandler("timeout", commands.timeout))
```

**Step 5:** Add API endpoint (optional)
```python
@router.post("/{group_id}/actions/TIMEOUT")
async def timeout_action(...):
    # Already works via action_type parameter
```

### Adding Custom Logging

**Step 1:** Use logger in your module
```python
from utils.logging import setup_logger, get_action_logger

logger = setup_logger(__name__)
action_logger = get_action_logger(__name__)
```

**Step 2:** Log events
```python
action_logger.action_executed('BAN', group_id, user_id, admin_id, reason)
action_logger.action_failed('BAN', group_id, user_id, "API error")
```

### Adding Custom Validation

**Step 1:** Add validator in `utils/validators.py`
```python
def validate_custom_field(value):
    if not is_valid(value):
        raise ValidationError(f"Invalid: {value}")
    return True
```

**Step 2:** Use validator
```python
from utils.validators import validate_custom_field

validate_custom_field(value)  # Raises if invalid
```

### Adding Notification Handler

**Step 1:** Override in `services/bidirectional.py`
```python
async def _send_group_notification(self, payload, action_id):
    # Default behavior with custom message
    message = f"Custom notification for {payload.action}"
    await self.bot.send_message(payload.group_id, message)
```

---

## API Reference

### POST /groups/{group_id}/actions/{action_type}

Execute an action.

**Parameters:**
- `group_id` (path) - Telegram group ID
- `action_type` (path) - BAN, UNBAN, MUTE, UNMUTE, KICK, or WARN
- `user_id` (body) - User ID to moderate
- `reason` (body, optional) - Reason for action
- `duration_hours` (body, optional) - Duration for MUTE

**Response:**
```json
{
  "ok": true,
  "source": "WEB",
  "timestamp": "2024-01-15T10:30:00Z",
  "action_id": "act_abc123",
  "execution_time_ms": 245.3
}
```

### GET /groups/{group_id}/logs

Get audit logs.

**Parameters:**
- `group_id` (path) - Telegram group ID
- `limit` (query, optional) - Max 200, default 50
- `offset` (query, optional) - Pagination offset, default 0

**Response:**
```json
{
  "total": 250,
  "limit": 50,
  "offset": 0,
  "entries": [
    {
      "action_id": "act_abc123",
      "action": "BAN",
      "user_id": 123,
      "admin_id": 456,
      "reason": "spam",
      "timestamp": "2024-01-15T10:30:00Z",
      "source": "WEB"
    }
  ]
}
```

### GET /groups/{group_id}/metrics

Get metrics.

**Parameters:**
- `group_id` (path) - Telegram group ID

**Response:**
```json
{
  "total_actions": 1250,
  "bot_actions": 800,
  "web_actions": 450,
  "action_breakdown": {
    "BAN": 300,
    "MUTE": 450,
    "WARN": 500
  },
  "success_rate_percent": 99.2
}
```

### GET /groups/{group_id}/health

Health check.

**Parameters:**
- `group_id` (path) - Telegram group ID

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## Development Guide

### Setting Up Development Environment

```bash
# Install dependencies
pip install python-telegram-bot fastapi uvicorn motor redis python-dotenv pydantic

# Create development .env
cp .env.example .env

# Set development mode
echo "ENVIRONMENT=development" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Run bot
python -m main

# In another terminal, run API
uvicorn api.endpoints:router --reload
```

### Testing Components Individually

**Test Config:**
```python
from config.settings import get_config
config = get_config()
print(config.TELEGRAM_BOT_TOKEN)  # Should be set
```

**Test Models:**
```python
from core.models import ActionPayload, ActionType
payload = ActionPayload(
    action=ActionType.BAN,
    group_id=-123,
    user_id=456,
    admin_id=789
)
print(payload.to_dict())
```

**Test Validators:**
```python
from utils.validators import validate_user_id, ValidationError
try:
    validate_user_id(-1)
except ValidationError as e:
    print(f"Caught: {e}")
```

**Test Service:**
```python
from services.bidirectional import BidirectionalService
service = BidirectionalService()
# Mock bot, db, redis as needed
```

### Code Style

- Follow PEP 8
- Use type hints on all functions
- Add docstrings to all classes/methods
- Keep functions under 50 lines (prefer composition)
- Use descriptive variable names
- Comment complex logic

### Common Patterns

**Pattern 1: Check Admin**
```python
if not await self._check_admin(update, context):
    await update.message.reply_text("❌ Admin only")
    return
```

**Pattern 2: Parse Arguments**
```python
if not context.args or len(context.args) < 1:
    await update.message.reply_text("❌ Usage: /ban <user_id>")
    return
user_id = int(context.args[0])
```

**Pattern 3: Create Payload**
```python
payload = ActionPayload(
    action=ActionType.BAN,
    group_id=update.effective_chat.id,
    user_id=user_id,
    admin_id=update.effective_user.id,
    reason=" ".join(context.args[1:]) if len(context.args) > 1 else None,
    source=ActionSource.BOT
)
```

**Pattern 4: Execute and Reply**
```python
result = await self.service.execute_action(payload)
if result.ok:
    await update.message.reply_text(f"✅ Ban executed\nTime: {result.execution_time_ms:.1f}ms")
else:
    await update.message.reply_text(f"❌ Error: {result.error}")
```

---

**Version**: 3.0.0  
**Last Updated**: 2024
