# 📊 Smart Stickers/GIFs Filter - Visual Guide

## Decision Tree

```
Message Received
│
├─ Is it a Sticker/GIF?
│  │
│  ├─ NO → Continue with other checks
│  │
│  └─ YES → Fetch user permissions
│     │
│     ├─ Stickers ON, GIFs ON
│     │  └─ ✅ ALLOW MESSAGE
│     │
│     ├─ Stickers OFF, GIFs ON
│     │  │
│     │  └─ Is it a Sticker?
│     │     ├─ YES → ❌ AUTO-DELETE
│     │     └─ NO (GIF) → ✅ ALLOW
│     │
│     ├─ Stickers ON, GIFs OFF
│     │  │
│     │  └─ Is it a GIF?
│     │     ├─ YES → ❌ AUTO-DELETE
│     │     └─ NO (Sticker) → ✅ ALLOW
│     │
│     └─ Stickers OFF, GIFs OFF
│        │
│        ├─ 🔒 APPLY FULL RESTRICTION
│        │  └─ Call Telegram API restrictChatMember
│        │
│        ├─ 🗄️ SAVE TO MONGODB
│        │  └─ Set can_send_other_messages: false
│        │
│        └─ ❌ AUTO-DELETE MESSAGE
```

## State Matrix

```
┌─────────────────────────────────────────────────────────────┐
│ Stickers Status │ GIFs Status │ Action                      │
├─────────────────────────────────────────────────────────────┤
│ ✅ ON           │ ✅ ON       │ ✅ Allow all                │
├─────────────────────────────────────────────────────────────┤
│ ❌ OFF          │ ✅ ON       │ ❌ Auto-delete stickers     │
│                 │             │    ✅ Allow GIFs            │
├─────────────────────────────────────────────────────────────┤
│ ✅ ON           │ ❌ OFF      │ ❌ Auto-delete GIFs         │
│                 │             │    ✅ Allow stickers        │
├─────────────────────────────────────────────────────────────┤
│ ❌ OFF          │ ❌ OFF      │ 🔒 Full restriction via API │
│                 │             │ ❌ Auto-delete everything   │
│                 │             │ 🗄️ Save to MongoDB         │
└─────────────────────────────────────────────────────────────┘
```

## Timeline: Mixed Restrictions (One ON, One OFF)

```
Timeline: User sends Sticker (Stickers OFF, GIFs ON)

T=0ms     User sends sticker message
          ↓
T=10ms    Bot receives message event
          ↓
T=15ms    Bot detects: is_sticker = True
          ↓
T=20ms    Bot calls API: GET /permissions
          ↓
T=120ms   Bot receives: stickers=False, gifs=True
          ↓
T=125ms   Bot checks: is_sticker AND not stickers_allowed
          ↓
T=130ms   Bot deletes message
          ↓
T=135ms   ❌ Message deleted from chat
          (User sees: "message was deleted" in Telegram)
```

## Timeline: Full Restriction (Both OFF)

```
Timeline: User sends GIF (Both Stickers & GIFs OFF)

T=0ms     User sends GIF message
          ↓
T=10ms    Bot receives message event
          ↓
T=15ms    Bot detects: is_gif = True
          ↓
T=20ms    Bot calls API: GET /permissions
          ↓
T=120ms   Bot receives: stickers=False, gifs=False
          ↓
T=125ms   Bot detects: both stickers AND gifs OFF
          ↓
T=130ms   Bot calls API: POST /enforce/restrict
          ├─ user_id: 501166051
          ├─ permission_type: send_other_messages
          └─ group_id: -1003447608920
          ↓
T=2100ms  API saves to MongoDB
          ├─ can_send_other_messages: false
          └─ updated_at: 2026-01-19T15:30:45
          ↓
T=2110ms  API calls Telegram API: restrictChatMember
          ├─ permissions: {can_send_other_messages: false}
          └─ user_id: 501166051
          ↓
T=4500ms  Telegram API responds OK
          ↓
T=4510ms  Bot deletes the GIF message
          ↓
T=4520ms  ✅ Restriction applied
          ✅ Message deleted
          🗄️ Saved to database
          
          (User now cannot send ANY stickers/GIFs on Telegram)
```

## Memory & Processing

### Per Message Check

```
┌─────────────────────────────────┐
│ Message Handler (handle_message)│
└──────────┬──────────────────────┘
           │
           ├─→ Check if sticker/GIF? [<5ms]
           │
           ├─→ Fetch permissions [100-150ms]
           │   └─ API call with 5s timeout
           │
           └─→ Decide action [<10ms]
               ├─ Auto-delete? [<50ms]
               │
               ├─ Restrict? [1-3s + DB write]
               │  ├─ API call to restrict
               │  ├─ MongoDB save
               │  └─ Delete message
               │
               └─ Allow? [0ms]

Total Time:
- Allow: ~150ms
- Auto-delete: ~160ms  
- Full restriction: ~3s
```

### Concurrent Messages

If 2 users send stickers/GIFs simultaneously:

```
User A sends Sticker (Stickers OFF)
│
├─ Check perms [async, 100-150ms]
│
└─ Auto-delete [if restricted, <50ms]

User B sends GIF (Both OFF)
│
├─ Check perms [async, 100-150ms]
│
├─ Call Restrict API [async, 1-3s]
│
└─ Auto-delete [after API responds]

Result:
Both happen concurrently
No blocking between users
```

## Code Flow Diagram

```
handle_message()
│
├─ Detect message type
│  └─ is_sticker, is_gif, etc
│
├─ Night mode check
│  ├─ GET /night-mode/check
│  └─ Delete if restricted
│
├─ TEXT CHECK
│  ├─ GET /is-restricted?type=text
│  └─ Delete if restricted
│
├─ STICKER/GIF CHECK ⭐ (NEW)
│  │
│  ├─ GET /permissions (full state)
│  │
│  ├─ Analyze state:
│  │  ├─ stickers_allowed
│  │  └─ gifs_allowed
│  │
│  ├─ Check message type:
│  │  ├─ is_sticker
│  │  └─ is_gif
│  │
│  ├─ Decision logic:
│  │  ├─ Both allowed?
│  │  │  └─ ✅ Continue (allow)
│  │  │
│  │  ├─ One allowed, one not?
│  │  │  └─ Check message type
│  │  │     ├─ Matches restricted?
│  │  │     │  └─ ❌ Auto-delete
│  │  │     └─ Doesn't match?
│  │  │        └─ ✅ Allow
│  │  │
│  │  └─ Both restricted?
│  │     ├─ POST /enforcement/restrict
│  │     │  └─ Call Telegram API
│  │     │
│  │     ├─ MongoDB saves state
│  │     │
│  │     └─ ❌ Auto-delete
│  │
│  └─ Return (exit if deleted)
│
├─ VOICE CHECK
│  ├─ GET /is-restricted?type=voice
│  └─ Delete if restricted
│
└─ Allow message ✅
```

## State Transitions

```
User Permissions Over Time:

Initial State:
┌──────────────┐
│ Both ON      │
└──────┬───────┘
       │ /free toggle stickers
       ↓
┌──────────────┐
│ Stickers OFF │  ← AUTO-DELETE TIER
│ GIFs ON      │    (mixed state)
└──────┬───────┘
       │ /free toggle gifs
       ↓
┌──────────────┐
│ Stickers OFF │  ← RESTRICTION TIER
│ GIFs OFF     │    (both off)
└──────┬───────┘
       │ Call Telegram API
       │ Save to MongoDB
       │
       ↓
┌──────────────────────────────────┐
│ User fully restricted on Telegram│
│ (cannot send stickers or GIFs)   │
└──────┬───────────────────────────┘
       │ /free toggle stickers (ON)
       ↓
┌──────────────┐
│ Stickers ON  │  ← AUTO-DELETE TIER again
│ GIFs OFF     │    (back to mixed)
└──────┬───────┘
       │ /free toggle gifs (ON)
       ↓
┌──────────────┐
│ Both ON      │  ← ALLOW TIER (full freedom)
└──────────────┘
```

## API Call Sequence

### Scenario: User sends GIF when Both Stickers & GIFs are OFF

```
Sequence Diagram:

Bot                API                MongoDB         Telegram
│                  │                  │               │
│ 1. Message       │                  │               │
│ Received         │                  │               │
├─→ GET /perms ────→                  │               │
│                  │ 2. Query DB ─────→               │
│                  │                  │ 3. Response   │
│                  │ ←─────────────────               │
│                  │ 4. Return perms  │               │
│ ←─ Response ─────│                  │               │
│                  │                  │               │
│ 5. Both OFF? YES │                  │               │
│                  │                  │               │
│ POST /restrict ──→                  │               │
│                  │ 6. Save to DB ───→               │
│                  │                  │ 7. Saved      │
│                  │                  │               │
│                  │ 8. Call Telegram ─────────────→  │
│                  │                  │ 9. restrictChatMember
│                  │                  │               │
│                  │                  │ 10. OK ←──────│
│                  │                  │               │
│                  │ 11. Response ←─────────────────  │
│ ←─ Response ─────│                  │               │
│                  │                  │               │
│ 12. Delete msg   │                  │               │
│                  │                  │               │
│ ✅ Restricted    │                  │               │
```

## Performance Comparison

```
Handling Sticker/GIF Messages

┌─────────────────┬──────────┬─────────┬─────────────┐
│ Scenario        │ Time     │ API     │ DB Calls    │
├─────────────────┼──────────┼─────────┼─────────────┤
│ Both ON         │ ~150ms   │ 1       │ 0           │
│ (allowed)       │          │ (fetch) │             │
├─────────────────┼──────────┼─────────┼─────────────┤
│ One OFF         │ ~160ms   │ 1       │ 0           │
│ (auto-delete)   │          │ (fetch) │             │
├─────────────────┼──────────┼─────────┼─────────────┤
│ Both OFF        │ ~2-3s    │ 2       │ 1           │
│ (restrict)      │          │ (fetch  │ (update     │
│                 │          │  +      │  perms)     │
│                 │          │ restrict│             │
├─────────────────┼──────────┼─────────┼─────────────┤
│ Error/Timeout   │ ~5150ms  │ 1       │ 0           │
│ (fall through)  │          │ (fetch) │ (timeout)   │
└─────────────────┴──────────┴─────────┴─────────────┘
```

## Logging Output Examples

### Successful Auto-Delete (Mixed)
```
📨 Message from user (user_id: 501166051)
📊 Stickers/GIFs state: stickers=False, gifs=True
⛔ User 501166051 sending STICKER but stickers RESTRICTED
❌ Auto-deleted sticker message from 501166051
```

### Successful Full Restriction (Both OFF)
```
📨 Message from user (user_id: 501166051)
📊 Stickers/GIFs state: stickers=False, gifs=False
🔒 User 501166051 BOTH stickers AND gifs restricted. Applying Telegram restriction.
✅ User 501166051 restricted via Telegram API (both stickers & gifs OFF)
❌ Auto-deleted message from 501166051
```

### Permission Check Failure (Fallthrough)
```
📨 Message from user (user_id: 501166051)
⚠️ Could not check sticker/GIF permissions: timeout
→ Continuing with next check (fail-open)
✅ Message allowed (permission check failed)
```

## Summary Table

```
┌──────────────────────────────────────────────────────────┐
│ Smart Stickers/GIFs Content Filter                      │
├──────────────────────────────────────────────────────────┤
│ Logic Tiers:                                             │
│  1. Both ON    → ✅ Allow                               │
│  2. Mixed     → ❌ Auto-delete (no API call)            │
│  3. Both OFF  → 🔒 Full restriction (API + DB)         │
├──────────────────────────────────────────────────────────┤
│ Performance:                                             │
│  Allow:        ~150ms  (1 API call)                     │
│  Auto-delete:  ~160ms  (1 API call)                     │
│  Restrict:     ~2-3s   (2 API calls + DB write)        │
├──────────────────────────────────────────────────────────┤
│ Enforcement:                                             │
│  Auto-delete:  Message-level (client-side)             │
│  Restrict:     User-level (Telegram API enforced)      │
├──────────────────────────────────────────────────────────┤
│ Persistence:                                             │
│  MongoDB:      Yes (when restricted)                   │
│  Telegram:     Yes (cached in user permissions)        │
└──────────────────────────────────────────────────────────┘
```
