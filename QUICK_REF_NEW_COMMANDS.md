# ⚡ Quick Reference - New Commands

**Commands Added:** 5 new commands (Dec 31, 2025)

---

## 📋 Command Cheatsheet

### 🆓 /free - Remove Restrictions
```
Usage:    /free @user           Direct mode
         (Reply) → /free        Reply mode
Purpose:  Opposite of /restrict - removes ALL restrictions
Who:      Admins only
Example:  /free @spammer
```

### 🆔 /id - Get User ID
```
Usage:    /id                   Get your ID
         (Reply) → /id          Get their ID
Purpose:  Get user ID & info (useful for other commands)
Who:      Everyone
Example:  /id
Response: Shows ID, name, username, group info
```

### ⚙️ /settings - Group Config
```
Usage:    /settings
Purpose:  Show group settings & admin list
Who:      Admins only
Example:  /settings
```

### 👑 /promote - Make Admin
```
Usage:    /promote @user                Make admin
         /promote @user Title           With custom title
         (Reply) → /promote Title       Reply mode
Purpose:  Promote user to admin (with optional title)
Who:      OWNER ONLY
Title:    Max 16 characters
Example:  /promote @john Moderator
```

### 👤 /demote - Remove Admin
```
Usage:    /demote @user         Direct mode
         (Reply) → /demote      Reply mode
Purpose:  Remove admin status, make regular user
Who:      OWNER ONLY
Example:  /demote @john
```

---

## 🎯 When to Use Each

| Situation | Command |
|-----------|---------|
| User was restricted, now OK | `/free @user` |
| Need someone's ID for commands | `/id` (reply) |
| See who has admin powers | `/settings` |
| Make someone a moderator | `/promote @user` |
| Remove moderator powers | `/demote @user` |

---

## ✨ Reply Mode is 4x Faster!

### ❌ Slow Way (Direct)
```
/promote @john_with_super_long_username_123 Moderator
(Type all that out... slow!)
```

### ✅ Fast Way (Reply)
```
(Click reply on John's message)
(Type: /promote Moderator)
(Send!)
(Done in half the time! ⚡)
```

---

## 📊 Permissions Summary

| Command | Permission | Owner | Admin | User |
|---------|-----------|-------|-------|------|
| /free | ✅ | ✅ | ✅ | ❌ |
| /id | ✅ | ✅ | ✅ | ✅ |
| /settings | ✅ | ✅ | ✅ | ❌ |
| /promote | ✅ Owner only | ✅ | ❌ | ❌ |
| /demote | ✅ Owner only | ✅ | ❌ | ❌ |

---

## 🚀 Quick Examples

### Example 1: Someone Spammed Photos
```
Step 1: /restrict @spammer photos 24
Result: Can't send photos for 24 hours

Step 2: (After 24 hours or they apologized)
Step 2: /free @spammer
Result: All restrictions removed, can post normally
```

### Example 2: Need New Moderator
```
Step 1: (Reply to someone's message) → /id
Result: Get their ID

Step 2: /promote @person Moderator
Result: They're now a moderator

Step 3: /settings
Result: See them in admin list
```

### Example 3: Quick ID Lookup
```
Just reply to any message and type /id
Get: Their ID, name, username, bot status
No need to ask "what's your ID?" - just use reply mode!
```

---

## ⚡ Tips & Tricks

### 💡 Tip 1: Use Reply Mode
- 3-4x faster than typing names
- Perfect for busy chats
- No typos in usernames

### 💡 Tip 2: Get ID First
```
(Reply) → /id
→ Copy ID
→ Use in other commands (/ban, /kick, etc)
```

### 💡 Tip 3: Check Admins Before Promoting
```
/settings
→ See current admins
→ Then promote using /promote
```

### 💡 Tip 4: Title Limit
- Max: 16 characters
- Examples: "Moderator", "Senior Mod", "Helper"

### 💡 Tip 5: Only Owner Can Promote/Demote
- These are OWNER-ONLY commands
- Admins can use other commands
- This protects group hierarchy

---

## 🔐 Security Notes

### ✅ Permission Checks Active
- Every command validates permissions
- Owner-only commands are strict
- Admin commands require admin role
- Regular users get clear errors

### ✅ All Actions Logged
- Database records every change
- Admin name recorded
- Timestamp recorded
- Check /logs for history

### ✅ Safe to Use
- Commands validated thoroughly
- Error handling comprehensive
- No way to break group permissions
- Graceful failure handling

---

## 📞 Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Only admins can use this" | Not an admin | Ask owner to make you admin |
| "Only owner can promote" | Not the owner | Only group creator can do this |
| "User not found" | Bad username/ID | Check spelling or use /id to get ID |
| "Bot needs admin rights" | Bot not admin | Make bot an admin in group |

---

## 🎬 Video-Style Guides

### 30-Second: Get Someone's ID
```
1. Reply to their message
2. Type: /id
3. Copy the ID
4. Use in other commands
```

### 1-Minute: Make Someone Admin
```
1. Type: /promote @username Moderator
2. Check with: /settings
3. They're now a moderator!
4. To remove: /demote @username
```

### 2-Minute: Complete Admin Workflow
```
1. /settings → See current admins
2. /promote @john Moderator → Make admin
3. /settings → Verify in list
4. /demote @jane → Remove admin
5. /settings → Verify removed
6. /logs → See all actions
```

---

## 📱 Mobile Quick Taps

### iPhone/Android Optimization
```
Best for phone: Use reply mode! ↓
(Tap reply)
(Type: /free)
(Send)
✅ Done! Much easier on mobile.

Avoid:
/free @superlongusernamethatshardtotype_123
(Hard to type on phone, easy to typo)
```

---

## 🔄 Command Flow

```
Need to manage admin?
    ↓
Use /promote (owner only)
    ↓
Use /demote (owner only)
    ↓
Check with /settings (admin+)
    ↓
View history /logs (admin+)
```

```
Need to check user info?
    ↓
Use /id (everyone)
    ↓
Copy their ID
    ↓
Use in other commands
```

```
Need to remove restrictions?
    ↓
Use /free (admin+)
    ↓
Verify with reply mode
```

---

## 📊 All 14 Commands Summary

### Moderation (10)
1. `/ban @user` - Ban permanently
2. `/unban @user` - Unban
3. `/kick @user` - Kick from group
4. `/warn @user` - Give warning
5. `/mute @user` - Silence
6. `/unmute @user` - Allow speaking
7. `/restrict @user types` - Block content
8. `/free @user` - **NEW!** Remove restrictions
9. `/promote @user` - **NEW!** Make admin
10. `/demote @user` - **NEW!** Remove admin

### Info (4)
11. `/id` - **NEW!** Get user ID
12. `/settings` - **NEW!** Show group config
13. `/stats` - Show statistics
14. `/logs` - Show action history

---

## ✅ Verification Checklist

After using a command, verify:

### /free
- [ ] User can post again
- [ ] /logs shows UNMUTE action
- [ ] No restrictions shown for user

### /id
- [ ] Shows ID in backticks
- [ ] Shows name, username
- [ ] Shows group info (if in group)

### /settings
- [ ] Shows group ID
- [ ] Shows member count
- [ ] Shows admin list
- [ ] Shows at least 2 admins

### /promote
- [ ] User now in /settings admin list
- [ ] /logs shows WARN action
- [ ] User can perform admin actions

### /demote
- [ ] User removed from /settings list
- [ ] User can't delete messages anymore
- [ ] /logs shows WARN action

---

## 🎁 Bonus Tips

### Tip: Batch Operations
```
Need to manage multiple admins?
/settings → See all admins
/promote @person1 Mod → Add
/promote @person2 Mod → Add
/demote @person3 → Remove
/settings → Verify all
```

### Tip: New Groups
```
New group setup:
1. Add bot
2. /promote @admin1 Admin → Make admins
3. /promote @admin2 Admin
4. /settings → Verify
5. Done! Group ready
```

### Tip: Group Migration
```
Moving admins between groups:
1. /settings → Get admin list
2. Share admin list with new group owner
3. /promote each person in new group
4. Done!
```

---

## 📞 Support

### Common Questions

**Q: Can admins promote people?**  
A: No, only the group owner can promote/demote

**Q: Can I promote the bot?**  
A: No, bot is always admin by itself

**Q: Does /id show in DMs?**  
A: Yes, it works in DM and groups

**Q: Can I give multiple titles?**  
A: No, only one title per person (max 16 chars)

**Q: Are all actions logged?**  
A: Yes, check /logs for all changes

---

## 🎉 You're All Set!

- ✅ Understand all 5 new commands
- ✅ Know when to use each one
- ✅ Know reply mode shortcuts
- ✅ Ready to manage your group!

**Start using them now!** 🚀

---

**Last Updated:** 2025-12-31  
**Status:** ✅ Production Ready  
**Print this page or save as PDF** for quick reference!
