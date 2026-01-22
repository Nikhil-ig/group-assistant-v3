# 🎨 /FREE Command - Visual Guide & Feature Map

## 📱 User Interface

### Menu Display

```
╔════════════════════════════════════════════╗
║ 🔓 ADVANCED CONTENT & BEHAVIOR MANAGER     ║
╚════════════════════════════════════════════╝

👤 Target User: @username (123456789)
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
  🌊 Floods: ✅ Enabled (Auto-delete spam)
  📨 Spam: ❌ Disabled (Detect links/mentions)
  ✅ Checks: ✅ Enabled (Verify members)
  🌙 Silence: ❌ Disabled (Night mode)

🌃 NIGHT MODE: ⭕ Inactive

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 QUICK GUIDE:
Content: Click to toggle what user can send
Filters: Click to enable/disable auto-actions
Reset: Restore default permissions
Close: Dismiss this menu

Updates saved to database in real-time
```

---

## 🎛️ Button Layout

### Grid Format

```
┌──────────────────┬──────────────────┐
│                                      │
│  ╔ 📋 CONTENT PERMISSIONS           │
│                                      │
│  ┌──────────────┬──────────────┐    │
│  │📝 Text ✅   │🎨 Stickers ❌│    │
│  ├──────────────┼──────────────┤    │
│  │🎬 GIFs ✅   │📸 Media ❌   │    │
│  ├──────────────┼──────────────┤    │
│  │🎤 Voice ✅  │🔗 Links ✅   │    │
│  └──────────────┴──────────────┘    │
│                                      │
│  ╠ 🚨 BEHAVIOR FILTERS              │
│                                      │
│  ┌──────────────┬──────────────┐    │
│  │🌊 Floods ✅ │📨 Spam ❌    │    │
│  ├──────────────┼──────────────┤    │
│  │✅ Checks ✅ │🌙 Silence ❌ │    │
│  └──────────────┴──────────────┘    │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 🌃 Night Mode ⭕ Inactive    │   │
│  └──────────────────────────────┘   │
│                                      │
│  ╠ 🎛️ ACTIONS                       │
│  ┌──────────────┬──────────────┐    │
│  │↻ Reset All   │❌ Close      │    │
│  └──────────────┴──────────────┘    │
│                                      │
└──────────────────────────────────────┘
```

---

## 📊 Feature Matrix

### Content Types (Per-User)

```
┌─────────────┬────────────────┬─────────────────┬──────────────┐
│ Content     │ API Field      │ Default State   │ Auto-Delete  │
├─────────────┼────────────────┼─────────────────┼──────────────┤
│ 📝 Text     │ can_send_msgs  │ ✅ Allowed     │ ❌ No        │
│ 🎨 Stickers │ can_send_other │ ✅ Allowed     │ ✅ Yes       │
│ 🎬 GIFs     │ can_send_other │ ✅ Allowed     │ ✅ Yes       │
│ 📸 Media    │ can_send_media │ ✅ Allowed     │ ✅ Yes       │
│ 🎤 Voice    │ can_send_audio │ ✅ Allowed     │ ✅ Yes       │
│ 🔗 Links    │ can_add_links  │ ✅ Allowed     │ ❌ No        │
└─────────────┴────────────────┴─────────────────┴──────────────┘
```

### Media Types (Cascading with 📸 Media)

```
📸 Media → Includes:
  ├─ 📷 Photos
  ├─ 🎥 Videos
  ├─ 📄 Documents
  ├─ 🎵 Audio Files
  ├─ 🎤 Voice Notes (separate control)
  └─ 📹 Video Notes (separate control)
```

### Behavior Filters (Group-Level)

```
┌──────────────┬─────────────────────┬──────────────┬───────────────┐
│ Filter       │ Detects             │ Threshold    │ Action        │
├──────────────┼─────────────────────┼──────────────┼───────────────┤
│ 🌊 Floods    │ Rapid messages      │ >4 msgs/5s   │ Auto-delete   │
│ 📨 Spam      │ Links/mentions      │ 3+ per msg   │ Auto-delete   │
│ ✅ Checks    │ New members         │ All users    │ CAPTCHA       │
│ 🌙 Silence   │ Night mode hours    │ Schedule     │ Auto-delete   │
└──────────────┴─────────────────────┴──────────────┴───────────────┘
```

---

## 🔄 State Transitions

### Permission Toggle Flow

```
Current State: ✅ ALLOWED (can_send = True)
         ↓
User clicks button
         ↓
API call: toggle-permission
         ↓
Database updated
         ↓
New State: ❌ BLOCKED (can_send = False)
         ↓
Bot sends: "✅ Stickers toggled"
```

### Media Detection & Delete Flow

```
User sends message
         ↓
Is it media? (sticker/GIF/photo/video/voice/etc)
         ↓ Yes
Get user permissions from API
         ↓
Is restricted? (can_send_X = False)
         ↓ Yes
Delete message
         ↓
Log action: {user_id, media_type, reason}
         ↓ No
Allow message
```

---

## 🎯 Command Usage Paths

### Path 1: Direct User Specification

```
/free @john_spammer
         ↓
Bot loads user @john_spammer
         ↓
Shows menu with @john_spammer's current restrictions
         ↓
Admin clicks buttons to modify
```

### Path 2: User ID

```
/free 123456789
         ↓
Bot loads user 123456789
         ↓
Shows menu
         ↓
Admin modifies restrictions
```

### Path 3: Reply to Message

```
Admin: [Replies to John's message] /free
         ↓
Bot extracts John's user ID from reply
         ↓
Shows menu for John
         ↓
Admin modifies John's restrictions
```

---

## 🌙 Night Mode Integration

### Night Mode + /FREE Interaction

```
/nightmode (configure schedule)
    ↓
Night mode active from 10 PM - 6 AM
    ↓
Non-exempt users during night:
    - Can send: Text messages only
    - Auto-deleted: Stickers, GIFs, media, voice
    ↓
Exempt users during night:
    - Can send: Everything
    - Nothing auto-deleted
    ↓
/free @user → Click 🌃 Night Mode
    ↓
Toggle user exemption:
    - ⭐ Personally exempt
    - 🎖️ Exempt by role
    - ❌ No exemption
```

---

## 📈 Permission State Diagram

### User Permission Model

```
User → Restrictions (per user, per group):
    ├─ can_send_messages
    │   ├─ True: Can send text
    │   └─ False: ❌ Blocked
    ├─ can_send_other_messages
    │   ├─ True: Stickers/GIFs allowed
    │   └─ False: ❌ Blocked
    ├─ can_send_media_messages
    │   ├─ True: Photos/videos/docs allowed
    │   └─ False: ❌ Blocked
    ├─ can_send_audios
    │   ├─ True: Voice/audio allowed
    │   └─ False: ❌ Blocked
    ├─ can_send_voice_notes
    │   ├─ True: Voice notes allowed
    │   └─ False: ❌ Blocked
    └─ can_add_web_page_previews
        ├─ True: Links allowed
        └─ False: ❌ Blocked

Media Filter:
    User sends message with media
         ↓
    Check: can_send_media_messages?
         ↓ False
    DELETE → Log
```

---

## 🔐 Security Flow

### Admin Verification

```
User clicks button
    ↓
handle_free_callback() triggered
    ↓
Check: Is user admin?
    ↓ No
    └─ Return: "❌ Admin only"
    ↓ Yes
Check: Valid callback data?
    ↓ No
    └─ Return: "Invalid data"
    ↓ Yes
Execute toggle/filter operation
```

### Permission Enforcement

```
Media Filter on new message:
    1. Check: Is from bot?
        └─ Skip if yes
    2. Check: Is in group?
        └─ Skip if private
    3. Check: Is command?
        └─ Skip if command
    4. Detect media type
    5. Fetch permissions from API
    6. If restricted: Delete + Log
    7. If allowed: Continue
```

---

## 📊 Data Model

### User Restriction Document

```json
{
  "user_id": 123456789,
  "group_id": 987654321,
  "can_send_messages": true,           // 📝 Text
  "can_send_other_messages": false,    // 🎨 Stickers, 🎬 GIFs
  "can_send_media_messages": false,    // 📸 Photos/Videos/Docs
  "can_send_audios": true,             // 🎤 Voice/Audio
  "can_send_voice_notes": true,        // 🎤 Voice Notes
  "can_add_web_page_previews": true,   // 🔗 Links
  "restricted_at": "2026-01-18T21:22:00Z",
  "restricted_by": 111111111,
  "reason": "Spam restriction"
}
```

### Group Policy Document

```json
{
  "group_id": 987654321,
  "floods_enabled": true,
  "flood_threshold": 4,
  "flood_window": 5,
  "spam_enabled": true,
  "spam_threshold": 3,
  "checks_enabled": true,
  "checks_type": "captcha",
  "silence_enabled": false,
  "silence_type": "night_mode"
}
```

### Audit Log Entry

```json
{
  "group_id": 987654321,
  "user_id": 123456789,
  "action": "auto_delete",
  "media_type": "sticker",
  "reason": "Stickers restricted",
  "message_id": 555,
  "timestamp": "2026-01-18T21:22:30Z",
  "status": "success"
}
```

---

## 🎬 Interaction Timeline

### Scenario: Restrict Spammer's Media

```
T=0s    Admin: /free @spammer
        Bot: Loads @spammer's data
        Bot: Fetches permissions from API
        Bot: Displays menu

T=0.5s  Bot: Menu shown with:
        📸 Media: ✅ Allowed
        ... (other options)

T=2s    Admin: Clicks 📸 Media button
        Callback: free_toggle_media_{user_id}_{group_id}

T=2.5s  API: Toggle permission request received
        API: Updates database
        API: Returns success

T=3s    Bot: Receives API response
        Bot: Shows toast: "📸 Media toggled + auto-delete enabled ✅"

T=3.5s  @spammer sends sticker
        media_filter_handler checks permissions
        Finds: can_send_media_messages = false
        Deletes sticker silently
        Logs: {user_id: spammer, media_type: sticker, ...}
```

---

## 🎯 Icon Legend

```
✅ = Allowed / Enabled / Success
❌ = Blocked / Disabled / Not available
🔐 = Locked / Restricted
⭕ = Off / Inactive / Neutral
🌙 = Night mode / Scheduled / Special
⚠️ = Warning / Caution / Error
📋 = Content / Configuration / Settings
🚨 = Alert / Important / Behavior
🎛️ = Actions / Controls / Management
🌙 = Time-based / Schedule
📊 = Data / Statistics / Information
```

---

## 🚀 Performance Profile

### Operation Speeds

```
Menu Load:        ~500ms (2 API calls)
├─ GET permissions
└─ GET policies

Button Click:     ~1s (1 API call)
├─ Toggle permission
└─ Update database

Media Detection:  <10ms (local check)
├─ Detect sticker/GIF/photo/etc
└─ Check message type

Permission Check: ~200ms (1 API call)
├─ GET user permissions
└─ Evaluate restriction

Auto-Delete:      <100ms
├─ Delete message
└─ Log action
```

---

## 📡 API Call Diagram

### Permission Flow

```
Client (Bot)
    ↓
GET /api/v2/groups/{gid}/users/{uid}/permissions
    ↓
API Server
    ↓
MongoDB (fetch permissions)
    ↓
Return: {can_send_messages: true, ...}
    ↓
Bot: Display current state
```

### Toggle Flow

```
Admin clicks button
    ↓
Client (Bot)
    ↓
POST /api/v2/groups/{gid}/enforcement/toggle-permission
{user_id, permission_type}
    ↓
API Server
    ↓
MongoDB (update state)
    ↓
Return: {success: true, new_state: {...}}
    ↓
Bot: Show feedback
```

---

## 🎨 Visual Status Indicators

### Status Display Legend

```
✅ ALLOWED      = User can send this content type
❌ BLOCKED      = User cannot send, will be auto-deleted
✅ ENABLED      = Filter/feature is active
❌ DISABLED     = Filter/feature is inactive
🌙 ACTIVE       = Night mode is currently running
⭕ Inactive     = Night mode is off
🎖️ Exempt by role     = User's role exempts them
⭐ Personally exempt  = User individually exempted
🌙 ACTIVE + ⭕ Inactive = Night mode status display
```

---

## 🎓 User Education

### Quick Mental Model

```
Think of /free as a PERMISSION MANAGER:

Content Permissions = What users CAN send
├─ 📝 Text: Always allowed (toggle text)
├─ 🎨 Stickers: Can turn off
├─ 🎬 GIFs: Can turn off
├─ 📸 Media: Can turn off (blocks photos, videos, docs)
├─ 🎤 Voice: Can turn off
└─ 🔗 Links: Can turn off

Behavior Filters = What group DISALLOWS
├─ 🌊 Floods: Block spam message flood
├─ 📨 Spam: Block link/mention spam
├─ ✅ Checks: Require CAPTCHA
└─ 🌙 Silence: Night mode enforcement

Night Mode = Time-based automatic mode
├─ Activates at configured hours
├─ Auto-deletes non-text during hours
└─ Can exempt users/roles
```

---

**Visual Documentation Complete! 🎨**

Use this guide to understand the /free command's interface, data flow, and functionality at a glance.

---

*Last Updated: January 18, 2026*
