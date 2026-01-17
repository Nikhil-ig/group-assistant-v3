# Callback Flow Visualization

## 1. Settings Callback Flow

```
User clicks toggle button in /settings message
                ↓
        Telegram receives callback
                ↓
    Bot's handle_callback() triggered
                ↓
    Check if data == "settings" or starts with "settings"
                ↓
    Route to handle_settings_callbacks()
                ↓
    ┌─────────────────────────────────────────┐
    │ handle_settings_callbacks()              │
    ├─────────────────────────────────────────┤
    │ 1. Fetch fresh settings from API        │
    │    GET /api/advanced/settings/{group_id}│
    │                                          │
    │ 2. Build UI with toggle buttons:        │
    │    For each feature in settings:        │
    │    ├─ Show feature name                 │
    │    ├─ Show current state (✅/❌)        │
    │    └─ Generate toggle button            │
    │       Data: "toggle_setting::feature"  │
    │                                          │
    │ 3. Add "Edit Template" buttons:        │
    │    Data: "edit_template::field"        │
    │                                          │
    │ 4. Add "Close" button                  │
    │    Data: "settings_close"               │
    │                                          │
    │ 5. Edit message with new keyboard      │
    │    message.edit_text(ui_text, keyboard)│
    │                                          │
    │ 6. Show notification                   │
    │    callback_query.answer("Settings...") │
    └─────────────────────────────────────────┘
                ↓
        Message updated on Telegram
                ↓
            User sees new UI
```

## 2. Toggle Setting Flow

```
User clicks toggle button (e.g., "Auto-delete Commands")
                ↓
        Telegram receives callback
        Data: "toggle_setting::auto_delete_commands"
                ↓
    Bot's handle_callback() triggered
                ↓
    Check if data starts with "toggle_setting::"
                ↓
    Route to handle_toggle_setting_callback()
                ↓
    ┌──────────────────────────────────────────┐
    │ handle_toggle_setting_callback()          │
    ├──────────────────────────────────────────┤
    │ 1. Parse callback data:                  │
    │    feature = "auto_delete_commands"      │
    │                                           │
    │ 2. Fetch current settings:               │
    │    GET /api/advanced/settings/{group_id} │
    │                                           │
    │ 3. Get current state of feature:         │
    │    enabled = settings[feature]           │
    │                                           │
    │ 4. Toggle the feature:                  │
    │    new_state = !enabled                  │
    │                                           │
    │ 5. Send toggle to API:                  │
    │    POST .../toggle-feature               │
    │    ?feature=auto_delete_commands         │
    │    &enabled=true|false                   │
    │                                           │
    │ 6. Invalidate cache:                    │
    │    invalidate_group_settings_cache()    │
    │                                           │
    │ 7. Refresh settings UI:                 │
    │    Call handle_settings_callbacks()      │
    │    (which fetches fresh data)           │
    │                                           │
    │ 8. Show success notification:            │
    │    callback_query.answer("✅ Toggled!")  │
    └──────────────────────────────────────────┘
                ↓
        Message updated with new toggle state
                ↓
            User sees ✅/❌ updated
```

## 3. Template Edit Flow

```
User clicks "Edit Welcome Template" button
                ↓
        Telegram receives callback
        Data: "edit_template::welcome_message"
                ↓
    Bot's handle_callback() triggered
                ↓
    Check if data starts with "edit_template::"
                ↓
    Route to handle_edit_template_callback()
                ↓
    ┌────────────────────────────────────────┐
    │ handle_edit_template_callback()         │
    ├────────────────────────────────────────┤
    │ 1. Parse callback data:                │
    │    field = "welcome_message"            │
    │                                         │
    │ 2. Store pending edit:                 │
    │    pending_template_edits[             │
    │      (chat_id, user_id)                │
    │    ] = field                            │
    │                                         │
    │ 3. Send prompt message:                │
    │    "📝 Send your custom welcome..."    │
    │    Variables: {group_name}, {username} │
    │                              {user_id} │
    │                                         │
    │ 4. Show button notification:            │
    │    callback_query.answer("...")         │
    │                                         │
    │ 5. Wait for admin to reply              │
    └────────────────────────────────────────┘
                ↓
        User sees prompt
                ↓
    User sends custom template message
    E.g., "Welcome to {group_name}! 👋"
                ↓
    Bot's pending_template_message_handler triggered
                ↓
    ┌────────────────────────────────────────┐
    │ pending_template_message_handler()      │
    ├────────────────────────────────────────┤
    │ 1. Check pending edits:                │
    │    Is (chat_id, user_id) in dict?      │
    │                                         │
    │ 2. Get field name:                    │
    │    field = pending_template_edits[...] │
    │                                         │
    │ 3. Save new template to API:           │
    │    POST .../update                      │
    │    {welcome_message: new_text}          │
    │                                         │
    │ 4. Confirm to user:                   │
    │    "✅ Template updated!"               │
    │                                         │
    │ 5. Show new template in /settings      │
    │                                         │
    │ 6. Clean up pending edits:             │
    │    delete pending_template_edits[...]  │
    └────────────────────────────────────────┘
                ↓
        Template saved in DB
                ↓
    Next user join/leave uses new template
```

## 4. Action Callback Flow (Ban Example)

```
User clicks "Ban" button in moderation UI
                ↓
        Telegram receives callback
        Data: "ban_123456_-1001234567890"
              └─────┬──────┘   └──────┬──────────┘
                action          group_id
                ↓ target_user_id
                ↓
    Bot's handle_callback() triggered
                ↓
    Parse callback data:
    ├─ action = "ban"
    ├─ target_user_id = 123456
    └─ group_id = -1001234567890
                ↓
    Check if action in allowed_actions list
                ↓
    ┌──────────────────────────────────────────┐
    │ Action Callback Handler                  │
    ├──────────────────────────────────────────┤
    │ 1. Permission Check:                     │
    │    check_is_admin(callback_user_id,      │
    │                   group_id)              │
    │    ├─ TRUE: Continue                     │
    │    └─ FALSE: Show "❌ Need admin" alert  │
    │             STOP                         │
    │                                          │
    │ 2. Create action data:                  │
    │    {                                     │
    │      action_type: "ban",                 │
    │      group_id: -1001234567890,           │
    │      user_id: 123456,                    │
    │      initiated_by: callback_user_id      │
    │    }                                     │
    │                                          │
    │ 3. Execute via API:                     │
    │    api_client.execute_action(action_data)│
    │    POST /api/actions/execute             │
    │                                          │
    │ 4. Check result:                        │
    │    ├─ Has error → Show error UI         │
    │    └─ Success → Show success UI          │
    │                                          │
    │ 5. Success Response:                    │
    │    ├─ Edit message with result          │
    │    ├─ Show: "🔨 ACTION COMPLETED"        │
    │    ├─ Display: User ID, Action, Status  │
    │    ├─ Generate new action buttons       │
    │    │  (Unban, Kick, Warn)               │
    │    └─ Log action to database            │
    │                                          │
    │ 6. Error Response:                      │
    │    ├─ Show alert: "❌ Ban failed!"       │
    │    ├─ Edit message: Error details       │
    │    ├─ Keep original buttons available   │
    │    └─ Log failure to database           │
    │                                          │
    │ 7. User feedback:                       │
    │    callback_query.answer(message)       │
    └──────────────────────────────────────────┘
                ↓
        Message updated with result
                ↓
            User sees action result
                ↓
        (Can click another action button)
```

## 5. Permission Check Flow

```
User clicks action button or runs command
                ↓
    Command handler called
                ↓
    Call check_is_admin(user_id, group_id)
                ↓
    ┌──────────────────────────────────────┐
    │ check_is_admin()                     │
    ├──────────────────────────────────────┤
    │ 1. Try Telegram API:                │
    │    bot.get_chat_member(group_id,    │
    │                        user_id)     │
    │    ├─ If status in [admin, creator] │
    │    │  → Return TRUE                 │
    │    └─ Else continue                 │
    │                                      │
    │ 2. Try Centralized API:             │
    │    GET /api/rbac/users/{user_id}/   │
    │        permissions                  │
    │    ├─ If has manage_group → TRUE    │
    │    └─ Else → FALSE                  │
    └──────────────────────────────────────┘
                ↓
        Return is_admin: bool
                ↓
    ┌─────────────────────────┐
    │ Is admin?               │
    ├──────────┬──────────────┤
    │   YES    │      NO      │
    ├──────────┼──────────────┤
    │ Continue │ Send error   │
    │execution │ message:     │
    │          │ "❌ Need     │
    │          │ admin"       │
    │          │ RETURN       │
    └──────────┴──────────────┘
```

## 6. Cache Behavior Flow

```
Command / Callback requests settings
                ↓
    Call api_client.get_group_settings(group_id)
                ↓
    ┌──────────────────────────────────────┐
    │ Check if in cache                    │
    ├──────────────────────────────────────┤
    │ Is (group_id, expires_at) in cache? │
    │ And expires_at > current_time?       │
    ├─────────────┬────────────────────────┤
    │    YES      │         NO             │
    ├─────────────┼────────────────────────┤
    │ Return from │ Fetch from API:        │
    │ cache       │ GET /api/advanced/     │
    │ <100ms      │ settings/{group_id}    │
    │             │                        │
    │             │ Store in cache:        │
    │             │ _settings_cache[id] =  │
    │             │ (data, expires_at)     │
    │             │                        │
    │             │ Return data            │
    │             │ 500-1000ms             │
    └─────────────┴────────────────────────┘
                ↓
        Return settings to caller
                ↓
    ┌──────────────────────────────┐
    │ After toggle_feature():      │
    │ 1. Save to API               │
    │ 2. Invalidate cache:         │
    │    delete _settings_cache[id]│
    │ 3. Next request fetches fresh│
    └──────────────────────────────┘
```

## 7. Error Handling Flow

```
Callback / Command execution
                ↓
    Wrap in try/except
                ↓
    ┌──────────────────────────┐
    │ Exception occurs?        │
    ├────────────┬─────────────┤
    │    YES     │     NO      │
    ├────────────┼─────────────┤
    │ Catch:     │ Continue    │
    │ - API err  │ normal flow │
    │ - DB err   │             │
    │ - Network  │             │
    │ - Parse    │             │
    │ - Timeout  │             │
    └────────────┴─────────────┘
            │
            ├─ Log error with context
            │
            ├─ Prepare error response:
            │  ├─ User-friendly message
            │  ├─ Keep UI usable
            │  └─ Show retry option
            │
            └─ Send to user:
               ├─ callback_query.answer(
               │    "Alert text",
               │    show_alert=True)
               │
               ├─ Edit message with error
               │
               └─ Log to database
```

## 8. Callback Data Formats Reference

```
Settings:
├─ "settings" → Open settings UI
├─ "toggle_setting::feature_name" → Toggle feature
├─ "edit_template::field_name" → Edit template
└─ "settings_close" → Close settings

Actions:
└─ "action_target_user_id_group_id"
   Examples:
   ├─ "ban_123456_-1001234567890"
   ├─ "kick_123456_-1001234567890"
   ├─ "mute_123456_-1001234567890"
   ├─ "unmute_123456_-1001234567890"
   ├─ "warn_123456_-1001234567890"
   ├─ "promote_123456_-1001234567890"
   ├─ "demote_123456_-1001234567890"
   ├─ "restrict_123456_-1001234567890"
   ├─ "unrestrict_123456_-1001234567890"
   ├─ "pin_message_id_-1001234567890"
   ├─ "unpin_message_id_-1001234567890"
   └─ "lockdown_group_id_-1001234567890"

Info-Only:
├─ "user_info_123456_-1001234567890" → User details
├─ "user_stats_123456_-1001234567890" → User stats
├─ "user_history_123456_-1001234567890" → User history
├─ "admin_info_123456_-1001234567890" → Admin details
└─ "user_back_123456_-1001234567890" → Back button
```

## 9. Response Message Templates

```
✅ SUCCESS:
╔═══════════════════════════════════╗
║ 🔨 ACTION COMPLETED               ║
╚═══════════════════════════════════╝

📌 User ID: <code>123456</code>
⚡ Action: <code>BAN</code>
✅ Status: <code>SUCCESS</code>
📍 Result: <i>User banned</i>

🚀 <b>Next Actions Available ↓</b>
[Action Buttons]

❌ ERROR:
⚠️ <b>ACTION FAILED</b>

<b>Action:</b> BAN
<b>User ID:</b> <code>123456</code>
<b>Error:</b> <code>User is admin</code>

Please check permissions or try again.

ℹ️ INFO:
📋 <b>USER INFORMATION - 123456</b>

<b>User ID:</b> <code>123456</code>
<b>Group ID:</b> <code>-1001234567890</code>
<b>Status:</b> <code>Active</code>

📊 <b>Detailed Statistics:</b>
• Warnings: 3
• Mutes: 2
• Kicks: 1

[Back Button]
```

---

## Summary

This visualization shows how callbacks flow through the system:

1. **User triggers callback** (clicks button)
2. **Bot receives callback_query**
3. **Route to appropriate handler** (settings, toggle, template, action)
4. **Execute logic** (permission check, API call, etc.)
5. **Handle result** (success or error)
6. **Update UI** (edit message with new content)
7. **Provide feedback** (alert notification)

All handlers follow this pattern ensuring consistency and maintainability.
