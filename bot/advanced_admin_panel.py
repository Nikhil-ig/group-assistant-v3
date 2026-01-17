# Advanced Admin Toggle Management System
# Handles state toggles: mute↔unmute, ban↔unban, warn↔unwarn, nightmode ON/OFF, lockdown↔freedom

async def get_advanced_admin_panel(group_id: int, user_id: int, admin_id: int) -> dict:
    """
    Get comprehensive admin panel state with all toggle statuses.
    Returns beautiful formatted data for display.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get user stats and current restrictions
            resp = await client.get(
                f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/status",
                headers={"Authorization": f"Bearer {api_client.api_key}"},
                timeout=10
            )
            
            if resp.status_code == 200:
                return resp.json()
            return {"error": "Could not fetch admin panel data"}
    except Exception as e:
        logger.error(f"Error fetching admin panel: {e}")
        return {"error": str(e)}


async def toggle_action_state(group_id: int, user_id: int, action: str, admin_id: int) -> dict:
    """
    Smart toggle system:
    - mute ↔ unmute
    - ban ↔ unban
    - warn ↔ unwarn
    - lockdown ↔ freedom (unlock)
    - nightmode on ↔ nightmode off
    - restrict ↔ unrestrict
    
    Automatically detects current state and applies inverse action.
    """
    try:
        # Get current state
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check current action status
            resp = await client.get(
                f"{api_client.base_url}/api/v2/groups/{group_id}/users/{user_id}/actions",
                headers={"Authorization": f"Bearer {api_client.api_key}"},
                timeout=10
            )
            
            if resp.status_code == 200:
                actions = resp.json().get("active_actions", [])
                
                # Determine next action based on current state
                next_action = action
                if action == "mute" and "mute" in actions:
                    next_action = "unmute"
                elif action == "ban" and "ban" in actions:
                    next_action = "unban"
                elif action == "warn" and "warn" in actions:
                    next_action = "unwarn"
                elif action == "restrict" and "restrict" in actions:
                    next_action = "unrestrict"
                elif action == "lockdown":
                    next_action = "unlock" if "lockdown" in actions else "lockdown"
                
                # Execute the action
                result = await api_client.execute_action({
                    "action_type": next_action,
                    "group_id": group_id,
                    "user_id": user_id,
                    "initiated_by": admin_id
                })
                
                return {
                    "success": result.get("error") is None,
                    "action": next_action,
                    "message": result.get("message", "Action executed"),
                    "error": result.get("error")
                }
        
        return {"success": False, "error": "Could not determine current state"}
    
    except Exception as e:
        logger.error(f"Error toggling action: {e}")
        return {"success": False, "error": str(e)}


async def format_admin_panel_message(
    user_info: dict,
    user_id: int,
    group_id: int,
    admin_id: int
) -> str:
    """
    Format beautiful professional admin panel message with user mention.
    Shows all available toggles and current states.
    """
    
    # Get user information
    username = user_info.get("username", f"User {user_id}")
    first_name = user_info.get("first_name", "")
    user_mention = f"<a href=\"tg://user?id={user_id}\">👤 {first_name or username}</a>"
    
    # Get current action states
    actions = user_info.get("active_actions", [])
    
    # Format action states
    mute_status = "🔇 MUTED" if "mute" in actions else "🔊 UNMUTED"
    ban_status = "🔨 BANNED" if "ban" in actions else "✅ ACTIVE"
    warn_status = f"⚠️ WARNS: {user_info.get('warn_count', 0)}" if "warn" in actions else "⚠️ WARNS: 0"
    restrict_status = "🔒 RESTRICTED" if "restrict" in actions else "🔓 UNRESTRICTED"
    lockdown_status = "🔐 LOCKED" if "lockdown" in actions else "🔓 UNLOCKED"
    nightmode_status = "🌙 ON" if user_info.get("nightmode_exempt") else "🌙 OFF"
    
    message = (
        f"╔════════════════════════════════════════╗\n"
        f"║  🎯 <b>ADVANCED ADMIN PANEL</b>       ║\n"
        f"╚════════════════════════════════════════╝\n\n"
        f"<b>👤 Target User:</b>\n"
        f"{user_mention}\n"
        f"<code>ID: {user_id}</code>\n\n"
        
        f"<b>📊 Current State:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  {mute_status}\n"
        f"  {ban_status}\n"
        f"  {warn_status}\n"
        f"  {restrict_status}\n"
        f"  {lockdown_status}\n"
        f"  {nightmode_status}\n\n"
        
        f"<b>⚡ Quick Actions:</b>\n"
        f"Click buttons below to toggle actions\n"
        f"Buttons auto-detect current state and apply opposite action"
    )
    
    return message


async def build_advanced_toggle_keyboard(user_id: int, group_id: int) -> InlineKeyboardMarkup:
    """
    Build beautiful keyboard with all toggle buttons.
    Smart buttons that show next action they'll perform.
    """
    
    buttons = [
        # Row 1: Mute/Unmute & Ban/Unban
        [
            InlineKeyboardButton(
                text="🔇 Mute ↔ Unmute",
                callback_data=f"adv_toggle_mute_{user_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="🔨 Ban ↔ Unban",
                callback_data=f"adv_toggle_ban_{user_id}_{group_id}"
            ),
        ],
        # Row 2: Warn & Restrict/Unrestrict
        [
            InlineKeyboardButton(
                text="⚠️ Warn",
                callback_data=f"adv_toggle_warn_{user_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="🔒 Restrict ↔ Free",
                callback_data=f"adv_toggle_restrict_{user_id}_{group_id}"
            ),
        ],
        # Row 3: Lockdown & Night Mode
        [
            InlineKeyboardButton(
                text="🔐 Lockdown ↔ Freedom",
                callback_data=f"adv_toggle_lockdown_{user_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="🌙 Night Mode",
                callback_data=f"adv_toggle_nightmode_{user_id}_{group_id}"
            ),
        ],
        # Row 4: Promote/Demote
        [
            InlineKeyboardButton(
                text="⬆️ Promote",
                callback_data=f"adv_toggle_promote_{user_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="⬇️ Demote",
                callback_data=f"adv_toggle_demote_{user_id}_{group_id}"
            ),
        ],
        # Row 5: Refresh & Close
        [
            InlineKeyboardButton(
                text="🔄 Refresh",
                callback_data=f"adv_panel_refresh_{user_id}_{group_id}"
            ),
            InlineKeyboardButton(
                text="❌ Close",
                callback_data=f"adv_panel_close_{user_id}_{group_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

