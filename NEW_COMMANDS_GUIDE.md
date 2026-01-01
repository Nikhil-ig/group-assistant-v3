# 🆕 New Commands Guide - Dec 31, 2025

**Status:** ✅ Just Added & Ready to Use  
**Commands Added:** 6 new commands  
**Total Bot Commands:** 14 commands

---

## 📋 Quick Overview

| Command | Purpose | Owner Only | Reply Mode |
|---------|---------|-----------|-----------|
| `/free` | Remove all restrictions | ❌ No | ✅ Yes |
| `/id` | Get user ID & info | ❌ No | ✅ Yes |
| `/settings` | Show group settings | ❌ No | ✅ Admin |
| `/promote` | Make user admin | ✅ Yes | ✅ Yes |
| `/demote` | Remove admin | ✅ Yes | ✅ Yes |

---

## 🆓 /free - Remove All Restrictions

**Purpose:** Opposite of `/restrict` - removes ALL restrictions from a user

**Syntax:**
```
Direct mode:   /free <user_id|@username>
Reply mode:    Reply to message → /free
```

**Examples:**
```
/free @user                    (direct mode)
/free 123456                   (direct mode with ID)
(Reply to message) → /free     (reply mode - fastest!)
```

**Response:**
```
🔓 User @user has been freed (all restrictions removed)
```

**Use Cases:**
- User was restricted, now can post normally again
- Temporary restriction expired, re-enable permissions
- Mistake - user wasn't supposed to be restricted

**Who Can Use:** Group admins

---

## 🆔 /id - Get User ID & Information

**Purpose:** Get user ID and information (useful for other commands)

**Syntax:**
```
/id                    (get your own ID)
(Reply to message) → /id    (get that user's ID)
```

**Examples:**
```
/id                           (shows your info)
(Reply to any message) → /id  (shows message sender's info)
```

**Response:**
```
👤 **User Information:**

ID: `123456789`
Name: John Doe
Username: @johndoe
Bot: No

Group ID: `-1001234567890`
Group: My Bot Testing Group
```

**Use Cases:**
- You need someone's ID for `/ban`, `/mute`, etc.
- Verify who you're looking at
- Get group ID for API calls
- Check if account is a bot

**Who Can Use:** Everyone

---

## ⚙️ /settings - Show Group Settings

**Purpose:** View group configuration and admin list

**Syntax:**
```
/settings
```

**Examples:**
```
/settings
```

**Response:**
```
⚙️ **Group Settings for My Group**

Group ID: `-1001234567890`
Type: Supergroup
Members: 156

👥 **Admins (3):**
  • Bot Owner (@owner) - ID: 111111
  • John Admin (@john) - ID: 222222
  • Jane Mod (@jane) - ID: 333333

📋 For detailed settings, use /stats or /logs
```

**What It Shows:**
- ✅ Group ID & type
- ✅ Member count
- ✅ List of admins (with IDs)
- ✅ Admin usernames

**Use Cases:**
- See who has admin powers
- Get group ID for API usage
- Quick group overview

**Who Can Use:** Group admins only

---

## 👑 /promote - Make User Admin

**Purpose:** Promote regular user to group admin with optional custom title

**Syntax:**
```
Direct mode:     /promote <user_id|@username> [custom_title]
Reply mode:      Reply to message → /promote [custom_title]
```

**Examples:**
```
/promote @john                    (make admin with no title)
/promote 123456 Senior Moderator  (make admin with title)
(Reply) → /promote Moderator      (reply mode with title)
(Reply) → /promote                (reply mode, no title)
```

**Response:**
```
👑 User @john has been promoted to admin with title: Senior Moderator
```

**What Gets Enabled:**
- ✅ Delete messages
- ✅ Restrict/unrestrict members
- ✅ Post/edit messages
- ✅ Pin messages
- ✅ Manage voice chats

**Permissions NOT Enabled:**
- ❌ Cannot promote other admins
- ❌ Cannot change group info
- ❌ Cannot manage topics

**Custom Title:**
- Max 16 characters
- Optional parameter
- Examples: "Moderator", "Senior Mod", "Helper"

**Who Can Use:** Group owner only

---

## 👤 /demote - Remove Admin

**Purpose:** Remove admin privileges and make user a regular member

**Syntax:**
```
Direct mode:     /demote <user_id|@username>
Reply mode:      Reply to message → /demote
```

**Examples:**
```
/demote @john           (direct mode)
/demote 123456          (direct mode with ID)
(Reply) → /demote       (reply mode - fastest!)
```

**Response:**
```
👤 User @john has been demoted to regular user
```

**What Gets Disabled:**
- ❌ Delete messages
- ❌ Restrict members
- ❌ Post messages
- ❌ Pin messages
- ❌ All admin powers removed

**Use Cases:**
- Admin misbehaving or left
- Accidentally promoted wrong person
- Temporary admin needs to be removed
- Reorganizing admin team

**Who Can Use:** Group owner only

---

## 📚 Complete Command Reference

### Moderation Commands (Admins)
```
/ban <user>              Ban permanently
/kick <user>             Kick from group
/warn <user>             Give warning
/mute <user> [hours]     Silence user
/unmute <user>           Allow user to speak
/restrict <user> <types> Block specific content
/free <user>             Remove restrictions
```

### Info Commands (Everyone)
```
/id                      Get your ID
/settings                Show group config (admin only)
/stats                   Show statistics (admin only)
/logs                    Show action history (admin only)
```

### Admin Management (Owner)
```
/promote <user> [title]  Make someone admin
/demote <user>           Remove admin
```

---

## 🎯 Real-World Scenarios

### Scenario 1: User Spammed, Now Apologized
```
1. /restrict @user media 24          (restrict for 24 hours)
   ✅ User can't send media

2. *After 24 hours or user apologizes*

3. /free @user                       (remove restrictions)
   ✅ User unrestricted
```

### Scenario 2: New Moderator Needed
```
1. /id                               (reply to their message)
   → Get their ID: 123456

2. /promote 123456 Moderator         (make them admin)
   ✅ They're now admin with title "Moderator"

3. /settings                         (verify)
   ✅ See new admin in list
```

### Scenario 3: Admin Misbehaving
```
1. /settings                         (see who's admin)
   → Find problematic admin

2. /demote @badmin                   (remove their powers)
   ✅ They're back to regular user

3. /ban @badmin                      (if needed)
   ✅ Also ban them
```

### Scenario 4: Quick User Lookup
```
(Reply to any message) → /id
→ Get all info about that user
→ Copy their ID for other commands
```

---

## ⚡ Quick Tips

### 💡 Tip 1: Use Reply Mode for Speed
```
Instead of:  /ban @john_with_long_username_123
Do this:     (Reply to John's message) → /ban
             Result: 10x faster! ⚡
```

### 💡 Tip 2: Custom Titles Have Max Length
```
✅ Works:     /promote @user Moderator         (10 chars)
✅ Works:     /promote @user Senior Mod        (11 chars)
❌ Too Long:  /promote @user Very Long Title   (16+ chars)
```

### 💡 Tip 3: Get ID Before Using Commands
```
1. Reply to user → /id
2. Copy their ID from response
3. Use ID in other commands
```

### 💡 Tip 4: Only Owner Can Promote/Demote
```
If you're not the owner, these commands won't work:
❌ /promote @user
❌ /demote @user

Only the group creator can use them!
```

---

## 🔐 Permission Matrix

| Command | Everyone | Admin | Owner |
|---------|----------|-------|-------|
| /id | ✅ | ✅ | ✅ |
| /free | ❌ | ✅ | ✅ |
| /ban | ❌ | ✅ | ✅ |
| /kick | ❌ | ✅ | ✅ |
| /mute | ❌ | ✅ | ✅ |
| /restrict | ❌ | ✅ | ✅ |
| /settings | ❌ | ✅ | ✅ |
| /stats | ❌ | ✅ | ✅ |
| /logs | ❌ | ✅ | ✅ |
| /promote | ❌ | ❌ | ✅ |
| /demote | ❌ | ❌ | ✅ |

---

## 📖 All Available Commands

### Moderation (12 commands)
1. `/ban` - Ban user
2. `/unban` - Unban user
3. `/kick` - Kick user
4. `/warn` - Warn user
5. `/mute` - Mute user
6. `/unmute` - Unmute user
7. `/restrict` - Restrict permissions
8. `/free` - Remove restrictions (NEW!)
9. `/promote` - Make admin (NEW!)
10. `/demote` - Remove admin (NEW!)

### Info (4 commands)
11. `/id` - Get user ID (NEW!)
12. `/settings` - Show settings (NEW!)
13. `/stats` - Show statistics
14. `/logs` - Show logs

---

## ✨ Features

### ✅ All Support Reply Mode
- Reply to any message
- Type the command
- No need to type user ID
- **3-4x faster!**

### ✅ All Have Logging
- Every action logged to database
- Admin who performed action recorded
- Reason captured
- Timestamp recorded

### ✅ All Have Error Handling
- Clear error messages
- Helpful usage hints
- Graceful failures

### ✅ All Support Both Modes
- Direct: `/command @user`
- Reply: (Reply) → `/command`
- Choose whichever is faster!

---

## 🎬 Step-by-Step: Promote Someone

### Method 1: Direct Mode
```
Step 1: Type /promote @username Moderator
Step 2: Send message
Step 3: Bot responds "User promoted!"
```

### Method 2: Reply Mode (Faster!)
```
Step 1: Find user's message in chat
Step 2: Reply to their message
Step 3: Type /promote Moderator
Step 4: Send
Step 5: Bot responds "User promoted!"
```

---

## 📊 Command Statistics

| Category | Count |
|----------|-------|
| Total Commands | 14 |
| Moderation | 10 |
| Information | 4 |
| Admin Only | 8 |
| Owner Only | 2 |
| Everyone | 1 |

---

## 🚀 What's Next?

These new commands give you complete group management:
- ✅ Full moderation system
- ✅ Admin management
- ✅ User info lookup
- ✅ Group configuration
- ✅ Action history
- ✅ Statistics

**Try them out in your group!** 🎉

---

**Date Added:** 2025-12-31  
**Status:** ✅ Production Ready  
**All Commands:** 14 total

Start using them now! 🚀
