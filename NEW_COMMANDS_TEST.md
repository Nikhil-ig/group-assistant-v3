# 🧪 Testing Guide - New Commands

**Date:** 2025-12-31  
**Commands to Test:** 5 new commands  
**Estimated Time:** 15-20 minutes

---

## ✅ Pre-Test Checklist

Before testing, ensure:
- [ ] Bot is running in your test group
- [ ] You're the group owner (for /promote, /demote tests)
- [ ] You have admin powers
- [ ] Have a test user to use with commands
- [ ] Bot has admin permissions in group

---

## 🆓 Test 1: /free Command

### Setup
```
1. Have a test user ready
2. Restrict them first: /restrict @testuser media
   Expected: User restricted
```

### Test 1a: Direct Mode (by username)
```
Command:  /free @testuser
Expected: 🔓 User @testuser has been freed
Result:   ✅ PASS or ❌ FAIL
```

### Test 1b: Direct Mode (by ID)
```
Command:  /free 123456          (use actual ID from /id)
Expected: 🔓 User [name] has been freed
Result:   ✅ PASS or ❌ FAIL
```

### Test 1c: Reply Mode
```
1. Reply to @testuser's message
2. Type: /free
Expected: 🔓 User has been freed
Result:   ✅ PASS or ❌ FAIL
```

### Test 1d: Verify Unrestricted
```
Have test user try to post media
Expected: Should post successfully
Result:   ✅ PASS or ❌ FAIL
```

### Test 1e: Error - Not Admin
```
Test from non-admin account:
Command:  /free @user
Expected: ⚠️ Only admins can use this
Result:   ✅ PASS or ❌ FAIL
```

### Test Results
- [ ] Test 1a: PASS ✅
- [ ] Test 1b: PASS ✅
- [ ] Test 1c: PASS ✅
- [ ] Test 1d: PASS ✅
- [ ] Test 1e: PASS ✅

---

## 🆔 Test 2: /id Command

### Setup
```
1. Have a test user available
2. Note: Everyone can use /id
```

### Test 2a: Get Own ID
```
Command:  /id
Expected: Shows YOUR ID, name, username, bot status, group ID
Result:   ✅ PASS or ❌ FAIL

Sample Response:
👤 **User Information:**
ID: `123456789`
Name: Your Name
Username: @yourname
Bot: No

Group ID: `-1001234567890`
Group: Test Group
```

### Test 2b: Reply Mode - Get User Info
```
1. Reply to @testuser's message
2. Type: /id
Expected: Shows THEIR ID, name, username, same group
Result:   ✅ PASS or ❌ FAIL
```

### Test 2c: Verify ID Format
```
Check that:
- ID is in backticks ✅
- Name shows first + last if available ✅
- Username shows with @ ✅
- Group ID is negative number ✅
- Bot status shows Yes/No ✅
Result:   ✅ PASS or ❌ FAIL
```

### Test 2d: Works in DM
```
Send /id in DM to bot
Expected: Shows your ID (no group info)
Result:   ✅ PASS or ❌ FAIL
```

### Test Results
- [ ] Test 2a: PASS ✅
- [ ] Test 2b: PASS ✅
- [ ] Test 2c: PASS ✅
- [ ] Test 2d: PASS ✅

---

## ⚙️ Test 3: /settings Command

### Setup
```
1. Must be in a group
2. Must be admin
3. At least 2 admins should exist
```

### Test 3a: Basic Command
```
Command:  /settings
Expected: Shows group ID, type, member count, admin list
Result:   ✅ PASS or ❌ FAIL

Sample Response:
⚙️ **Group Settings**
Group ID: `-1001234567890`
Type: Supergroup
Members: 156

👥 **Admins:**
  • Bot Owner (@owner) - ID: 111111
  • John (@john) - ID: 222222
```

### Test 3b: Verify All Info Shows
```
Check:
- ✅ Group ID shown
- ✅ Group type shown (Group/Supergroup)
- ✅ Member count shown
- ✅ Admin names shown
- ✅ Admin IDs shown
- ✅ Admin usernames shown
Result:   ✅ PASS or ❌ FAIL
```

### Test 3c: Error - Not Admin
```
Test from non-admin account:
Command:  /settings
Expected: ⚠️ Only admins can use this
Result:   ✅ PASS or ❌ FAIL
```

### Test 3d: Admin List Limit
```
If group has 15+ admins:
Expected: Shows first 10, then "(5 more admins)"
Result:   ✅ PASS or ❌ FAIL
```

### Test Results
- [ ] Test 3a: PASS ✅
- [ ] Test 3b: PASS ✅
- [ ] Test 3c: PASS ✅
- [ ] Test 3d: PASS ✅

---

## 👑 Test 4: /promote Command

### Setup
```
1. MUST be group owner to test
2. Have a regular user ready
3. This is an owner-only command
```

### Test 4a: Promote Without Title
```
Command:  /promote @testuser
Expected: 👑 @testuser promoted to admin (no title)
Result:   ✅ PASS or ❌ FAIL
```

### Test 4b: Promote With Title
```
Command:  /promote @testuser Moderator
Expected: 👑 @testuser promoted to admin
         Title set to: Moderator
Result:   ✅ PASS or ❌ FAIL
```

### Test 4c: Reply Mode Without Title
```
1. Reply to user's message
2. Type: /promote
Expected: 👑 User promoted to admin
Result:   ✅ PASS or ❌ FAIL
```

### Test 4d: Reply Mode With Title
```
1. Reply to different user's message
2. Type: /promote Senior Moderator
Expected: 👑 User promoted with title
Result:   ✅ PASS or ❌ FAIL
```

### Test 4e: Title Length Limit
```
Try: /promote @user VeryLongTitleThatExceeds16Characters
Expected: Either truncated to 16 chars OR error
Result:   ✅ PASS or ❌ FAIL
```

### Test 4f: Verify Promotion
```
After promoting @testuser:
Command:  /settings
Expected: @testuser appears in admin list
Result:   ✅ PASS or ❌ FAIL
```

### Test 4g: Error - Not Owner (as admin)
```
From admin account (not owner):
Command:  /promote @user
Expected: ⚠️ Only owner can promote
Result:   ✅ PASS or ❌ FAIL
```

### Test 4h: Verify Admin Can Post
```
As newly promoted admin:
Try posting in restricted channel
Expected: Should be able to post
Result:   ✅ PASS or ❌ FAIL
```

### Test Results
- [ ] Test 4a: PASS ✅
- [ ] Test 4b: PASS ✅
- [ ] Test 4c: PASS ✅
- [ ] Test 4d: PASS ✅
- [ ] Test 4e: PASS ✅
- [ ] Test 4f: PASS ✅
- [ ] Test 4g: PASS ✅
- [ ] Test 4h: PASS ✅

---

## 👤 Test 5: /demote Command

### Setup
```
1. MUST be group owner
2. Have an admin to demote (or use one you just promoted)
3. This is owner-only
```

### Test 5a: Demote Admin
```
Command:  /demote @admin (someone you promoted)
Expected: 👤 @admin demoted to regular user
Result:   ✅ PASS or ❌ FAIL
```

### Test 5b: Demote By ID
```
Command:  /demote 123456 (ID of admin)
Expected: 👤 User demoted
Result:   ✅ PASS or ❌ FAIL
```

### Test 5c: Reply Mode
```
1. Reply to message from an admin
2. Type: /demote
Expected: 👤 User demoted
Result:   ✅ PASS or ❌ FAIL
```

### Test 5d: Verify Demotion
```
Command:  /settings
Expected: Demoted user NO LONGER in admin list
Result:   ✅ PASS or ❌ FAIL
```

### Test 5e: Verify Lost Powers
```
As demoted user, try:
- Delete someone's message (should fail)
- Restrict someone (should fail)
Expected: All admin powers gone
Result:   ✅ PASS or ❌ FAIL
```

### Test 5f: Error - Not Owner
```
From non-owner account:
Command:  /demote @user
Expected: ⚠️ Only owner can demote
Result:   ✅ PASS or ❌ FAIL
```

### Test Results
- [ ] Test 5a: PASS ✅
- [ ] Test 5b: PASS ✅
- [ ] Test 5c: PASS ✅
- [ ] Test 5d: PASS ✅
- [ ] Test 5e: PASS ✅
- [ ] Test 5f: PASS ✅

---

## 🗄️ Database Logging Tests

### Test 6: Verify Logging

```
After running all tests, check:

Log Entry 1 (/free):
- Action: UNMUTE
- User: @testuser
- Admin: You
- Group: Your group
- Timestamp: Recent

Log Entry 2 (/promote):
- Action: WARN (promotion)
- User: @testuser
- Admin: You
- Reason: "Promoted to admin"
- Timestamp: Recent

Log Entry 3 (/demote):
- Action: WARN (demotion)
- User: @admin
- Admin: You
- Reason: "Demoted from admin"
- Timestamp: Recent

Result: ✅ PASS or ❌ FAIL
```

### Check Logs Command
```
Command:  /logs
Expected: All recent actions visible
Result:   ✅ PASS or ❌ FAIL
```

---

## 🔄 Integration Tests

### Test 7: Complete Workflow

```
Scenario: Promote someone, restrict them, then free and demote

Step 1: /promote @testuser Moderator
Result: ✅ Promoted

Step 2: /restrict @testuser media 12
Result: ✅ Restricted (12 hours)

Step 3: /free @testuser
Result: ✅ Freed

Step 4: /demote @testuser
Result: ✅ Demoted

Check /logs:
Result: ✅ All 4 actions logged
```

### Test 8: Reply Mode Workflow

```
Scenario: Use reply mode for multiple operations

Step 1: Find user message
Step 2: Reply → /id
Result: ✅ Got their ID

Step 3: Reply again → /promote Moderator
Result: ✅ Promoted

Step 4: Reply again → /demote
Result: ✅ Demoted

Check speed:
Result: ✅ Faster than typing IDs
```

---

## 📊 Summary Table

| Test | Status | Date | Notes |
|------|--------|------|-------|
| /free direct | ⬜ | | |
| /free reply | ⬜ | | |
| /free error | ⬜ | | |
| /id own | ⬜ | | |
| /id reply | ⬜ | | |
| /id format | ⬜ | | |
| /settings | ⬜ | | |
| /settings error | ⬜ | | |
| /promote basic | ⬜ | | |
| /promote title | ⬜ | | |
| /promote reply | ⬜ | | |
| /promote error | ⬜ | | |
| /demote basic | ⬜ | | |
| /demote reply | ⬜ | | |
| /demote error | ⬜ | | |
| Logging | ⬜ | | |
| Workflow | ⬜ | | |

---

## ✨ Expected Results Summary

### Commands Should Work
- ✅ /free - Remove restrictions
- ✅ /id - Show user info  
- ✅ /settings - Show group config
- ✅ /promote - Make admin
- ✅ /demote - Remove admin

### Reply Mode Should Work
- ✅ /free (reply to message)
- ✅ /id (reply to message)
- ✅ /promote (reply to message)
- ✅ /demote (reply to message)

### Permissions Should Work
- ✅ Admin checks on /free, /settings
- ✅ Owner checks on /promote, /demote
- ✅ No permission needed for /id

### Logging Should Work
- ✅ Every action in database
- ✅ /logs shows all actions
- ✅ Admin name recorded
- ✅ Timestamp recorded

---

## 🚀 Final Checklist

- [ ] All 5 commands working
- [ ] Reply mode working (4 commands)
- [ ] Permission checks working
- [ ] Error messages clear
- [ ] Database logging working
- [ ] All tests passed
- [ ] No errors in logs
- [ ] Ready for production

---

## 📝 Notes

**Date Created:** 2025-12-31  
**Commands Tested:** 5  
**Test Cases:** 30+  
**Time Needed:** 15-20 minutes  
**Priority:** High

**Next Steps After Testing:**
1. ✅ Mark all as PASS
2. 🚀 Deploy to production
3. 📢 Announce new features
4. 🎓 Train moderators
5. 📊 Monitor usage

---

**Status:** Ready for Testing  
**Good luck!** 🎉
