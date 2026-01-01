# 🎨 User Interface & Experience Guide

## Web Dashboard Flow

### 1. Login Page
```
┌─────────────────────────────────────────┐
│     GUARDIAN BOT - Web Dashboard        │
│                                         │
│  🔐 LOGIN                               │
│                                         │
│  User ID:  [  123456789   ]             │
│  Username: [  admin       ]             │
│                                         │
│           [   Login   ]                 │
│                                         │
│  Demo Credentials:                      │
│  - ID: 123456789                        │
│  - Username: admin                      │
│  - Role: Superadmin (sees all groups)   │
│                                         │
└─────────────────────────────────────────┘
```

### 2. Dashboard Home
```
┌──────────────────────────────────────────────────────┐
│ GUARDIAN BOT Dashboard                      [Logout] │
├──────────────────────────────────────────────────────┤
│                                                       │
│  📊 Your Statistics                                   │
│  ┌─────────────┬─────────────┬─────────────┐        │
│  │ Total       │ Total       │ Active      │        │
│  │ Groups: 5   │ Members: 240│ Admins: 12  │        │
│  └─────────────┴─────────────┴─────────────┘        │
│                                                       │
│  🏘️ Your Groups                                       │
│  ┌──────────────────────────────────────────┐        │
│  │ ✓ Tech Group              50 members      │  👉    │
│  │ ✓ Gaming Community        120 members     │  👉    │
│  │ ✓ Dev Team               30 members      │  👉    │
│  │ ✓ Support Team           25 members      │  👉    │
│  │ ✓ Marketing              15 members      │  👉    │
│  └──────────────────────────────────────────┘        │
│                                                       │
│  Recent Actions                                       │
│  ├─ 2 hours ago: @admin banned @spambot             │
│  ├─ 4 hours ago: @moderator warned @user1           │
│  ├─ 6 hours ago: @admin muted @spam2 for 24h        │
│  └─ 1 day ago: New group "Test Group" created       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 3. Group Detail Page (Click Group)
```
┌─────────────────────────────────────────────────────────┐
│ < Back | Tech Group                          [Settings] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Group Stats                                          │
│  ├─ Members: 50                                          │
│  ├─ Admins: 2                                            │
│  ├─ Banned: 3                                            │
│  ├─ Muted: 1                                             │
│  └─ Total Actions: 45                                    │
│                                                          │
│  👥 Members (Searchable)                                 │
│  ┌────────────────────────────────────────────┐         │
│  │ Search members... [────────────────────]   │         │
│  │                                             │         │
│  │ [Sort by: Name ▼] [Filter: All ▼]         │         │
│  │                                             │         │
│  │ Name         | Status    | Warns | Actions│         │
│  ├────────────────────────────────────────────┤         │
│  │ @john_doe    │ Active    │ 0     │ ⏳ ⏭️  │         │
│  │ @jane_admin  │ Admin     │ 0     │ 👤 ⏳   │         │
│  │ @spambot_1   │ Banned    │ 5     │ 🔓 👤  │         │
│  │ @user_123    │ Muted     │ 2     │ 🔊 👤  │         │
│  │ @guest_user  │ Active    │ 1     │ ⏳ 👤  │         │
│  │ ...          │ ...       │ ...   │ ...    │         │
│  └────────────────────────────────────────────┘         │
│     ⏳ = Mute/Unmute                                     │
│     🔓 = Unban                                          │
│     👤 = Promote/Demote                                 │
│     ⏭️ = Kick                                           │
│                                                          │
│  ⚡ Real-Time Action Log                                │
│  ┌────────────────────────────────────────────┐         │
│  │ [Filter: All ▼] [Last 24h ▼]              │         │
│  │                                             │         │
│  │ 14:32  [WEB]  @admin banned @spambot      │         │
│  │        Reason: "Spam"                      │         │
│  │                                             │         │
│  │ 14:15  [BOT]  @admin muted @user_123      │         │
│  │        Duration: 24 hours                  │         │
│  │        Reason: "Spam messages"             │         │
│  │                                             │         │
│  │ 13:45  [BOT]  @admin warned @user_456     │         │
│  │        Reason: "Off-topic"                 │         │
│  │                                             │         │
│  │ 12:00  [WEB]  @admin promoted @john       │         │
│  │        New Role: Moderator                 │         │
│  │                                             │         │
│  └────────────────────────────────────────────┘         │
│     [WEB] = Action from web dashboard                   │
│     [BOT] = Action from bot command                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4. Member Quick Action (Click Member)
```
┌─────────────────────────────────────┐
│ @spambot_1                          │
│ User ID: 987654321                  │
├─────────────────────────────────────┤
│                                     │
│ Status:     Banned                  │
│ Joined:     2025-01-15              │
│ Warns:      5/3 (threshold hit)     │
│ Ban Reason: Spam                    │
│                                     │
├─────────────────────────────────────┤
│ Quick Actions:                      │
│                                     │
│ [ 🔓 Unban User ]                   │
│ [ 🚫 Ban User ]                     │
│ [ 🔇 Mute User ]                    │
│ [ ⏭️ Kick User ]                     │
│ [ ⚠️ Warn User ]                     │
│ [ 👤 Promote Admin ]                │
│ [ 🔼 Demote Admin ]                 │
│ [ 💬 Send Message ]                 │
│                                     │
├─────────────────────────────────────┤
│ Close                               │
└─────────────────────────────────────┘
```

### 5. Ban User Dialog
```
┌──────────────────────────────────────┐
│ Ban User: @spambot_1                 │
├──────────────────────────────────────┤
│                                      │
│ User: @spambot_1 (987654321)        │
│                                      │
│ Ban Reason: [Spam Bot           ]   │
│                                      │
│ Duration:   [Permanent ▼]           │
│             ├─ 1 hour               │
│             ├─ 24 hours             │
│             ├─ 7 days               │
│             ├─ 30 days              │
│             └─ Permanent            │
│                                      │
│ Also mute:  [ ] Mute user first     │
│                                      │
│ Notify:     [✓] Send notification   │
│                                      │
├──────────────────────────────────────┤
│  [ Ban User ]  [ Cancel ]            │
│                                      │
│ Note: User will be immediately      │
│ banned from the group. Cannot        │
│ send messages or reactions.          │
│                                      │
└──────────────────────────────────────┘
```

### 6. Real-Time Notification (Toast)
```
Top-right corner of dashboard:

┌────────────────────────────────────┐
│ ✅ @admin banned @spambot          │  ← Auto-disappears in 5s
│    Reason: Spam                    │
└────────────────────────────────────┘

Or:

┌────────────────────────────────────┐
│ ⚠️ @admin warned @user_123         │
│    Reason: Off-topic               │
└────────────────────────────────────┘

Or:

┌────────────────────────────────────┐
│ 🔇 @admin muted @spam_bot for 24h │
└────────────────────────────────────┘
```

### 7. Group Settings Panel
```
┌──────────────────────────────────────────────┐
│ Tech Group Settings                [Save]    │
├──────────────────────────────────────────────┤
│                                              │
│ 📋 General                                    │
│ ├─ Group Name: [Tech Group             ]    │
│ ├─ Description: [Community for tech..   ]    │
│ └─ Avatar: [Choose File]  [Current]      │
│                                              │
│ 🛡️ Moderation                                 │
│ ├─ Auto-Mod Enabled: [✓]                    │
│ ├─ Warn Threshold: [3]     (ban after 3)    │
│ ├─ Ban on Threshold: [✓]                    │
│ ├─ Default Mute Duration: [24] hours        │
│ └─ Filter Spam: [✓]                         │
│                                              │
│ 🎯 Rules & Welcome                           │
│ ├─ Welcome Enabled: [✓]                     │
│ ├─ Welcome Message: [────────────────]      │
│ ├─ Rules Enabled: [✓]                       │
│ └─ Rules: [─────────────────────────────]   │
│                                              │
│ 👥 Permissions                               │
│ ├─ Owner: @admin                            │
│ ├─ Moderators: @jane_admin, @john_mod      │
│ └─ Admin Permissions:                       │
│    ├─ [✓] Can Ban Users                     │
│    ├─ [✓] Can Mute Users                    │
│    ├─ [✓] Can Kick Users                    │
│    ├─ [✓] Can Warn Users                    │
│    ├─ [✓] Can Manage Admins                 │
│    └─ [✓] Can Change Settings               │
│                                              │
├──────────────────────────────────────────────┤
│  [ Save Changes ]  [ Reset ]  [ Close ]     │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Telegram Bot Commands Flow

```
User types in Telegram group:
└─ /ban @john Spam

Bot responds:
├─ Processes command
├─ Validates user permissions
├─ Executes ban in Telegram
├─ Stores in database
├─ Publishes to Redis
└─ WebSocket notifies all web clients

Web Dashboard updates:
├─ Toast: "Admin banned @john"
├─ Removes @john from members list
├─ Adds to "Banned Users" section
├─ Updates logs
└─ All in REAL-TIME ⚡
```

---

## Real-Time Indicator

```
Top of dashboard, next to group name:

Status Indicators:
├─ ⚡ Listening for bot actions (green)
│  └─ When WebSocket is connected
│
├─ ⏳ Connecting (yellow)
│  └─ Temporary during reconnect
│
└─ 🔌 Disconnected (red)
   └─ Reconnects automatically

Example:
┌──────────────────────────────────┐
│ Tech Group ⚡ Listening...       │
│           Listening for bot      │
│           actions...             │
└──────────────────────────────────┘
```

---

## Mobile View (Responsive)

```
┌──────────────────────┐
│ ◀ Tech Group  ⋮      │
├──────────────────────┤
│                      │
│ 📊 Stats             │
│ ├─ Members: 50       │
│ ├─ Admins: 2         │
│ └─ Banned: 3         │
│                      │
│ 👥 Members (5)       │
│ ├─ @john_doe ⋮      │
│ ├─ @jane_admin ⋮    │
│ ├─ @spambot ⋮       │
│ ├─ @user_123 ⋮      │
│ └─ @guest ⋮         │
│                      │
│ 📋 Recent Actions    │
│ ├─ Banned @spam...   │
│ ├─ Muted @user...    │
│ └─ Warned @...       │
│                      │
└──────────────────────┘

Tap ⋮ for member actions
Swipe left for quick actions
```

---

## Workflow Examples

### Example 1: Ban Spammer via Web
```
1. Admin opens web dashboard
   └─ Sees list of members

2. Admin clicks on @spambot
   └─ Member detail card opens

3. Admin clicks [🚫 Ban User]
   └─ Ban dialog appears

4. Admin enters reason: "Spam"
   └─ Clicks [Ban User]

5. Web sends: POST /api/v1/groups/{id}/ban
   └─ {user_id: 987654321, reason: "Spam"}

6. Backend executes:
   └─ bot.ban_chat_member()
   └─ Stores in database
   └─ Publishes to Redis

7. Result:
   ✅ User banned in Telegram (all users see it)
   ✅ Web dashboard updates in real-time
   ✅ Appears in action logs
   ✅ Removed from members list
```

### Example 2: Moderate via Bot Command
```
1. Moderator in Telegram group
   └─ Types: /warn @user_123 Off-topic

2. Bot processes:
   └─ Validates permission
   └─ Executes warning
   └─ Stores in database
   └─ Publishes to Redis

3. Web Dashboard updates:
   ✅ Toast: "@admin warned @user_123"
   ✅ User's warn count increases (1/3)
   ✅ Appears in action logs
   ✅ All clients see it INSTANTLY

4. If warn count hits 3:
   └─ Auto-ban triggered
   └─ All logs updated
   └─ Dashboard reflects new status
```

### Example 3: Promote Admin
```
1. Owner in web dashboard
   └─ Clicks member @john_doe
   └─ Clicks [👤 Promote Admin]

2. Dialog appears:
   └─ Asks for confirmation
   └─ Lists permissions @john will have

3. Owner confirms
   └─ Web sends: POST /api/v1/groups/{id}/promote

4. Backend:
   └─ Updates member role
   └─ Grants admin permissions in Telegram
   └─ Stores in database

5. Result:
   ✅ @john becomes admin (Telegram shows)
   ✅ Web updates member status to "Admin"
   ✅ Can now execute admin commands
   ✅ Appears in action logs
```

---

## Key UI Principles

✅ **Real-Time**: Everything updates instantly (no refresh)
✅ **Responsive**: Works on desktop, tablet, mobile
✅ **Intuitive**: Easy to find and click actions
✅ **Feedback**: Toasts and spinners show progress
✅ **Safe**: Confirmation dialogs for dangerous actions
✅ **Fast**: API calls optimized, caching on frontend
✅ **Accessible**: Keyboard navigation, high contrast
✅ **Visual**: Icons and colors for quick scanning

---

## Summary

The web dashboard provides complete control equal to bot commands:
- View all groups and members
- Take actions with one click
- See real-time updates instantly
- Never need to refresh page
- Track all changes in audit logs
- Full audit trail for compliance

Plus all data is automatically saved to database and synchronized across all clients!

