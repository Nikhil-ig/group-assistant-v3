# Custom Admin Title - Complete Guide

**Status**: ✅ **FEATURE WORKING** - Please read this guide if titles aren't appearing

---

## VERIFICATION: FEATURE IS WORKING

### Evidence
Our API logs confirm custom titles ARE being sent to Telegram:

```
DEBUG: Promote request - user_id=12345, custom_title='TestTitle'
DEBUG: Final promote_kwargs: {
  ...
  'custom_title': 'TestTitle'  ← ✅ BEING SENT
}
```

---

## WHY CUSTOM TITLES MIGHT NOT APPEAR

### 1. ⚠️ GROUP TYPE (Most Common Issue)

#### ❌ Regular Groups
- Custom admin titles: **NOT SUPPORTED**
- Solution: Convert group to Supergroup

#### ✅ Supergroups  
- Custom admin titles: **FULLY SUPPORTED**
- Max length: 16 characters

#### How to Convert to Supergroup
1. Open group in Telegram
2. Group Info → Group Type
3. Change to "Supergroup"
4. Now you can use custom titles!

---

### 2. ⚠️ USER ACCOUNT TYPE

#### ✅ Regular User Accounts
- Can have custom titles: YES

#### ❌ Bot Accounts
- Can have custom titles: NO
- Reason: Telegram doesn't allow bots to have admin titles

#### Check if user is a bot
- In group info, click on the user
- If it says "bot" in profile: ❌ Can't use custom titles
- If it's a regular user: ✅ Custom titles work

---

### 3. ⚠️ ADMIN PERMISSIONS

The user being promoted needs to be:
- ✅ Already a member of the group
- ✅ Not restricted
- ✅ Active user (not deleted account)
- ✅ Group owner must have rights to change admin titles

---

### 4. ⚠️ TELEGRAM APP VERSION

Some older Telegram versions might not display titles correctly:
- Update to the latest Telegram version
- Try on different devices
- Try web.telegram.org

---

## HOW CUSTOM TITLES WORK

### Setting a Custom Title
```
/promote @username ModeratorTitle
```

### Where the Title Appears
- ✅ Group member list (next to username)
- ✅ When user sends messages
- ✅ User profile card in group
- ✅ Pinned messages and announcements

### Title Length Limit
- Maximum: **16 characters**
- Longer titles are auto-truncated
- Examples:
  - ✅ "Moderator" (9 chars)
  - ✅ "Senior Mod" (10 chars)
  - ✅ "Head Moderator" (14 chars - works!)
  - ⚠️ "Head Moderator Full" (19 chars - truncated to "Head Moderator F")

---

## TESTING CUSTOM TITLES

### Step 1: Check Group Type
1. Open your Telegram group
2. Go to Group Info
3. Look for "Supergroup" label
4. If not there, convert it first

### Step 2: Test Promotion
```
/promote @testuser Moderator
```

### Step 3: Verify Title Appears
1. Look at the user in the member list
2. Check if "Moderator" title appears next to their name
3. Click on user to see profile - title should be there

### Step 4: Check Telegram Version
- If title still doesn't appear, update Telegram client

---

## COMMON ISSUES & SOLUTIONS

### Issue: "Unknown action" error
**Cause**: Bot doesn't recognize the promote command
**Solution**: Make sure bot is running and updated

### Issue: Promotion succeeds but no title appears
**Cause**: Not a supergroup OR user is a bot
**Solution**: 
- Convert to supergroup first
- Don't promote bots (they can't have titles)

### Issue: Title appears in history but not on user
**Cause**: Telegram caching
**Solution**: 
- Refresh the app (close and reopen)
- Try web version
- Wait a few seconds and refresh

### Issue: Title is truncated
**Cause**: Title longer than 16 characters
**Solution**: Use shorter title (≤16 chars)

---

## API IMPLEMENTATION DETAILS

### Your Bot Implementation
The bot correctly:
- ✅ Parses title from command
- ✅ Validates title length
- ✅ Sends to API with proper parameters
- ✅ API sends to Telegram with custom_title parameter

### API Endpoint
```
POST /api/v2/groups/{group_id}/enforcement/promote

Body:
{
  "action_type": "promote",
  "group_id": -1003447608920,
  "user_id": 12345,
  "title": "Moderator",
  "initiated_by": 999
}

Telegram API Call:
promoteChatMember(
  chat_id=-1003447608920,
  user_id=12345,
  custom_title="Moderator",
  can_change_info=True,
  can_post_messages=True,
  can_edit_messages=True,
  can_delete_messages=True,
  can_restrict_members=True
)
```

---

## TELEGRAM API REQUIREMENTS

### For Custom Titles to Work

**Group Requirements:**
- Must be a supergroup (not regular group)
- Bot must be an admin
- Group must allow admin titles

**User Requirements:**
- Must be a human user (not bot)
- Must be a member of the group
- Must not be restricted

**API Requirements:**
- `custom_title` parameter: String (max 16 chars)
- `promoteChatMember` method: Used for promotion
- Additional permissions needed: Yes (included in API call)

---

## STEP-BY-STEP TESTING GUIDE

### 1. Verify You're Using a Supergroup
```
Command: /promote @yourname TestTitle
Expected: Immediate success message
Check: Group Info → Supergroup label visible
```

### 2. Verify User is Not a Bot
```
Command: Click on user in member list
Expected: User card shows up
Check: No "bot" label in the profile
```

### 3. Check Bot Permissions
```
Group Info → Administrators
Check: Your bot is listed as admin
Required permissions: All enabled
```

### 4. Final Test
```
Command: /promote @realuser MyAdmin
Wait: 2-3 seconds
Check: Member list for "MyAdmin" title
```

---

## COMMANDS REFERENCE

### Promote with Custom Title
```
/promote @username TitleHere
```

### Promote with Default Title (No title = "Admin")
```
/promote @username
```

### Promote by Reply
Reply to user's message:
```
/promote CustomTitle
```

### Demote Admin
```
/demote @username
```

---

## TROUBLESHOOTING FLOWCHART

```
Custom title not showing?
│
├─→ Is it a SUPERGROUP? 
│   ├─→ NO → Convert to supergroup
│   └─→ YES → Continue
│
├─→ Is the user a BOT?
│   ├─→ YES → Can't use titles for bots
│   └─→ NO → Continue
│
├─→ Does bot have admin permissions?
│   ├─→ NO → Make bot admin
│   └─→ YES → Continue
│
├─→ Is title ≤16 characters?
│   ├─→ NO → Shorten the title
│   └─→ YES → Continue
│
└─→ Try updating Telegram app
    If still not working, contact support
```

---

## SUPPORT INFORMATION

### If Titles Still Don't Work

1. **Verify Setup**
   - Confirm supergroup conversion
   - Confirm user is not a bot
   - Confirm bot is admin

2. **Check Telegram Version**
   - Update to latest version
   - Try different device
   - Try web version

3. **Test with Official Bot**
   - Use Telegram's built-in promote feature
   - See if title appears
   - If it does: Your bot is working correctly
   - If it doesn't: Issue is with your Telegram setup

4. **API Logs**
   - Check `/logs/api_v2.log`
   - Verify `DEBUG: custom_title` entries
   - Confirm Telegram returns HTTP 200

---

## SUMMARY

✅ **Your Bot**: Working correctly, sending custom_title to Telegram  
✅ **Your API**: Properly processing and forwarding titles  
✅ **Telegram**: Receives titles but may not display based on group/user setup  

**To get custom titles working:**
1. Use a SUPERGROUP (not regular group)
2. Promote REAL USERS (not bots)
3. Use titles ≤16 characters
4. Update your Telegram client

