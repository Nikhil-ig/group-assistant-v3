# 🔇 Quick Reference - Mute/Unmute Commands

## ⚡ Quick Start

### Mute a User
```
/mute (reply to message)
```
**Or with duration:**
```
/mute 30 (reply to message)
```

### Unmute a User
```
/unmute <user_id|@username>
```

---

## 📋 What You'll See

### ✅ Mute Response (Forever)
```
╔═══════════════════════════════════╗
║ 🔇 ACTION EXECUTED                ║
╚═══════════════════════════════════╝

📌 User ID: 501166051
⚡ Action: MUTE
✅ Status: SUCCESS
⏱️  Duration: forever
📍 Result: User muted

🚀 Next Actions Available Below ↓

[🔊 Unmute] [🔨 Ban]
[⚠️ Warn]  [📊 Stats]
```

### ✅ Mute Response (30 Minutes)
```
╔═══════════════════════════════════╗
║ 🔇 ACTION EXECUTED                ║
╚═══════════════════════════════════╝

📌 User ID: 501166051
⚡ Action: MUTE
✅ Status: SUCCESS
⏱️  Duration: for 30 minutes
📍 Result: User muted

🚀 Next Actions Available Below ↓

[🔊 Unmute] [🔨 Ban]
[⚠️ Warn]  [📊 Stats]
```

### ✅ Unmute Response
```
╔═══════════════════════════════════╗
║ 🔊 ACTION EXECUTED                ║
╚═══════════════════════════════════╝

📌 User ID: 501166051
⚡ Action: UNMUTE
✅ Status: SUCCESS
📍 Result: User unmuted

🚀 Next Actions Available Below ↓

[🔇 Mute]     [⚠️ Warn]
[✅ Grant]    [👥 Promote]
```

---

## 🔘 Action Buttons

### Mute Buttons
| Button | Action | Use When |
|--------|--------|----------|
| 🔊 Unmute | Undo mute | Changed mind |
| 🔨 Ban | Ban permanently | Too severe |
| ⚠️ Warn | Warn user | Record needed |
| 📊 Stats | View history | Need info |

### Unmute Buttons
| Button | Action | Use When |
|--------|--------|----------|
| 🔇 Mute | Re-mute | Repeat offense |
| ⚠️ Warn | Warn user | Behavior warning |
| ✅ Grant | Restore perms | Full forgiveness |
| 👥 Promote | Make mod | Reward loyalty |

---

## 📝 Usage Examples

### Example 1: Mute Forever
```
You: /mute (reply to spammer)
Bot: Shows mute response with "Duration: forever"
```

### Example 2: Mute for 1 Hour (60 min)
```
You: /mute 60 (reply to user)
Bot: Shows mute response with "Duration: for 60 minutes"
```

### Example 3: Unmute Specific User
```
You: /unmute 501166051
Bot: Shows unmute response
```

### Example 4: Click a Button
```
You: Click [🔊 Unmute] button
Bot: User unmuted, shows confirmation
```

---

## ✨ Features

### Duration Options
- **Forever:** `/mute` (no number)
- **Temporary:** `/mute <minutes>`

### Information Shown
- User ID
- Action (MUTE/UNMUTE)
- Status (SUCCESS/FAILED)
- Duration (if applicable)
- Result description

### Auto-Actions
- Message auto-deletes after 5 seconds
- Clean chat automatically
- No clutter left behind

---

## 🎯 Complete Commands

### Mute Commands
```bash
/mute                    # Mute forever (reply)
/mute 30                 # Mute 30 min (reply)
/mute 60                 # Mute 1 hour (reply)
/mute 1440               # Mute 1 day (reply)
/mute 501166051          # Mute user ID forever
/mute 501166051 30       # Mute user ID 30 min
/mute @username          # Mute by username forever
/mute @username 60       # Mute by username 60 min
```

### Unmute Commands
```bash
/unmute                  # Unmute (reply)
/unmute 501166051        # Unmute user ID
/unmute @username        # Unmute by username
```

---

## ✅ Verification Checklist

- [x] Mute shows professional format
- [x] Unmute shows professional format
- [x] Duration displays correctly
- [x] All 4 buttons appear
- [x] Buttons are clickable
- [x] Message auto-deletes
- [x] No errors in logs
- [x] Ready for use

---

## 🎨 Visual Layout

```
┌─────────────────────────────────────┐
│    HEADER (Emoji + Title)           │
├─────────────────────────────────────┤
│ 📌 User ID: [number]                │
│ ⚡ Action: [MUTE/UNMUTE]            │
│ ✅ Status: SUCCESS                  │
│ ⏱️  Duration: [forever/X minutes]   │
│ 📍 Result: [action result]          │
├─────────────────────────────────────┤
│ [Button1] [Button2]                 │
│ [Button3] [Button4]                 │
└─────────────────────────────────────┘
```

---

## 💡 Pro Tips

### Tip 1: Combine Actions
```
/mute 30  → Shows response
Click [⚠️ Warn] → Warns user too
```

### Tip 2: Check History
```
/mute 30  → Shows response
Click [📊 Stats] → View user history
```

### Tip 3: Quick Decision
```
/mute forever → Response
Click [🔨 Ban] → Ban instead
```

### Tip 4: Second Chances
```
/unmute 501166051 → Response
Click [✅ Grant] → Restore permissions
```

---

## 🔄 Command Flow

### Mute Workflow
```
1. User sends /mute
   ↓
2. Bot executes mute action
   ↓
3. Shows professional response
   ↓
4. Display 4 action buttons
   ↓
5. Optional: Click a button for follow-up
   ↓
6. Message auto-deletes after 5 seconds
```

### Unmute Workflow
```
1. User sends /unmute <user_id>
   ↓
2. Bot executes unmute action
   ↓
3. Shows professional response
   ↓
4. Display different 4 action buttons
   ↓
5. Optional: Click a button for follow-up
   ↓
6. Message auto-deletes after 5 seconds
```

---

## 📊 Status

| Component | Status |
|-----------|--------|
| Mute Command | ✅ Active |
| Unmute Command | ✅ Active |
| Action Buttons | ✅ Active |
| Duration Display | ✅ Active |
| Professional Format | ✅ Active |
| Bot Connection | ✅ Running |
| API Connection | ✅ Healthy |

---

## 🎯 Key Changes

### What's New
- ✅ Beautiful box formatting
- ✅ Complete information display
- ✅ 4 quick-action buttons
- ✅ Duration shows clearly
- ✅ Professional appearance

### What's Same
- ✅ Command syntax unchanged
- ✅ Duration calculation same
- ✅ Mute functionality same
- ✅ User experience same

---

## 🚀 Ready to Use!

Everything is deployed and running:
- ✅ Bot is polling
- ✅ API is healthy
- ✅ Services are running
- ✅ No errors in logs

**Send `/mute` or `/unmute` to see the new professional format!** 🎉

---

**Version:** 3.0.1  
**Last Updated:** 2026-01-14  
**Status:** ✅ Live & Ready

