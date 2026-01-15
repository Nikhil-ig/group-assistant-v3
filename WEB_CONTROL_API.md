# Web Control API Documentation

Complete REST API for controlling the Telegram bot via web interface. All bot actions can be executed and monitored through HTTP endpoints.

---

## 🚀 Quick Start

### Base URL
```
http://localhost:8000/api/web
```

### Example: Ban a user via web

```bash
curl -X POST http://localhost:8000/api/web/actions/ban \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "user_input": "123456789",
    "reason": "Spam behavior",
    "initiated_by": 987654321
  }'
```

---

## 📋 Core Concepts

### User Reference
Users can be referenced by:
- **Numeric ID**: `"123456789"` (as string)
- **Username**: `"@john_doe"` or `"john_doe"`

The API automatically parses both formats.

### Response Format
All endpoints return consistent JSON responses:

**Success Response:**
```json
{
  "success": true,
  "action_id": "507f1f77bcf86cd799439011",
  "user_id": 123456789,
  "username": "@john_doe",
  "message": "User has been banned"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid user reference",
  "details": "User reference could not be parsed"
}
```

---

## 🔧 Utility Endpoints

### Parse User Reference

**Endpoint:** `POST /parse-user`

Validate and normalize user input before using in other endpoints.

**Request:**
```json
{
  "user_input": "123456789"
}
```

**Response:**
```json
{
  "user_id": 123456789,
  "username": null,
  "input": "123456789",
  "type": "numeric",
  "is_valid": true
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_input | string | ✅ | User ID or @username |

---

## 🎯 Action Endpoints

### Ban User

**Endpoint:** `POST /actions/ban`

Permanently ban a user from a group.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "reason": "Spam",
  "initiated_by": 987654321
}
```

**Response:**
```json
{
  "success": true,
  "action_id": "507f...",
  "user_id": 123456789,
  "username": null,
  "message": "User has been banned"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID (negative) |
| user_input | string | ✅ | User ID or @username |
| reason | string | ❌ | Reason for ban |
| initiated_by | integer | ✅ | Admin user ID performing action |

---

### Kick User

**Endpoint:** `POST /actions/kick`

Kick a user from a group (can rejoin).

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "@john_doe",
  "reason": "Violating rules",
  "initiated_by": 987654321
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |
| user_input | string | ✅ | User ID or @username |
| reason | string | ❌ | Reason for kick |
| initiated_by | integer | ✅ | Admin user ID |

---

### Mute User

**Endpoint:** `POST /actions/mute`

Silence a user (prevent sending messages).

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "duration_minutes": 60,
  "reason": "Flooding",
  "initiated_by": 987654321
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |
| user_input | string | ✅ | User ID or @username |
| duration_minutes | integer | ❌ | Duration in minutes (0 = forever) |
| reason | string | ❌ | Reason for mute |
| initiated_by | integer | ✅ | Admin user ID |

---

### Unmute User

**Endpoint:** `POST /actions/unmute`

Restore user's ability to send messages.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "initiated_by": 987654321
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |
| user_input | string | ✅ | User ID or @username |
| initiated_by | integer | ✅ | Admin user ID |

---

### Restrict Permissions

**Endpoint:** `POST /actions/restrict`

Limit specific permissions for a user.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "permission_type": "send_messages",
  "initiated_by": 987654321
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |
| user_input | string | ✅ | User ID or @username |
| permission_type | string | ❌ | Permission to restrict (default: send_messages) |
| initiated_by | integer | ✅ | Admin user ID |

**Permission Types:**
- `send_messages` - Block sending text/media
- `send_media` - Block media uploads
- `send_stickers` - Block stickers
- `send_animations` - Block animations
- `send_polls` - Block polls
- `add_web_page_previews` - Block link previews

---

### Unrestrict Permissions

**Endpoint:** `POST /actions/unrestrict`

Restore all user permissions.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "initiated_by": 987654321
}
```

---

### Warn User

**Endpoint:** `POST /actions/warn`

Issue a warning to a user.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "reason": "Disrespectful behavior",
  "initiated_by": 987654321
}
```

---

### Promote to Admin

**Endpoint:** `POST /actions/promote`

Promote a user to admin status.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "title": "Moderator",
  "initiated_by": 987654321
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |
| user_input | string | ✅ | User ID or @username |
| title | string | ❌ | Admin title (default: Admin) |
| initiated_by | integer | ✅ | Admin user ID |

---

### Demote from Admin

**Endpoint:** `POST /actions/demote`

Remove admin status from a user.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "initiated_by": 987654321
}
```

---

### Unban User

**Endpoint:** `POST /actions/unban`

Remove a ban from a previously banned user.

**Request:**
```json
{
  "group_id": -1001234567890,
  "user_input": "123456789",
  "initiated_by": 987654321
}
```

---

## 📦 Batch Operations

### Execute Multiple Actions

**Endpoint:** `POST /actions/batch`

Execute up to 100 actions in a single request.

**Request:**
```json
{
  "actions": [
    {
      "action_type": "ban",
      "group_id": -1001234567890,
      "user_input": "111111",
      "reason": "Spam",
      "initiated_by": 987654321
    },
    {
      "action_type": "mute",
      "group_id": -1001234567890,
      "user_input": "222222",
      "duration_minutes": 60,
      "initiated_by": 987654321
    },
    {
      "action_type": "warn",
      "group_id": -1001234567890,
      "user_input": "@john_doe",
      "reason": "Off-topic",
      "initiated_by": 987654321
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "success": true,
      "action_id": "507f...",
      "action_type": "ban"
    },
    {
      "index": 1,
      "success": true,
      "action_id": "507f...",
      "action_type": "mute"
    },
    {
      "index": 2,
      "success": true,
      "action_id": "507f...",
      "action_type": "warn"
    }
  ]
}
```

**Limits:**
- Maximum 100 actions per batch
- Partial success is possible (some fail, others succeed)

---

## 📊 Query & Monitoring Endpoints

### Get User Action History

**Endpoint:** `GET /actions/user-history`

Retrieve all actions performed on a specific user.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| group_id | integer | required | Telegram group ID |
| user_input | string | required | User ID or @username |
| limit | integer | 50 | Max results (1-200) |

**Example:**
```bash
curl http://localhost:8000/api/web/actions/user-history?group_id=-1001234567890&user_input=123456789&limit=50
```

**Response:**
```json
{
  "success": true,
  "group_id": -1001234567890,
  "user_id": 123456789,
  "username": null,
  "total_actions": 5,
  "actions": [
    {
      "action_id": "507f...",
      "action_type": "ban",
      "initiated_by": 987654321,
      "reason": "Spam",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "action_id": "507f...",
      "action_type": "warn",
      "initiated_by": 987654321,
      "reason": "Flooding",
      "created_at": "2024-01-14T15:20:00Z"
    }
  ]
}
```

---

### Get Group Statistics

**Endpoint:** `GET /actions/group-stats`

Get overview statistics for a group.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| group_id | integer | ✅ | Telegram group ID |

**Example:**
```bash
curl http://localhost:8000/api/web/actions/group-stats?group_id=-1001234567890
```

**Response:**
```json
{
  "success": true,
  "group_id": -1001234567890,
  "total_actions": 127,
  "actions_by_type": {
    "ban": 12,
    "mute": 45,
    "warn": 60,
    "kick": 10
  },
  "recent_actions": [
    {
      "action_id": "507f...",
      "action_type": "ban",
      "user_id": 123456789,
      "initiated_by": 987654321,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "most_active_admin": {
    "user_id": 987654321,
    "username": "@moderator_jane",
    "actions_count": 45
  }
}
```

---

### Get Action Status

**Endpoint:** `GET /actions/status/{action_id}`

Get detailed information about a specific action.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| action_id | string | MongoDB action ID |

**Example:**
```bash
curl http://localhost:8000/api/web/actions/status/507f1f77bcf86cd799439011
```

**Response:**
```json
{
  "success": true,
  "action_id": "507f1f77bcf86cd799439011",
  "action_type": "ban",
  "group_id": -1001234567890,
  "user_id": 123456789,
  "username": null,
  "initiated_by": 987654321,
  "created_at": "2024-01-15T10:30:00Z",
  "status": "success",
  "result": {
    "telegram_response": "ok",
    "execution_time_ms": 245
  }
}
```

---

### List Managed Groups

**Endpoint:** `GET /groups/list`

Get all groups managed by the bot.

**Example:**
```bash
curl http://localhost:8000/api/web/groups/list
```

**Response:**
```json
{
  "success": true,
  "total_groups": 3,
  "groups": [
    {
      "group_id": -1001234567890,
      "group_name": "My Awesome Group",
      "members_count": 1250,
      "total_actions": 127,
      "last_action": "2024-01-15T10:30:00Z"
    },
    {
      "group_id": -1001234567891,
      "group_name": "Developer Community",
      "members_count": 3450,
      "total_actions": 89,
      "last_action": "2024-01-15T09:15:00Z"
    }
  ]
}
```

---

## ℹ️ System Endpoints

### Health Check

**Endpoint:** `GET /health`

Check if web control API is operational.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "3.0.0",
  "endpoints_available": 20,
  "message": "Web control API is operational"
}
```

---

### API Info

**Endpoint:** `GET /info`

Get comprehensive documentation of all available endpoints.

**Response:**
```json
{
  "api_version": "1.0.0",
  "name": "Web Control API",
  "description": "Complete REST API for controlling bot via web interface",
  "base_path": "/api/web",
  "endpoints": {
    "parse-user": {
      "method": "POST",
      "description": "Parse user reference",
      "path": "/parse-user"
    },
    "actions": {
      "ban": {"method": "POST", "path": "/actions/ban"},
      "kick": {"method": "POST", "path": "/actions/kick"},
      ...
    }
  }
}
```

---

## 💡 Usage Examples

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/web"

def ban_user(group_id, user_id, admin_id, reason="Spam"):
    """Ban a user from a group"""
    response = requests.post(
        f"{BASE_URL}/actions/ban",
        json={
            "group_id": group_id,
            "user_input": str(user_id),
            "reason": reason,
            "initiated_by": admin_id
        }
    )
    return response.json()

def batch_actions(actions_list):
    """Execute multiple actions"""
    response = requests.post(
        f"{BASE_URL}/actions/batch",
        json={"actions": actions_list}
    )
    return response.json()

# Usage
result = ban_user(
    group_id=-1001234567890,
    user_id=123456789,
    admin_id=987654321,
    reason="Spam behavior"
)
print(result)
```

### JavaScript Example

```javascript
const BASE_URL = "http://localhost:8000/api/web";

async function banUser(groupId, userId, adminId, reason = "Spam") {
  const response = await fetch(`${BASE_URL}/actions/ban`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      group_id: groupId,
      user_input: String(userId),
      reason: reason,
      initiated_by: adminId,
    }),
  });
  return response.json();
}

// Usage
const result = await banUser(-1001234567890, 123456789, 987654321);
console.log(result);
```

### JavaScript/Node.js Batch Example

```javascript
async function batchActions(actions) {
  const response = await fetch(`${BASE_URL}/actions/batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ actions }),
  });
  return response.json();
}

// Ban 3 users at once
const actions = [
  {
    action_type: "ban",
    group_id: -1001234567890,
    user_input: "111111",
    reason: "Spam",
    initiated_by: 987654321,
  },
  {
    action_type: "ban",
    group_id: -1001234567890,
    user_input: "222222",
    reason: "Toxic behavior",
    initiated_by: 987654321,
  },
  {
    action_type: "mute",
    group_id: -1001234567890,
    user_input: "@username",
    duration_minutes: 60,
    initiated_by: 987654321,
  },
];

const result = await batchActions(actions);
console.log(`Successful: ${result.successful}/${result.total}`);
```

---

## 🔐 Security Considerations

1. **Always include `initiated_by`**: Every action must specify who is performing it
2. **Verify admin status**: API doesn't check permissions - web interface should validate
3. **Rate limiting**: Consider implementing rate limiting in production
4. **Authentication**: Add API key authentication in production
5. **Audit logging**: All actions are logged in MongoDB with timestamps

---

## 📈 Performance Notes

- **Single action**: ~200-400ms (network + MongoDB)
- **Batch actions**: ~50-100ms per action average
- **Query endpoints**: ~100-300ms depending on data size
- **Caching**: Results are not cached (always fresh from DB)

---

## 🐛 Error Handling

### Common Errors

**400 Bad Request:**
```json
{
  "detail": "Invalid user reference"
}
```

**404 Not Found:**
```json
{
  "detail": "Action not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Database connection failed"
}
```

### Error Responses

All error responses include:
- **status_code**: HTTP status code
- **detail**: Human-readable error message
- **timestamp**: When error occurred

---

## 🚀 Integration Checklist

- [ ] Web Control API running on `http://localhost:8000/api/web`
- [ ] MongoDB connected and initialized
- [ ] Parse function working (`/parse-user` endpoint)
- [ ] Ban action working (`/actions/ban`)
- [ ] Batch actions working (`/actions/batch`)
- [ ] Query endpoints working (`/actions/user-history`)
- [ ] Health check passing (`/health`)
- [ ] API documentation accessible (`/info`)

---

## 📝 Version History

**v1.0.0** (2024-01-15):
- Initial release
- All core action endpoints
- Batch operations support
- Query and monitoring endpoints
- User reference parsing
- Health checks

---

## 🤝 Support

For issues or questions:
1. Check health endpoint: `GET /health`
2. Review API logs: `docker logs centralized_api`
3. Verify MongoDB connection
4. Test with `/parse-user` endpoint first

