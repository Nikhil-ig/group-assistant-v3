# 🔌 REST API Documentation - New Commands

**Status:** ✅ Complete  
**Date:** December 31, 2025  
**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer Token (JWT)

---

## 🎯 New Command Endpoints

All endpoints require JWT authentication. Include token in `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 1. 🆓 POST /commands/free - Remove Restrictions

**Purpose:** Remove all restrictions from a user (opposite of `/restrict`)

**Request:**
```json
{
  "group_id": -1001234567890,
  "target_user_id": 123456789,
  "target_username": "username"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "message": "✅ User freed from restrictions",
  "action_id": "free_-1001234567890_123456789"
}
```

**Response (Error):**
```json
{
  "ok": false,
  "message": "Not authorized - admin required"
}
```

**Permissions Required:**
- Admin or Owner
- Group ID must match user's group

**Examples:**

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "john_doe"
  }'
```

### JavaScript/TypeScript
```typescript
const response = await moderationService.freeUser(
  -1001234567890,    // group_id
  123456789,         // target_user_id
  "john_doe"         // target_username
);
```

### Python (requests)
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/commands/free",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "group_id": -1001234567890,
        "target_user_id": 123456789,
        "target_username": "john_doe"
    }
)
```

---

## 2. 🆔 POST /commands/id - Get User ID & Info

**Purpose:** Get user ID and information

**Request:**
```json
{
  "group_id": -1001234567890,
  "target_user_id": 123456789
}
```

**Response (Success):**
```json
{
  "ok": true,
  "user": {
    "user_id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "john_doe",
    "is_bot": false,
    "group_id": -1001234567890,
    "group_name": "My Group"
  },
  "message": "User info retrieved successfully"
}
```

**Response (Error):**
```json
{
  "ok": false,
  "message": "User not found"
}
```

**Permissions Required:**
- None (Everyone can use)

**Examples:**

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789
  }'
```

### JavaScript/TypeScript
```typescript
const response = await moderationService.getUserID(
  -1001234567890,    // group_id
  123456789          // target_user_id (optional)
);
```

### Python (requests)
```python
response = requests.post(
    "http://localhost:8000/api/v1/commands/id",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "group_id": -1001234567890,
        "target_user_id": 123456789
    }
)
```

---

## 3. ⚙️ GET /commands/settings/{group_id} - Get Group Settings

**Purpose:** Get group settings and admin list

**Request:**
```
GET /commands/settings/-1001234567890
Authorization: Bearer <token>
```

**Response (Success):**
```json
{
  "ok": true,
  "settings": {
    "group_id": -1001234567890,
    "group_name": "My Awesome Group",
    "group_type": "supergroup",
    "member_count": 156,
    "admins": [
      {
        "user_id": 111111,
        "username": "bot_owner",
        "first_name": "Bot",
        "last_name": "Owner",
        "custom_title": "Owner"
      },
      {
        "user_id": 222222,
        "username": "john",
        "first_name": "John",
        "last_name": "Admin",
        "custom_title": "Moderator"
      }
    ],
    "description": "Group for testing"
  },
  "message": "Group settings retrieved successfully"
}
```

**Response (Error):**
```json
{
  "ok": false,
  "message": "Not authorized - admin required"
}
```

**Permissions Required:**
- Admin or Owner

**Examples:**

### cURL
```bash
curl -X GET http://localhost:8000/api/v1/commands/settings/-1001234567890 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### JavaScript/TypeScript
```typescript
const response = await moderationService.getGroupSettings(
  -1001234567890    // group_id
);
```

### Python (requests)
```python
response = requests.get(
    "http://localhost:8000/api/v1/commands/settings/-1001234567890",
    headers={"Authorization": f"Bearer {token}"}
)
```

---

## 4. 👑 POST /commands/promote - Make User Admin

**Purpose:** Promote user to admin with optional custom title

**Request:**
```json
{
  "group_id": -1001234567890,
  "target_user_id": 123456789,
  "target_username": "john_doe",
  "custom_title": "Moderator"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "message": "✅ User promoted to admin with title: Moderator",
  "action_id": "promote_-1001234567890_123456789",
  "title_set": true
}
```

**Response (Error - Not Owner):**
```json
{
  "ok": false,
  "message": "Not authorized - owner required"
}
```

**Permissions Required:**
- Owner ONLY (not regular admin)

**Parameters:**
- `custom_title` (optional): Max 16 characters
  - Examples: "Moderator", "Senior Mod", "Helper"

**Examples:**

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "john_doe",
    "custom_title": "Moderator"
  }'
```

### JavaScript/TypeScript
```typescript
const response = await moderationService.promoteUser(
  -1001234567890,    // group_id
  123456789,         // target_user_id
  "Moderator",       // custom_title
  "john_doe"         // target_username
);
```

### Python (requests)
```python
response = requests.post(
    "http://localhost:8000/api/v1/commands/promote",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "group_id": -1001234567890,
        "target_user_id": 123456789,
        "target_username": "john_doe",
        "custom_title": "Moderator"
    }
)
```

---

## 5. 👤 POST /commands/demote - Remove Admin

**Purpose:** Demote admin back to regular user

**Request:**
```json
{
  "group_id": -1001234567890,
  "target_user_id": 123456789,
  "target_username": "john_doe"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "message": "✅ User demoted to regular member",
  "action_id": "demote_-1001234567890_123456789"
}
```

**Response (Error - Not Owner):**
```json
{
  "ok": false,
  "message": "Not authorized - owner required"
}
```

**Permissions Required:**
- Owner ONLY (not regular admin)

**Examples:**

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/commands/demote \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "john_doe"
  }'
```

### JavaScript/TypeScript
```typescript
const response = await moderationService.demoteUser(
  -1001234567890,    // group_id
  123456789,         // target_user_id
  "john_doe"         // target_username
);
```

### Python (requests)
```python
response = requests.post(
    "http://localhost:8000/api/v1/commands/demote",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "group_id": -1001234567890,
        "target_user_id": 123456789,
        "target_username": "john_doe"
    }
)
```

---

## 📊 Error Codes & Meanings

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized (no token) | Add `Authorization: Bearer <token>` header |
| 403 | Forbidden (not enough permissions) | Check user role (admin/owner required) |
| 404 | Not found | Check group_id or user_id |
| 500 | Server error | Check server logs |

---

## 🔐 Permission Levels

| Endpoint | Everyone | Admin | Owner |
|----------|----------|-------|-------|
| `/commands/free` | ❌ | ✅ | ✅ |
| `/commands/id` | ✅ | ✅ | ✅ |
| `/commands/settings/{group_id}` | ❌ | ✅ | ✅ |
| `/commands/promote` | ❌ | ❌ | ✅ |
| `/commands/demote` | ❌ | ❌ | ✅ |

---

## 💡 Common Use Cases

### 1. Get Admin List for Group
```typescript
const settings = await moderationService.getGroupSettings(groupId);
const admins = settings.settings?.admins || [];
```

### 2. Promote Multiple Users at Once
```typescript
const users = [123456, 234567, 345678];
for (const userId of users) {
  await moderationService.promoteUser(groupId, userId, "Moderator");
}
```

### 3. Get User Info Before Action
```typescript
const userInfo = await moderationService.getUserID(groupId, userId);
if (userInfo.ok) {
  console.log(`User: ${userInfo.user?.username}`);
}
```

### 4. Free User After Restriction Expires
```typescript
await moderationService.freeUser(groupId, userId);
```

### 5. Build Admin Panel
```typescript
const settings = await moderationService.getGroupSettings(groupId);
// Display in UI:
// - Group name
// - Member count
// - Admin list
```

---

## 🧪 Testing Endpoints

### Using REST Client (VS Code)

Create a `.rest` file:
```rest
@baseUrl = http://localhost:8000/api/v1
@token = YOUR_JWT_TOKEN

### Get User ID
POST {{baseUrl}}/commands/id
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "group_id": -1001234567890,
  "target_user_id": 123456789
}

### Get Group Settings
GET {{baseUrl}}/commands/settings/-1001234567890
Authorization: Bearer {{token}}

### Promote User
POST {{baseUrl}}/commands/promote
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "group_id": -1001234567890,
  "target_user_id": 123456789,
  "custom_title": "Moderator"
}
```

### Using Postman

1. Create new collection
2. Add requests with:
   - Method: POST/GET
   - URL: `http://localhost:8000/api/v1/commands/<endpoint>`
   - Headers: `Authorization: Bearer <token>`
   - Body: JSON payload

---

## 📝 Response Formats

All responses follow this format:

### Success
```json
{
  "ok": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### Error
```json
{
  "ok": false,
  "message": "Error description"
}
```

---

## 🔄 Integration with Frontend

### Vue.js Example
```vue
<template>
  <button @click="promoteUser">Promote User</button>
</template>

<script>
import { moderationService } from './frontend/service';

export default {
  methods: {
    async promoteUser() {
      const result = await moderationService.promoteUser(
        this.groupId,
        this.userId,
        "Moderator"
      );
      if (result.ok) {
        alert("User promoted!");
      }
    }
  }
}
</script>
```

### React Example
```jsx
import { moderationService } from './frontend/service';

export function PromoteUserButton({ groupId, userId }) {
  const [loading, setLoading] = useState(false);

  const handlePromote = async () => {
    setLoading(true);
    const result = await moderationService.promoteUser(groupId, userId);
    if (result.ok) {
      alert("User promoted!");
    }
    setLoading(false);
  };

  return <button onClick={handlePromote}>Promote User</button>;
}
```

---

## 📞 Support

- **Issues?** Check error message and permission level
- **Need docs?** See QUICK_REF_NEW_COMMANDS.md
- **Having problems?** Check bot logs at `/logs/bot.log`

---

**Status:** ✅ API Complete & Ready  
**Last Updated:** December 31, 2025  
**Version:** 1.0
