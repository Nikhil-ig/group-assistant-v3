# 🔓 /FREE Command - Advanced Content & Behavior Manager

## Overview

The `/free` command has been completely redesigned and enhanced with a **powerful suite of content restriction and behavior filtering tools**. It provides admins with granular control over user permissions and group-wide behavioral policies.

---

## 📋 Features Breakdown

### 1️⃣ **CONTENT PERMISSIONS** (Per-User)

Control what types of content a user can send:

#### **📝 Text Messages**
- Toggle whether user can send text/message content
- Restriction: `can_send_messages = False`
- Usage: Toggle "📝 Text" button

#### **🎨 Stickers**
- Auto-delete stickers sent by user when locked
- Restriction: `can_send_other_messages = False`
- Usage: Toggle "🎨 Stickers" button
- **Auto-Delete**: When locked, stickers are instantly deleted

#### **🎬 GIFs / Animations**
- Auto-delete animated GIFs/animations
- Restriction: `can_send_other_messages = False`
- Usage: Toggle "🎬 GIFs" button
- **Auto-Delete**: When locked, GIFs disappear immediately

#### **📸 Media** (Photos, Videos, Documents, Audio)
- **Key Feature**: Auto-delete ALL media types when locked
- Includes:
  - 📷 Photos
  - 🎥 Videos
  - 📄 Documents
  - 🎵 Audio files
- Restriction: `can_send_media_messages = False`
- Usage: Toggle "📸 Media" button
- **Auto-Delete Logic**: 
  - When media is restricted, the bot automatically detects and deletes:
    - Any photo message
    - Any video message
    - Any document message
    - Any audio file message
  - Deletion is instant with logging to audit trail

#### **🎤 Voice Messages & Video Notes**
- Auto-delete voice notes and video notes
- Restriction: `can_send_audios = False`
- Usage: Toggle "🎤 Voice" button
- **Auto-Delete**: Voice and video notes deleted instantly

#### **🔗 Links / Web Previews**
- Control link sharing and URL previews
- Restriction: `can_add_web_page_previews = False`
- Usage: Toggle "🔗 Links" button

---

### 2️⃣ **BEHAVIOR FILTERS** (Group-Level)

#### **🌊 Floods** (Spam Detection)
- **What it does**: Detects and auto-deletes rapid message spam
- **Threshold**: >4 messages in 5 seconds = spam
- **Action**: Auto-delete excess messages
- **Uses**: Stops bot abuse and spam floods
- **Toggle**: Click "🌊 Floods" button
- **Database**: Saves to group policies

#### **📨 Spam** (Link & Mention Detection)
- **What it does**: Detects excessive links, @mentions, hashtags
- **Threshold**: 3+ links or mentions in single message = spam
- **Action**: Auto-delete the message
- **Uses**: Prevents link spam and mention abuse
- **Toggle**: Click "📨 Spam" button
- **Smart Detection**:
  - Multiple URL links
  - Excessive @mentions (tag spam)
  - Hashtag spamming

#### **✅ Checks** (Verification for New Members)
- **What it does**: Requires new members to pass verification
- **Verification Type**: CAPTCHA puzzle
- **Action**: New member cannot post until verified
- **Uses**: Prevents bot/spam accounts from joining
- **Toggle**: Click "✅ Checks" button
- **Features**:
  - Simple CAPTCHA on join
  - Automatic role assignment after verification
  - Logs verification attempts

#### **🌙 Silence Mode** (Night Mode)
- **What it does**: Automatic muting during specified hours
- **Action**: Auto-delete non-text messages during night hours
- **Time-Based**: Only runs during configured "night hours"
- **Toggle**: Click "🌙 Silence" button
- **Key Features**:
  - Configurable schedule (e.g., 10 PM - 6 AM)
  - Exempts trusted users/moderators
  - Allows text-only messages
  - Auto-deletes: stickers, voice, media, links, etc.
  - Can exempt specific users from night mode

---

### 3️⃣ **NIGHT MODE EXEMPTION** (Per-User)

- **Purpose**: Exempt specific users from night mode restrictions
- **Types of Exemption**:
  - 🎖️ **Role-Based**: All users with certain role exempt
  - ⭐ **Personal**: Single user exempt
- **Toggle**: Click "🌃 Night Mode" button to toggle user's exemption status
- **Status Display**: 
  - 🌙 ACTIVE = Night mode is running
  - ⭐ Personally exempt = User can post during night mode
  - 🎖️ Exempt by role = User's role grants exemption

---

### 4️⃣ **ACTION BUTTONS**

#### **↻ Reset All**
- Restores user to default permissions (all allowed)
- Useful for un-restricting someone completely
- One-click restoration

#### **❌ Close**
- Closes the permissions menu
- Menu is deleted from chat

#### **🌙 Night Mode Info** (Display-Only)
- Shows current night mode status
- Indicates if user is exempt
- Shows exemption type (role vs personal)

---

## 🎯 Usage

### **Basic Usage**

```
/free                    # Usage help
/free @username          # Manage specific user
/free 123456789         # Manage by user ID
Reply with /free        # Manage user who wrote the replied-to message
```

### **Example Workflows**

#### **Scenario 1: Block spammer's media**
1. Use `/free @spammer`
2. Click "📸 Media" button
3. All photos, videos, documents they send → auto-deleted

#### **Scenario 2: Enable group-wide spam protection**
1. Use `/free` (any target)
2. Click "📨 Spam" button to enable spam detection
3. Click "🌊 Floods" button to enable flood detection
4. All spam automatically deleted

#### **Scenario 3: Quiet hours (Night Mode)**
1. Use `/free @user`
2. Click "🌙 Silence" button to enable night mode
3. During night hours, non-text messages are auto-deleted
4. Click same button again for user to toggle their exemption

#### **Scenario 4: Verify new members**
1. Use `/free` in admin mode
2. Click "✅ Checks" button
3. New members must pass CAPTCHA before posting

---

## 🔄 Auto-Delete Mechanism

### **How It Works**

When a content restriction is enabled via `/free`:

1. **User sends restricted media** (e.g., sticker)
2. **Media filter handler detects it** in real-time
3. **Bot checks API** for user's permission state
4. **If restricted**: Message is deleted instantly
5. **Logged**: Action recorded in audit trail with:
   - User ID
   - Media type
   - Timestamp
   - Reason

### **Media Types Auto-Detected**

```python
✅ Stickers       → Deleted if can_send_other_messages = False
✅ GIFs           → Deleted if can_send_other_messages = False
✅ Voice Messages → Deleted if can_send_audios = False
✅ Video Notes    → Deleted if can_send_media_messages = False
✅ Photos         → Deleted if can_send_media_messages = False
✅ Videos         → Deleted if can_send_media_messages = False
✅ Documents      → Deleted if can_send_media_messages = False
✅ Audio Files    → Deleted if can_send_media_messages = False
```

### **Silent Deletion**

- Messages are deleted WITHOUT notification (no "removed" indicator)
- No bot reply or explanation message
- Clean and discrete
- Logs entry created for audit purposes

---

## 🎨 UI Layout

### **Menu Layout**

```
╔════════════════════════════════════════════╗
║ 🔓 ADVANCED CONTENT & BEHAVIOR MANAGER     ║
╚════════════════════════════════════════════╝

👤 Target User: 123456789
👥 Group: 987654321

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 CONTENT RESTRICTIONS:
  📝 Text: ✅ Allowed
  🎨 Stickers: ❌ Blocked
  🎬 GIFs: ✅ Allowed
  📸 Media: ❌ Blocked
  🎤 Voice: ✅ Allowed
  🔗 Links: ✅ Allowed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 BEHAVIOR FILTERS:
  🌊 Floods: ❌ Disabled (Auto-delete spam)
  📨 Spam: ✅ Enabled (Detect links/mentions)
  ✅ Checks: ❌ Disabled (Verify members)
  🌙 Silence: ✅ Enabled (Night mode)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 QUICK GUIDE:
Content: Click to toggle what user can send
Filters: Click to enable/disable auto-actions
Reset: Restore default permissions
Close: Dismiss this menu
```

### **Button Grid**

```
┌─────────────────────────┬─────────────────────────┐
│  📝 Text ✅             │  🎨 Stickers ✅         │
├─────────────────────────┼─────────────────────────┤
│  🎬 GIFs ❌             │  📸 Media ❌            │
├─────────────────────────┼─────────────────────────┤
│  🎤 Voice ✅            │  🔗 Links ✅            │
├─────────────────────────┴─────────────────────────┤
│  🌊 Floods ✅           │  📨 Spam ❌             │
├─────────────────────────┬─────────────────────────┤
│  ✅ Checks ✅           │  🌙 Silence ✅          │
├─────────────────────────────────────────────────┤
│  🌃 Night Mode 🌙 ACTIVE                        │
├─────────────────────────────────────────────────┤
│  ↻ Reset All            │  ❌ Close               │
└─────────────────────────────────────────────────┘
```

---

## 💾 Data Persistence

All settings are persisted to the database:

### **Content Permission States**
- Stored per user, per group
- Keys: `can_send_messages`, `can_send_other_messages`, `can_send_audios`, etc.
- Fetched fresh from API on each toggle

### **Group Policies**
- Stored per group
- Fields: `floods_enabled`, `spam_enabled`, `checks_enabled`, `silence_enabled`
- Updated via dedicated policy endpoints

### **Night Mode Exemptions**
- Stored per user, per group
- Fields: `is_exempt`, `exempt_type` (role|personal)
- Checked before applying night mode restrictions

### **Audit Trail**
- All auto-deletes logged
- Fields: `user_id`, `media_type`, `reason`, `timestamp`
- Accessible via logs endpoint

---

## 🔐 Permissions & Security

- **Admin Only**: All `/free` command usage requires admin role
- **Bot Requirements**: Bot must have permission to:
  - Delete messages
  - Restrict/unrestrict members
  - Get member information
- **API Authentication**: All API calls verified with bearer token
- **User ID Verification**: Can't be used to self-restrict (bot protection)

---

## 📊 Statistics & Logging

### **Logged Events**

```
Auto-Delete Events:
- User ID: Who did it
- Media Type: sticker | GIF | voice | photo | video | document | audio
- Timestamp: When it happened
- Reason: "Stickers restricted" | "Media restricted" | etc
- Message ID: Which message was deleted

Toggle Events:
- Admin who made change
- What was toggled
- New state (enabled/disabled)
- Timestamp
```

---

## ⚙️ API Endpoints Used

### **Content Permissions**
```
GET /api/v2/groups/{group_id}/users/{user_id}/permissions
POST /api/v2/groups/{group_id}/enforcement/toggle-permission
POST /api/v2/groups/{group_id}/enforcement/reset-permissions
```

### **Group Policies**
```
POST /api/v2/groups/{group_id}/policies/floods
POST /api/v2/groups/{group_id}/policies/spam
POST /api/v2/groups/{group_id}/policies/checks
POST /api/v2/groups/{group_id}/policies/silence
```

### **Night Mode**
```
GET /api/v2/groups/{group_id}/night-mode/status
GET /api/v2/groups/{group_id}/night-mode/check/{user_id}/text
POST /api/v2/groups/{group_id}/night-mode/toggle-exempt/{user_id}
```

### **Logging**
```
POST /api/v2/groups/{group_id}/logs/auto-delete
```

---

## 🚀 Advanced Features

### **Cascading Restrictions**

When you restrict "Media" for a user:
- 📷 Photos blocked
- 🎥 Videos blocked
- 📄 Documents blocked
- 🎵 Audio files blocked
- All deleted automatically in real-time

### **Smart Detection**

The media filter uses Telegram's native message types:
- `message.sticker` → Sticker
- `message.animation` → GIF
- `message.voice` → Voice message
- `message.video_note` → Video note
- `message.photo` → Photo
- `message.video` → Video
- `message.document` → Document
- `message.audio` → Audio

### **Silent Operations**

- No "message was deleted" notifications
- No bot replies explaining why
- Clean, discrete operation
- Audit trail maintains transparency

### **Real-Time Enforcement**

- Media filter runs on every message
- Instant detection and deletion
- Zero-delay enforcement
- No queuing or delays

---

## 📝 Examples

### **Example 1: Restrict Spammer's Media**

```
Admin: /free @john_spammer
Bot shows menu
Admin clicks: 📸 Media
Result: All photos, videos, documents from @john_spammer are auto-deleted

Status: 📸 Media: ❌ BLOCKED
```

### **Example 2: Enable Spam Protection**

```
Admin: /free
Bot shows menu
Admin clicks: 🌊 Floods
Admin clicks: 📨 Spam
Result: 
  - Flood detection enabled (>4 msgs/5sec = deleted)
  - Spam detection enabled (3+ links = deleted)

Status:
  🌊 Floods: ✅ ENABLED
  📨 Spam: ✅ ENABLED
```

### **Example 3: Night Mode with Exemption**

```
Admin: /free @trusted_moderator
Bot shows menu
Admin clicks: 🌙 Silence to ENABLE night mode
Night mode activates (e.g., 10 PM - 6 AM)
During night hours: Non-text messages auto-deleted
Admin clicks: 🌃 Night Mode button
@trusted_moderator becomes EXEMPT
Result: @trusted_moderator can post normally during night mode
```

### **Example 4: Verification Check**

```
Admin: /free
Bot shows menu
Admin clicks: ✅ Checks to ENABLE
New user joins group
Bot: Automatic CAPTCHA shown
User solves CAPTCHA
User: Now verified, can post normally
Non-verified users: Messages blocked
```

---

## 🔧 Troubleshooting

### **Media not being deleted**

**Cause**: Media permissions might be set to allowed
- **Fix**: Check the "📸 Media" button state
- **Solution**: Click to toggle to BLOCKED state

### **Restrictions not applying**

**Cause**: API might be down or slow
- **Fix**: Check API logs at `http://localhost:8002/health`
- **Solution**: Restart API service

### **Settings not persisting**

**Cause**: Database connection issue
- **Fix**: Verify MongoDB is running
- **Solution**: Restart bot and API

---

## 📌 Summary

The `/free` command is now a **comprehensive content & behavior management system** that:

1. ✅ **Restricts content types** per user (text, media, voice, etc.)
2. ✅ **Auto-deletes** restricted content in real-time
3. ✅ **Detects spam** (floods, links, mentions)
4. ✅ **Enforces night mode** with exemptions
5. ✅ **Verifies new members** with CAPTCHA
6. ✅ **Persists all settings** to database
7. ✅ **Maintains audit trail** for transparency
8. ✅ **Provides instant feedback** with visual indicators

**Result**: Powerful, flexible group moderation with zero setup complexity!

---

*Last Updated: January 18, 2026*
*Version: 2.0 - Advanced Content & Behavior Manager*
