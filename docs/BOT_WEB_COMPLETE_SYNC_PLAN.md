# Complete Bot-Web Sync Implementation Guide

## 🎯 Architecture Overview

```
Telegram Bot                  Database (MongoDB)          Web Dashboard
   ↓                              ↓                            ↓
Group Created  ──→  Auto Create   Group Record   ←───  Admin Control
                                       ↓
Bot /ban       ──→  Auto Store   Ban Record     ←───  Web Ban Button
               
Bot /mute      ──→  Auto Store   Mute Record    ←───  Web Mute Button

Members Join   ──→  Auto Sync    Member Record  ←───  Web Member List

                    ↓↓↓ Real-Time Updates via WebSocket ↓↓↓
                    
Dashboard shows all actions INSTANTLY when bot executes command
Bot shows when admin uses web interface to ban/mute users
```

## 📊 Current Implementation Status

✅ **Completed:**
- API endpoints for groups, logs, bans
- Real-time WebSocket for moderation actions
- Frontend auto-loads groups
- Basic RBAC permission system

❌ **Missing:**
- Auto-create group when bot is added to group
- Auto-sync members when members join/leave
- Full CRUD control from web (create, update, delete)
- Bi-directional sync (web changes → bot notifications)
- Automatic data cleanup

---

## 🔧 Implementation Steps

### Phase 1: Auto-Create & Auto-Sync Groups (Week 1)

#### 1a. Add Group Creation Handler in Bot
**File**: `src/bot/main.py`

Handler for `my_chat_member` event (when bot is added to group):
```python
@dp.my_chat_member()
async def on_bot_added_to_group(update: types.ChatMemberUpdated, bot: Bot):
    """Triggered when bot is added to a group."""
    chat = update.chat
    new_member = update.new_chat_member
    
    if new_member.is_member:  # Bot was added
        # Auto-create group in DB
        await GroupSyncService.ensure_group_exists(
            bot=bot,
            group_id=chat.id,
            group_title=chat.title
        )
        
        # Auto-sync members
        await sync_group_members(bot, chat.id)
        
        # Send welcome message
        welcome_msg = (
            f"✅ Guardian Bot activated in {chat.title}\n"
            f"📊 Syncing {chat.member_count} members...\n"
            f"🌐 Open dashboard: http://localhost:5173"
        )
        await bot.send_message(chat.id, welcome_msg)
```

#### 1b. Auto-Sync Members When Added
**File**: `src/services/group_sync.py`

```python
async def sync_group_members(bot: Bot, group_id: int):
    """Fetch all members from Telegram and store in DB."""
    try:
        # Get all members from Telegram
        admins = await bot.get_chat_administrators(group_id)
        
        for admin in admins:
            user = admin.user
            # Store in DB
            await MemberModel.add_member(
                group_id=group_id,
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                is_admin=admin.is_member_owner or admin.can_be_edited,
                joined_at=datetime.utcnow()
            )
        
        # Update member count in group
        await GroupModel.update(group_id, {
            "member_count": len(admins),
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"✅ Synced {len(admins)} members for group {group_id}")
    except Exception as e:
        logger.error(f"❌ Failed to sync members: {e}")
```

---

### Phase 2: Real-Time Bot-Web Sync (Week 1-2)

#### 2a. Bot Action → Database → WebSocket
Already implemented! Every bot action:
1. Executes moderation (ban/mute/warn)
2. Stores in MongoDB
3. Publishes to Redis
4. WebSocket sends to frontend

#### 2b. Web Action → Telegram Bot
**File**: `src/web/endpoints.py`

```python
@router.post("/groups/{group_id}/ban", response_model=ActionResponse)
async def ban_user_from_web(
    group_id: int,
    request: BanRequest,
    user: TokenPayload = Depends(verify_api_token),
):
    """Ban user from web dashboard."""
    # 1. Verify permissions
    if not user.is_superadmin:
        await check_user_permission(group_id, user.user_id, "can_ban")
    
    # 2. Execute ban in Telegram
    bot = get_global_bot()
    await bot.ban_chat_member(group_id, request.user_id)
    
    # 3. Store in DB (automatically via perform_mod_action)
    await perform_mod_action(
        group_id=group_id,
        action_type="BAN",
        admin_id=user.user_id,
        target_user_id=request.user_id,
        reason=request.reason,
        bot=bot
    )
    
    return ActionResponse(success=True, message="User banned")
```

---

### Phase 3: Full Web Control (Week 2)

#### 3a. Member Management API
**File**: `src/web/endpoints.py` - Add endpoints:

```python
@router.post("/groups/{group_id}/members/{user_id}/promote")
async def promote_member(group_id: int, user_id: int, ...):
    """Promote member to admin in web."""
    # 1. Update Telegram (give admin rights)
    # 2. Store in DB
    # 3. Broadcast to web via WebSocket

@router.post("/groups/{group_id}/members/{user_id}/demote")
async def demote_member(group_id: int, user_id: int, ...):
    """Demote admin to member."""

@router.post("/groups/{group_id}/members/{user_id}/remove")
async def remove_member(group_id: int, user_id: int, ...):
    """Remove member from group."""

@router.get("/groups/{group_id}/members")
async def get_group_members(group_id: int, ...):
    """Get all members of group from DB."""
```

#### 3b. Group Settings API
```python
@router.post("/groups/{group_id}/settings")
async def update_group_settings(group_id: int, settings: GroupSettings):
    """Update group settings from web."""
    # Update auto_mod, warn_threshold, etc.
    await GroupModel.update(group_id, settings.dict())
    
    # Notify bot via Redis
    await redis.publish(
        f"group_settings_updated:{group_id}",
        json.dumps(settings.dict())
    )
```

---

### Phase 4: Admin Dashboard Features (Week 2-3)

#### 4a. Group Overview
```
[Your Groups]
├─ Group 1 (50 members, 3 admins, 5 banned)
├─ Group 2 (120 members, 2 admins, 12 banned)
└─ Group 3 (30 members, 1 admin, 2 banned)
```

#### 4b. Group Detail Page
```
Group: Test Group
Members: 50
├─ Admin Controls
│  ├─ Auto-Mod Settings
│  ├─ Warn Threshold
│  └─ Ban on Threshold Toggle
├─ Members List (searchable)
│  ├─ Promote/Demote buttons
│  ├─ Ban/Unban buttons
│  └─ Direct message option
├─ Action Logs (real-time)
│  └─ Filter by type/date
└─ Banned Users
   ├─ List with reasons
   └─ Unban buttons
```

#### 4c. Real-Time Notifications
```
When bot is used in Telegram:
✅ "User @john banned" (appears instantly)
⚡ "Muted @spam for 60 min"
🔔 "5 new members joined"

When web is used:
✅ Notification in Telegram chat
   "Admin @websadmin banned @user"
```

---

## 🗄️ Database Schema (MongoDB)

```javascript
// Groups Collection
{
  _id: ObjectId,
  group_id: -1001234567890,          // Telegram group ID (negative)
  title: "Test Group",
  description: "Group description",
  owner_id: 123456789,               // Telegram user ID (owner)
  admins: [
    {
      user_id: 987654321,
      username: "admin1",
      role: "OWNER",
      permissions: ["can_ban", "can_mute", "manage_admins"]
    }
  ],
  settings: {
    auto_mod_enabled: true,
    warn_threshold: 3,
    ban_on_threshold: true,
    welcome_enabled: true,
    rules_enabled: true
  },
  stats: {
    member_count: 50,
    banned_count: 3,
    muted_count: 2,
    total_actions: 145,
    total_warns: 23
  },
  created_at: ISODate("2025-01-01"),
  updated_at: ISODate("2025-01-19")
}

// Members Collection
{
  _id: ObjectId,
  group_id: -1001234567890,
  user_id: 123456789,
  username: "john_doe",
  first_name: "John",
  last_name: "Doe",
  is_admin: false,
  warn_count: 0,
  is_banned: false,
  ban_reason: null,
  is_muted: false,
  muted_until: null,
  joined_at: ISODate("2025-01-01"),
  left_at: null
}

// Audit Logs Collection
{
  _id: ObjectId,
  group_id: -1001234567890,
  action: "BAN",
  admin_id: 987654321,
  admin_username: "admin1",
  target_user_id: 123456789,
  target_username: "john_doe",
  reason: "Spam",
  source: "WEB" | "BOT",              // Which interface triggered it
  timestamp: ISODate("2025-01-19"),
  details: {
    duration: null,
    before_state: {},
    after_state: {}
  }
}
```

---

## 🌐 Frontend Pages to Add/Modify

### 1. **Groups Management** (`/groups`)
- List all your groups
- Quick stats (members, admins, bans)
- Create/Delete groups button
- Search & filter

### 2. **Group Detail** (`/groups/:id`)
- Members list (with inline promote/demote/ban)
- Group settings panel
- Real-time action log
- Banned users list

### 3. **Admin Dashboard** (`/dashboard`)
- Overview of all groups
- System statistics
- Recent actions across all groups
- Quick access to group settings

### 4. **Moderation Panel** (`/moderation`)
- Quick ban/mute interface
- Search members
- Apply to single group or all groups
- Bulk actions

### 5. **Settings** (`/settings`)
- Personal preferences
- Group-specific permissions
- Notification settings
- API keys (for integrations)

---

## ⚙️ API Endpoints Summary

```
GET    /api/v1/groups                    # List all groups
GET    /api/v1/groups/my                 # List user's groups
POST   /api/v1/groups                    # Create group
GET    /api/v1/groups/{id}               # Get group detail
PUT    /api/v1/groups/{id}               # Update group settings
DELETE /api/v1/groups/{id}               # Delete group

GET    /api/v1/groups/{id}/members       # List members
POST   /api/v1/groups/{id}/members       # Add member
PUT    /api/v1/groups/{id}/members/{uid} # Update member
DELETE /api/v1/groups/{id}/members/{uid} # Remove member

POST   /api/v1/groups/{id}/ban           # Ban user
POST   /api/v1/groups/{id}/unban         # Unban user
POST   /api/v1/groups/{id}/mute          # Mute user
POST   /api/v1/groups/{id}/unmute        # Unmute user
POST   /api/v1/groups/{id}/warn          # Warn user
POST   /api/v1/groups/{id}/promote       # Promote to admin
POST   /api/v1/groups/{id}/demote        # Demote from admin

GET    /api/v1/groups/{id}/logs          # Get action logs
GET    /api/v1/groups/{id}/bans          # Get banned users
GET    /api/v1/groups/{id}/analytics     # Get statistics

WS     /ws/mod_actions/{group_id}        # Real-time updates
```

---

## 📋 Implementation Checklist

- [ ] **Phase 1a**: Add `my_chat_member` handler in bot
- [ ] **Phase 1b**: Auto-sync members on group creation
- [ ] **Phase 2a**: Verify bot → web sync is working
- [ ] **Phase 2b**: Add web → bot action endpoints
- [ ] **Phase 3a**: Member management API
- [ ] **Phase 3b**: Group settings API
- [ ] **Phase 4a**: Update frontend group page
- [ ] **Phase 4b**: Update member list with controls
- [ ] **Phase 4c**: Add real-time notifications
- [ ] **Testing**: End-to-end testing

---

## 🚀 Quick Start Commands

```bash
# 1. Start all services
cd /Users/apple/Documents/Personal/startup/bots/telegram\ bot/python/main_bot_v2

# Terminal 1: Backend
cd src && python main.py

# Terminal 2: Frontend
npm run dev

# Terminal 3: MongoDB
mongosh localhost:27017

# 2. Test bot added to group
# In Telegram: Add @guardian_bot to a test group
# Check MongoDB: db.groups.find()  # Should see new group

# 3. Test web control
# Open: http://localhost:5173/read-real-data
# Should auto-load group
# Click group → See members
# Ban a member via web
# Check Telegram: Should show ban notification
```

