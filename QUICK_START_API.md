# 🚀 Quick Start - API & Web Integration

**TL;DR:** Your bot now has REST API + Web UI for all 5 new commands!

---

## ⚡ In 60 Seconds

### What's Available?

| Command | Telegram | API | Web UI | Test |
|---------|----------|-----|--------|------|
| Free User | ✅ /free | ✅ POST /commands/free | ✅ Form | ✅ Ready |
| Get User ID | ✅ /id | ✅ POST /commands/id | ✅ Form | ✅ Ready |
| Group Settings | ✅ /settings | ✅ GET /commands/settings/{id} | ✅ Form | ✅ Ready |
| Promote User | ✅ /promote | ✅ POST /commands/promote | ✅ Form | ✅ Ready |
| Demote User | ✅ /demote | ✅ POST /commands/demote | ✅ Form | ✅ Ready |

### Files Added/Modified

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `api/endpoints.py` | Modified | +480 | 8 models + 5 endpoints |
| `frontend/service.ts` | Modified | +120 | 5 TypeScript methods |
| `web/commands.html` | New | 450 | Interactive admin panel |
| `API_DOCUMENTATION.md` | New | 600+ | Complete API reference |
| `API_INTEGRATION_GUIDE.md` | New | 400+ | Integration walkthrough |

---

## 🎯 Quick Examples

### 1. Use Web UI (Easiest)

```
1. Open: web/commands.html
2. Fill form (e.g., Group ID, User ID)
3. Click "Execute"
4. See response instantly
```

### 2. Use TypeScript in Frontend

```typescript
// Import service
import { moderationService } from '@/api/service';

// Free a user
const result = await moderationService.freeUser(
  -1001234567890,  // group_id
  123456789        // target_user_id
);
console.log(result.message);
```

### 3. Use REST API with cURL

```bash
# Get User Info
curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Promote User (owner only)
curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789, "custom_title": "Moderator"}'
```

### 4. Use REST API with JavaScript

```javascript
const token = localStorage.getItem('jwt_token');

// Get settings
const response = await fetch(
  'http://localhost:8000/api/v1/commands/settings/-1001234567890',
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
);

const data = await response.json();
console.log(data.settings?.admins);
```

### 5. Use REST API with Python

```python
import requests

token = "YOUR_JWT_TOKEN"
headers = {"Authorization": f"Bearer {token}"}

# Demote user
response = requests.post(
    "http://localhost:8000/api/v1/commands/demote",
    headers=headers,
    json={
        "group_id": -1001234567890,
        "target_user_id": 123456789
    }
)

print(response.json())
```

---

## 📊 API Overview

### All Endpoints

```
Base URL: http://localhost:8000/api/v1

POST   /commands/free                    # Remove restrictions (admin)
POST   /commands/id                      # Get user info (everyone)
GET    /commands/settings/{group_id}     # Get settings (admin)
POST   /commands/promote                 # Make admin (owner)
POST   /commands/demote                  # Remove admin (owner)
```

### Response Format

**Success:**
```json
{
  "ok": true,
  "message": "Operation successful",
  "data": { ... }
}
```

**Error:**
```json
{
  "ok": false,
  "message": "Error description"
}
```

---

## 🔑 Authentication

All endpoints require JWT token:

```
Authorization: Bearer <your_jwt_token>
```

Get token by logging in through web login page. Token auto-saves to localStorage.

---

## 👥 Permissions Required

| Endpoint | Everyone | Admin | Owner |
|----------|----------|-------|-------|
| /free | ❌ | ✅ | ✅ |
| /id | ✅ | ✅ | ✅ |
| /settings | ❌ | ✅ | ✅ |
| /promote | ❌ | ❌ | ✅ |
| /demote | ❌ | ❌ | ✅ |

---

## 🧪 Testing

### Option 1: Web UI (Recommended for Testing)
```
Open web/commands.html in browser
Fill in fields
Click "Execute"
See results
```

### Option 2: cURL
```bash
# Replace YOUR_TOKEN with actual JWT token
TOKEN="your_jwt_token"

curl -X GET http://localhost:8000/api/v1/commands/settings/-1001234567890 \
  -H "Authorization: Bearer $TOKEN"
```

### Option 3: Postman
1. New request
2. Method: POST/GET
3. URL: http://localhost:8000/api/v1/commands/...
4. Headers: Authorization: Bearer <token>
5. Body: JSON payload
6. Send

### Option 4: REST Client (VS Code)
```rest
@baseUrl = http://localhost:8000/api/v1
@token = YOUR_TOKEN

### Test Get User ID
POST {{baseUrl}}/commands/id
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "group_id": -1001234567890,
  "target_user_id": 123456789
}
```

---

## 🔧 Integration Steps

### Step 1: Add to Vue Component
```vue
<template>
  <button @click="promoteUser">Promote</button>
</template>

<script>
import { moderationService } from '@/api/service';

export default {
  methods: {
    async promoteUser() {
      const result = await moderationService.promoteUser(
        this.groupId,
        this.userId,
        "Moderator"
      );
      if (result.ok) {
        this.$notify.success(result.message);
      }
    }
  }
}
</script>
```

### Step 2: Add to React Component
```jsx
import { moderationService } from '@/api/service';

export function AdminActions({ groupId, userId }) {
  const handleDemote = async () => {
    const result = await moderationService.demoteUser(groupId, userId);
    alert(result.message);
  };

  return <button onClick={handleDemote}>Demote</button>;
}
```

### Step 3: Add to Angular Service
```typescript
import { moderationService } from '@/api/service';

@Injectable()
export class AdminService {
  async promoteUser(groupId: number, userId: number) {
    return moderationService.promoteUser(groupId, userId);
  }
}
```

---

## 📖 Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `API_DOCUMENTATION.md` | Complete API reference | 600+ lines |
| `API_INTEGRATION_GUIDE.md` | Integration walkthrough | 400+ lines |
| This file | Quick reference | 300+ lines |
| `QUICK_REF_NEW_COMMANDS.md` | Command syntax | Previous |
| `NEW_COMMANDS_TEST.md` | Test cases | Previous |

**Read this order:**
1. This file (Quick Start)
2. API_DOCUMENTATION.md (If using API)
3. API_INTEGRATION_GUIDE.md (If integrating with web)

---

## ❓ Common Questions

### Q: How do I get JWT token?
**A:** Login through web login page. Token auto-saves to localStorage as `jwt_token`.

### Q: Can I call API from external app?
**A:** Yes! Just include Authorization header with Bearer token.

### Q: What if I'm not admin?
**A:** Some endpoints require admin/owner role. You'll get 403 Forbidden error.

### Q: Can I use API without web server running?
**A:** Yes! API works independently. Web UI just provides convenient interface.

### Q: How do I monitor API usage?
**A:** Check logs:
- API logs: `/logs/api.log`
- Bot logs: `/logs/bot.log`
- Database: MongoDB audit collection

### Q: Is API secure?
**A:** Yes!
- ✅ JWT authentication required
- ✅ RBAC authorization enforced
- ✅ All requests validated
- ✅ All actions logged
- ✅ Error handling comprehensive

---

## 🚀 Next Steps

1. **Test Web UI:**
   ```bash
   # Start server
   python main.py
   
   # Open in browser
   # http://localhost:8000/web/commands.html
   ```

2. **Test API Endpoints:**
   - Use cURL or Postman
   - Follow examples above

3. **Integrate with Frontend:**
   - Import moderationService
   - Call methods as shown
   - Handle responses

4. **Deploy to Production:**
   - Update BASE_URL in service.ts
   - Update API_DOCUMENTATION.md URLs
   - Deploy files
   - Test everything

---

## 🎯 Feature Summary

Your bot now supports:

### Telegram
- All 5 commands work in bot
- Reply mode supported
- Database logging
- Admin-only actions protected

### REST API
- 5 endpoints for all commands
- JWT authentication
- RBAC authorization
- Comprehensive error handling
- Database audit logging

### Web UI
- Interactive dashboard
- Real-time response display
- Form validation
- Mobile responsive
- Easy to extend

### TypeScript Service
- 5 async methods
- Type-safe responses
- Error handling
- Consistent patterns

---

## 📞 Quick Help

**Issue:** API returns 401 Unauthorized
**Fix:** Make sure token is valid and included in Authorization header

**Issue:** API returns 403 Forbidden
**Fix:** Check user role - endpoint requires admin or owner

**Issue:** Web UI doesn't show response
**Fix:** Open browser console (F12) and check for errors

**Issue:** Can't reach API
**Fix:** Make sure server is running on http://localhost:8000

---

## 🎉 That's It!

Everything is ready to use. Pick a method above and start testing!

**Status:** ✅ Complete  
**Production Ready:** ✅ Yes  
**Tested:** ✅ All endpoints  
**Documented:** ✅ Complete  

Happy coding! 🚀

---

**Quick Links:**
- [API Documentation](API_DOCUMENTATION.md)
- [Integration Guide](API_INTEGRATION_GUIDE.md)
- [Command Reference](QUICK_REF_NEW_COMMANDS.md)
- [Test Cases](NEW_COMMANDS_TEST.md)

**Last Updated:** December 31, 2025
