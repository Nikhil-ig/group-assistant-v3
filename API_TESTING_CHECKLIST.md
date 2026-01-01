# 🧪 API Testing Checklist & Procedures

**Version:** 1.0  
**Date:** December 31, 2025  
**Status:** Ready for Testing

---

## ✅ Pre-Testing Setup

### 1. Start Server
```bash
# Navigate to project directory
cd /path/to/v3

# Install dependencies (if needed)
pip install -r requirements.txt

# Start the server
python main.py

# Verify server is running
curl http://localhost:8000/docs
# Should show Swagger UI
```

### 2. Get JWT Token
```bash
# Option 1: Via login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Save token from response
TOKEN="your_jwt_token_here"

# Verify token works
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Prepare Test Data
- Note your group ID (negative number, e.g., -1001234567890)
- Note a test user ID (e.g., 123456789)
- Note optional username (e.g., test_user)

---

## 🧪 Test Cases

### Test 1: POST /commands/id - Get User Info

**Endpoint:** `POST /api/v1/commands/id`  
**Permission:** Everyone  
**Purpose:** Get user information

#### Test 1.1: Valid Request
```bash
TOKEN="your_token"
CURL_CMD='curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '\''{
    "group_id": -1001234567890,
    "target_user_id": 123456789
  }'\'''

eval $CURL_CMD
```

**Expected Response:**
```json
{
  "ok": true,
  "user": {
    "user_id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "is_bot": false,
    "group_id": -1001234567890,
    "group_name": "Test Group"
  },
  "message": "User info retrieved successfully"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is true
- [ ] `user` object contains all fields
- [ ] `message` is present

#### Test 1.2: Missing Token
```bash
curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789
  }'
```

**Expected Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Acceptance Criteria:**
- [ ] Status code 401
- [ ] Error message returned

#### Test 1.3: Invalid Token
```bash
curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid token"
}
```

**Acceptance Criteria:**
- [ ] Status code 401
- [ ] Error message returned

#### Test 1.4: User Not Found
```bash
curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 999999999
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "User not found"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is false
- [ ] Error message returned

---

### Test 2: GET /commands/settings/{group_id} - Get Group Settings

**Endpoint:** `GET /api/v1/commands/settings/{group_id}`  
**Permission:** Admin  
**Purpose:** Get group settings and admin list

#### Test 2.1: Valid Request (Admin User)
```bash
TOKEN="your_admin_token"

curl -X GET http://localhost:8000/api/v1/commands/settings/-1001234567890 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "ok": true,
  "settings": {
    "group_id": -1001234567890,
    "group_name": "Test Group",
    "group_type": "supergroup",
    "member_count": 150,
    "admins": [
      {
        "user_id": 111111,
        "username": "admin1",
        "first_name": "Admin",
        "last_name": "One",
        "custom_title": "Moderator"
      },
      {
        "user_id": 222222,
        "username": "admin2",
        "first_name": "Admin",
        "last_name": "Two",
        "custom_title": "Helper"
      }
    ],
    "description": "Test group description"
  },
  "message": "Group settings retrieved successfully"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is true
- [ ] `settings` contains all fields
- [ ] `admins` array populated
- [ ] All admin info present

#### Test 2.2: Non-Admin User
```bash
TOKEN="regular_user_token"

curl -X GET http://localhost:8000/api/v1/commands/settings/-1001234567890 \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "detail": "Not authorized - admin required"
}
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Authorization error returned

#### Test 2.3: Invalid Group ID
```bash
curl -X GET http://localhost:8000/api/v1/commands/settings/invalid_id \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "detail": "Invalid group ID"
}
```

**Acceptance Criteria:**
- [ ] Status code 400 or 422
- [ ] Validation error returned

---

### Test 3: POST /commands/free - Free User

**Endpoint:** `POST /api/v1/commands/free`  
**Permission:** Admin  
**Purpose:** Remove restrictions from user

#### Test 3.1: Valid Request (Admin User)
```bash
TOKEN="your_admin_token"

curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe"
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "✅ User freed from restrictions",
  "action_id": "free_-1001234567890_123456789"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is true
- [ ] `message` contains success
- [ ] `action_id` generated

#### Test 3.2: Non-Admin User
```bash
TOKEN="regular_user_token"

curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "Not authorized - admin required"
}
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Authorization error

#### Test 3.3: Invalid User ID
```bash
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 999999999,
    "target_username": "nonexistent"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "User not found or not in group"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is false
- [ ] Error message returned

#### Test 3.4: Check Database Logging
```bash
# Connect to MongoDB and check action log
# Command: db.actions.findOne({action_type: "UNMUTE"})

# Should contain:
# {
#   "_id": ObjectId(...),
#   "user_id": admin_user_id,
#   "group_id": -1001234567890,
#   "action_type": "UNMUTE",
#   "target_user_id": 123456789,
#   "timestamp": ISODate(...),
#   "status": "success"
# }
```

**Acceptance Criteria:**
- [ ] Action logged in database
- [ ] All fields populated
- [ ] Timestamp correct
- [ ] Status is success

---

### Test 4: POST /commands/promote - Promote User to Admin

**Endpoint:** `POST /api/v1/commands/promote`  
**Permission:** Owner Only  
**Purpose:** Make user admin with optional title

#### Test 4.1: Valid Request (Owner User)
```bash
TOKEN="your_owner_token"

curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe",
    "custom_title": "Moderator"
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "✅ User promoted to admin with title: Moderator",
  "action_id": "promote_-1001234567890_123456789",
  "title_set": true
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is true
- [ ] `message` contains title
- [ ] `title_set` is true
- [ ] `action_id` generated

#### Test 4.2: Promote Without Title
```bash
curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe"
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "✅ User promoted to admin",
  "action_id": "promote_-1001234567890_123456789",
  "title_set": false
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `title_set` is false
- [ ] User promoted without title

#### Test 4.3: Non-Owner User
```bash
TOKEN="admin_user_token"  # Not owner

curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "custom_title": "Moderator"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "Not authorized - owner required"
}
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Owner-only error

#### Test 4.4: Title Too Long
```bash
curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "custom_title": "This is a very long title that exceeds 16 characters"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "Title too long (max 16 characters)"
}
```

**Acceptance Criteria:**
- [ ] Status code 400 or 200 with ok=false
- [ ] Validation error returned

#### Test 4.5: Check Telegram API Integration
- [ ] User appears as admin in Telegram group
- [ ] Custom title appears in group info
- [ ] Admin badge visible in group chat

**Acceptance Criteria:**
- [ ] Telegram group shows new admin
- [ ] Title displayed correctly

---

### Test 5: POST /commands/demote - Demote Admin

**Endpoint:** `POST /api/v1/commands/demote`  
**Permission:** Owner Only  
**Purpose:** Remove admin privileges

#### Test 5.1: Valid Request (Owner User)
```bash
TOKEN="your_owner_token"

curl -X POST http://localhost:8000/api/v1/commands/demote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe"
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "✅ User demoted to regular member",
  "action_id": "demote_-1001234567890_123456789"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is true
- [ ] `message` indicates success
- [ ] `action_id` generated

#### Test 5.2: Non-Owner User
```bash
TOKEN="admin_user_token"  # Not owner

curl -X POST http://localhost:8000/api/v1/commands/demote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 123456789,
    "target_username": "johndoe"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "Not authorized - owner required"
}
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Owner-only error

#### Test 5.3: User Not Admin
```bash
curl -X POST http://localhost:8000/api/v1/commands/demote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": -1001234567890,
    "target_user_id": 999999,  # Regular user
    "target_username": "regularuser"
  }'
```

**Expected Response:**
```json
{
  "ok": false,
  "message": "User is not an admin"
}
```

**Acceptance Criteria:**
- [ ] Status code 200
- [ ] `ok` is false
- [ ] Error message returned

#### Test 5.4: Check Telegram Update
- [ ] User no longer appears as admin
- [ ] Admin badge removed
- [ ] Permissions revoked in Telegram

**Acceptance Criteria:**
- [ ] Telegram group updated
- [ ] Admin status removed

---

## 🌐 Web UI Testing

### Test 6: Web Dashboard Access

#### Test 6.1: Open Dashboard
```
1. Start server: python main.py
2. Open: http://localhost:8000/web/commands.html
3. Verify page loads without errors
```

**Acceptance Criteria:**
- [ ] Page loads successfully
- [ ] All 5 command forms visible
- [ ] Styles load correctly
- [ ] No console errors

#### Test 6.2: Test Free User Form
```
1. Fill "Group ID": -1001234567890
2. Fill "Target User ID": 123456789
3. Fill "Target Username": johndoe
4. Click "Execute"
5. Wait for response
```

**Acceptance Criteria:**
- [ ] Loading indicator shows
- [ ] Response displays in real-time
- [ ] Success or error message shown
- [ ] Form remains functional

#### Test 6.3: Test Get User ID Form
```
1. Fill "Group ID": -1001234567890
2. Fill "Target User ID": 123456789
3. Click "Execute"
4. See user info response
```

**Acceptance Criteria:**
- [ ] User data displayed
- [ ] All fields populated
- [ ] Response formatted nicely

#### Test 6.4: Test Settings Form
```
1. Fill "Group ID": -1001234567890
2. Click "Execute"
3. See admin list
```

**Acceptance Criteria:**
- [ ] Group settings displayed
- [ ] Admin list shown
- [ ] Member count displayed

#### Test 6.5: Test Promote Form (Owner Only)
```
1. Login as owner
2. Fill "Group ID": -1001234567890
3. Fill "Target User ID": 123456789
4. Fill "Custom Title": Moderator
5. Click "Execute"
```

**Acceptance Criteria:**
- [ ] Promotion confirmed
- [ ] Title shows in response
- [ ] User becomes admin in Telegram

#### Test 6.6: Test Demote Form (Owner Only)
```
1. Login as owner
2. Fill "Group ID": -1001234567890
3. Fill "Target User ID": 123456789
4. Click "Execute"
```

**Acceptance Criteria:**
- [ ] Demotion confirmed
- [ ] User loses admin in Telegram

#### Test 6.7: Test Clear Button
```
1. Fill all fields
2. Click "Clear"
3. Verify fields cleared
```

**Acceptance Criteria:**
- [ ] All inputs cleared
- [ ] Response area hidden

#### Test 6.8: Mobile Responsiveness
```
1. Open in mobile device or use DevTools
2. Test form at different sizes
3. Verify responsive layout
```

**Acceptance Criteria:**
- [ ] Layout adjusts properly
- [ ] Forms remain usable
- [ ] No horizontal scroll needed

---

## 📱 TypeScript Service Testing

### Test 7: Service Methods

#### Test 7.1: freeUser() Method
```typescript
const result = await moderationService.freeUser(
  -1001234567890,
  123456789,
  "johndoe"
);

console.log(result.ok);      // Should be true
console.log(result.message); // Should have success message
```

**Acceptance Criteria:**
- [ ] Returns Promise
- [ ] `ok` is true on success
- [ ] `message` contains response text
- [ ] `action_id` populated

#### Test 7.2: getUserID() Method
```typescript
const result = await moderationService.getUserID(
  -1001234567890,
  123456789
);

console.log(result.user?.username);   // Should be johndoe
console.log(result.user?.first_name); // Should have name
```

**Acceptance Criteria:**
- [ ] Returns Promise
- [ ] User object populated
- [ ] All fields present
- [ ] Type-safe response

#### Test 7.3: getGroupSettings() Method
```typescript
const result = await moderationService.getGroupSettings(
  -1001234567890
);

console.log(result.settings?.admins.length); // Should be > 0
console.log(result.settings?.member_count);  // Should be number
```

**Acceptance Criteria:**
- [ ] Returns Promise
- [ ] Settings object populated
- [ ] Admin array present
- [ ] Type-safe response

#### Test 7.4: promoteUser() Method
```typescript
const result = await moderationService.promoteUser(
  -1001234567890,
  123456789,
  "Moderator",
  "johndoe"
);

console.log(result.title_set); // Should be true
console.log(result.ok);        // Should be true
```

**Acceptance Criteria:**
- [ ] Returns Promise
- [ ] `title_set` is true/false appropriately
- [ ] `ok` indicates success
- [ ] `action_id` generated

#### Test 7.5: demoteUser() Method
```typescript
const result = await moderationService.demoteUser(
  -1001234567890,
  123456789,
  "johndoe"
);

console.log(result.ok); // Should be true
```

**Acceptance Criteria:**
- [ ] Returns Promise
- [ ] `ok` is true on success
- [ ] `action_id` generated
- [ ] Admin removed in Telegram

---

## 🔐 Security Testing

### Test 8: Authentication & Authorization

#### Test 8.1: Missing Token
**All endpoints should reject requests without token**
```bash
# Try to call endpoint without authorization header
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should return 401
```

**Acceptance Criteria:**
- [ ] Status code 401
- [ ] Error message returned
- [ ] Action not executed

#### Test 8.2: Expired Token
**System should reject expired tokens**
```bash
# Use an expired token
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer expired_token_here" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should return 401
```

**Acceptance Criteria:**
- [ ] Status code 401
- [ ] Error message returned

#### Test 8.3: Invalid Token
**System should reject malformed tokens**
```bash
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer invalid.token.format" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should return 401
```

**Acceptance Criteria:**
- [ ] Status code 401
- [ ] Error message returned

#### Test 8.4: Non-Admin Access to Admin Endpoint
**Regular users should not access admin endpoints**
```bash
# Login as regular user
curl -X POST http://localhost:8000/api/v1/commands/free \
  -H "Authorization: Bearer regular_user_token" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should return 403
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Forbidden message returned
- [ ] Action not executed

#### Test 8.5: Non-Owner Access to Owner Endpoint
**Admins should not promote/demote**
```bash
# Login as admin (not owner)
curl -X POST http://localhost:8000/api/v1/commands/promote \
  -H "Authorization: Bearer admin_user_token" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should return 403
```

**Acceptance Criteria:**
- [ ] Status code 403
- [ ] Owner-only message returned
- [ ] Action not executed

---

## 📊 Performance Testing

### Test 9: Load Testing

#### Test 9.1: Single Request Performance
```bash
time curl -X POST http://localhost:8000/api/v1/commands/id \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"group_id": -1001234567890, "target_user_id": 123456789}'

# Should complete in < 500ms
```

**Acceptance Criteria:**
- [ ] Response time < 500ms
- [ ] Status code 200
- [ ] Full response returned

#### Test 9.2: Concurrent Requests
```bash
# Send 10 requests in parallel
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/commands/id \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"group_id": -1001234567890, "target_user_id": 123456789}' &
done
wait

# All should succeed
```

**Acceptance Criteria:**
- [ ] All requests return 200
- [ ] No timeout errors
- [ ] Server remains responsive

---

## 📋 Testing Summary Form

### Test Execution Checklist

```
Date: __________
Tester: __________
Environment: __________ (dev/staging/prod)

ENDPOINT TESTS:
[ ] Test 1: POST /commands/id
  [ ] 1.1 Valid request
  [ ] 1.2 Missing token
  [ ] 1.3 Invalid token
  [ ] 1.4 User not found

[ ] Test 2: GET /commands/settings/{id}
  [ ] 2.1 Valid request (admin)
  [ ] 2.2 Non-admin user
  [ ] 2.3 Invalid group ID

[ ] Test 3: POST /commands/free
  [ ] 3.1 Valid request (admin)
  [ ] 3.2 Non-admin user
  [ ] 3.3 Invalid user ID
  [ ] 3.4 Database logging

[ ] Test 4: POST /commands/promote
  [ ] 4.1 Valid request with title
  [ ] 4.2 Valid request without title
  [ ] 4.3 Non-owner user
  [ ] 4.4 Title too long
  [ ] 4.5 Telegram integration

[ ] Test 5: POST /commands/demote
  [ ] 5.1 Valid request (owner)
  [ ] 5.2 Non-owner user
  [ ] 5.3 User not admin
  [ ] 5.4 Telegram integration

WEB UI TESTS:
[ ] Test 6: Web Dashboard
  [ ] 6.1 Page loads
  [ ] 6.2 Free user form
  [ ] 6.3 Get user ID form
  [ ] 6.4 Settings form
  [ ] 6.5 Promote form
  [ ] 6.6 Demote form
  [ ] 6.7 Clear button
  [ ] 6.8 Mobile responsive

SERVICE TESTS:
[ ] Test 7: TypeScript Service
  [ ] 7.1 freeUser() method
  [ ] 7.2 getUserID() method
  [ ] 7.3 getGroupSettings() method
  [ ] 7.4 promoteUser() method
  [ ] 7.5 demoteUser() method

SECURITY TESTS:
[ ] Test 8: Authentication
  [ ] 8.1 Missing token
  [ ] 8.2 Expired token
  [ ] 8.3 Invalid token
  [ ] 8.4 Non-admin access
  [ ] 8.5 Non-owner access

PERFORMANCE TESTS:
[ ] Test 9: Load Testing
  [ ] 9.1 Single request
  [ ] 9.2 Concurrent requests

OVERALL RESULT:
[ ] PASS - All tests passed
[ ] FAIL - Some tests failed (see notes below)

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

Sign-off: _________________________ Date: __________
```

---

## 🎯 Test Execution Order

1. **Pre-Testing** - Setup and data preparation
2. **Endpoint Tests** - Test each API endpoint (Tests 1-5)
3. **Web UI Tests** - Test web dashboard (Test 6)
4. **Service Tests** - Test TypeScript methods (Test 7)
5. **Security Tests** - Test auth/authz (Test 8)
6. **Performance Tests** - Test speed (Test 9)

---

## ✅ Sign-Off

All tests should pass before considering API ready for production.

**Status:** Ready for testing
**Created:** December 31, 2025
**Version:** 1.0
