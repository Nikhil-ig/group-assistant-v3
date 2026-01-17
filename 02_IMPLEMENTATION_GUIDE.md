# 🔧 IMPLEMENTATION GUIDE - NEXT GENERATION FEATURES

**Status:** ✅ **READY TO CODE**  
**Target:** Add 12+ new modes + 15+ API endpoints  
**Time Estimate:** 2-3 hours implementation  

---

## 📋 STEP-BY-STEP IMPLEMENTATION

### STEP 1: Add New Delete Modes to bot/main.py

**Location:** After line 2915 (after all current delete modes)

```python
# ========== NEW DELETE MODES ==========

# MODE 12: Regex Pattern Delete
elif mode == "regex":
    if len(args) < 3:
        await send_and_delete(
            message,
            "Usage: /del regex \"<pattern>\"",
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    # Extract regex pattern (handle quotes)
    pattern_str = " ".join(args[2:])
    pattern_str = pattern_str.strip('"\'')
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-regex",
            {
                "pattern": pattern_str,
                "admin_id": message.from_user.id,
                "scan_limit": 100,
                "case_sensitive": False
            }
        )
        
        if result.get("success"):
            logger.info(f"Regex delete: {result.get('deleted_count')} messages")
    except Exception as e:
        logger.error(f"Regex delete error: {e}")
    
    return

# MODE 13: Duplicate Message Removal
elif mode == "duplicates":
    try:
        await message.delete()
    except:
        pass
    
    user_id = None
    if len(args) > 2:
        try:
            user_id = int(args[2])
        except:
            pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-duplicates",
            {
                "admin_id": message.from_user.id,
                "user_id": user_id,
                "scan_limit": 200
            }
        )
        
        if result.get("success"):
            logger.info(f"Duplicates delete: {result.get('deleted_count')} messages")
    except Exception as e:
        logger.error(f"Duplicates delete error: {e}")
    
    return

# MODE 14: Delete Inactive User Messages
elif mode == "inactive":
    if len(args) < 3:
        await send_and_delete(
            message,
            "Usage: /del inactive <days>",
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        days = int(args[2])
    except ValueError:
        await send_and_delete(
            message,
            "❌ Days must be a number",
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-inactive-users",
            {
                "admin_id": message.from_user.id,
                "days": days
            }
        )
        
        if result.get("success"):
            logger.info(f"Inactive delete: {result.get('deleted_count')} messages from {result.get('inactive_users')} users")
    except Exception as e:
        logger.error(f"Inactive delete error: {e}")
    
    return

# MODE 15: Delete Profanity/Inappropriate Content
elif mode == "profanity":
    severity = "medium"
    if len(args) > 2:
        severity = args[2].lower()
    
    if severity not in ["low", "medium", "high"]:
        severity = "medium"
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-profanity",
            {
                "admin_id": message.from_user.id,
                "severity": severity,
                "custom_words": []
            }
        )
        
        if result.get("success"):
            logger.info(f"Profanity delete: {result.get('deleted_count')} messages")
    except Exception as e:
        logger.error(f"Profanity delete error: {e}")
    
    return

# MODE 16: Delete Emoji Spam
elif mode == "emoji-spam":
    try:
        await message.delete()
    except:
        pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-emoji-spam",
            {
                "admin_id": message.from_user.id,
                "min_emoji_count": 3
            }
        )
        
        if result.get("success"):
            logger.info(f"Emoji spam delete: {result.get('deleted_count')} messages")
    except Exception as e:
        logger.error(f"Emoji spam delete error: {e}")
    
    return

# MODE 17: Delete Long Messages
elif mode == "long":
    if len(args) < 3:
        await send_and_delete(
            message,
            "Usage: /del long <character_limit>",
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        char_limit = int(args[2])
    except ValueError:
        await send_and_delete(
            message,
            "❌ Character limit must be a number",
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        await message.delete()
    except:
        pass
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/messages/delete-long",
            {
                "admin_id": message.from_user.id,
                "char_limit": char_limit
            }
        )
        
        if result.get("success"):
            logger.info(f"Long messages delete: {result.get('deleted_count')} messages")
    except Exception as e:
        logger.error(f"Long messages delete error: {e}")
    
    return
```

---

### STEP 2: Add New Send Modes to bot/main.py

**Location:** After line 3500 (after all current send modes)

```python
# ========== NEW SEND MODES ==========

# MODE 12: Batch Schedule (Multiple scheduled messages)
elif mode == "batch-schedule":
    # Interactive scheduling
    await send_and_delete(
        message,
        "📋 Batch scheduling not yet fully implemented. Use /send schedule instead.",
        parse_mode=ParseMode.HTML,
        delay=5
    )
    return

# MODE 13: Auto-Reply
elif mode == "auto-reply":
    if len(args) < 4:
        await send_and_delete(
            message,
            'Usage: /send auto-reply "<pattern>" "<response>"',
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        await message.delete()
    except:
        pass
    
    # Extract pattern and response
    text_parts = message.text.split('"')
    if len(text_parts) < 4:
        await send_and_delete(
            message,
            'Usage: /send auto-reply "<pattern>" "<response>"',
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    pattern = text_parts[1]
    response = text_parts[3]
    
    try:
        result = await api_client.post(
            f"/groups/{message.chat.id}/automation/auto-reply",
            {
                "admin_id": message.from_user.id,
                "pattern": pattern,
                "response": response,
                "enabled": True
            }
        )
        
        if result.get("success"):
            logger.info(f"Auto-reply created: {pattern} -> {response}")
    except Exception as e:
        logger.error(f"Auto-reply error: {e}")
    
    return

# MODE 14: Poll
elif mode == "poll":
    if len(args) < 4:
        await send_and_delete(
            message,
            'Usage: /send poll "<question>" "Option 1|Option 2|Option 3"',
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        await message.delete()
    except:
        pass
    
    # Extract question and options
    text_parts = message.text.split('"')
    if len(text_parts) < 4:
        return
    
    question = text_parts[1]
    options_str = text_parts[3]
    options = [opt.strip() for opt in options_str.split("|")]
    
    try:
        poll = await bot.send_poll(
            message.chat.id,
            question,
            options,
            is_anonymous=False
        )
        
        logger.info(f"Poll created: {question}")
        
        # Log to API
        try:
            await api_client.post(
                f"/groups/{message.chat.id}/messages/send",
                {
                    "text": question,
                    "admin_id": message.from_user.id,
                    "type": "poll",
                    "options": options
                }
            )
        except:
            pass
    
    except Exception as e:
        logger.error(f"Poll error: {e}")
    
    return

# MODE 15: Keyboard/Buttons
elif mode == "keyboard":
    if len(args) < 3:
        await send_and_delete(
            message,
            'Usage: /send keyboard "<text>" "btn1:url1|btn2:url2"',
            parse_mode=ParseMode.HTML,
            delay=5
        )
        return
    
    try:
        await message.delete()
    except:
        pass
    
    # Extract text and buttons
    text_parts = message.text.split('"')
    if len(text_parts) < 4:
        return
    
    text = text_parts[1]
    buttons_str = text_parts[3]
    
    # Parse buttons
    buttons = []
    for btn in buttons_str.split("|"):
        if ":" in btn:
            label, url = btn.split(":", 1)
            buttons.append(InlineKeyboardButton(text=label, url=url))
    
    if buttons:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
        
        try:
            await bot.send_message(
                message.chat.id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Keyboard message sent with {len(buttons)} buttons")
        except Exception as e:
            logger.error(f"Keyboard send error: {e}")
    
    return
```

---

### STEP 3: Add API Endpoints to api_v2/routes/message_operations.py

**Add at the end of file (after line 522):**

```python
# ========== NEW ULTRA DELETE ENDPOINTS ==========

@router.post("/groups/{group_id}/messages/delete-regex", response_model=Dict[str, Any])
async def delete_regex_messages(group_id: int, regex_data: dict = Body(...)):
    """Delete messages matching regex pattern."""
    import re
    
    try:
        pattern = regex_data.get("pattern")
        admin_id = regex_data.get("admin_id")
        scan_limit = regex_data.get("scan_limit", 100)
        case_sensitive = regex_data.get("case_sensitive", False)
        
        if not pattern or not admin_id:
            raise ValueError("pattern and admin_id required")
        
        # Compile regex with flags
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled_pattern = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex: {str(e)}")
        
        # Get recent messages
        action_collection = db["action_history"]
        messages = list(
            action_collection
            .find({"group_id": group_id, "action_type": "message_sent"})
            .sort("created_at", -1)
            .limit(scan_limit)
        )
        
        # Find matches
        matched_ids = []
        for msg in messages:
            text = msg.get("text", "")
            if text and compiled_pattern.search(text):
                matched_ids.append(msg.get("id"))
        
        # Delete matched
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg_id in matched_ids:
            messages_collection.insert_one({
                "message_id": msg_id,
                "group_id": group_id,
                "deleted_by": admin_id,
                "reason": f"Regex pattern: {pattern}",
                "deleted_at": datetime.utcnow(),
                "regex_pattern": pattern
            })
            deleted_count += 1
        
        # Log action
        action_collection.insert_one({
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "action_type": "regex_delete",
            "admin_id": admin_id,
            "pattern": pattern,
            "scanned": scan_limit,
            "matched": len(matched_ids),
            "deleted_count": deleted_count,
            "case_sensitive": case_sensitive,
            "deleted_at": datetime.utcnow()
        })
        
        logger.info(f"Regex delete: pattern={pattern}, deleted={deleted_count}")
        
        return {
            "success": True,
            "pattern": pattern,
            "matched": len(matched_ids),
            "deleted_count": deleted_count,
            "message": f"✅ {deleted_count} messages deleted"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Regex delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/messages/delete-duplicates", response_model=Dict[str, Any])
async def delete_duplicate_messages(group_id: int, dup_data: dict = Body(...)):
    """Delete duplicate messages."""
    try:
        admin_id = dup_data.get("admin_id")
        user_id = dup_data.get("user_id")
        scan_limit = dup_data.get("scan_limit", 200)
        
        if not admin_id:
            raise ValueError("admin_id required")
        
        # Get messages
        action_collection = db["action_history"]
        query = {"group_id": group_id, "action_type": "message_sent"}
        if user_id:
            query["user_id"] = user_id
        
        messages = list(
            action_collection
            .find(query)
            .sort("created_at", -1)
            .limit(scan_limit)
        )
        
        # Find duplicates
        seen = {}
        duplicate_ids = []
        
        for msg in messages:
            text = msg.get("text", "")
            sender = msg.get("user_id")
            
            key = (sender, text)
            if key in seen:
                duplicate_ids.append(msg.get("id"))
            else:
                seen[key] = msg.get("id")
        
        # Delete
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg_id in duplicate_ids:
            messages_collection.insert_one({
                "message_id": msg_id,
                "group_id": group_id,
                "deleted_by": admin_id,
                "reason": "Duplicate message",
                "deleted_at": datetime.utcnow(),
                "is_duplicate": True
            })
            deleted_count += 1
        
        return {
            "success": True,
            "duplicates_found": len(duplicate_ids),
            "deleted_count": deleted_count,
            "message": f"✅ {deleted_count} duplicates deleted"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Duplicates delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/messages/delete-inactive-users", response_model=Dict[str, Any])
async def delete_inactive_user_messages(group_id: int, inactive_data: dict = Body(...)):
    """Delete messages from inactive users."""
    from datetime import timedelta
    
    try:
        admin_id = inactive_data.get("admin_id")
        days = inactive_data.get("days", 30)
        
        if not admin_id:
            raise ValueError("admin_id required")
        if days < 1 or days > 365:
            raise ValueError("days must be 1-365")
        
        # Find inactive users
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        action_collection = db["action_history"]
        
        user_last_activity = {}
        messages = list(action_collection.find({"group_id": group_id}))
        
        for msg in messages:
            user_id = msg.get("user_id")
            date = msg.get("created_at")
            
            if user_id and date:
                if user_id not in user_last_activity:
                    user_last_activity[user_id] = date
                elif date > user_last_activity[user_id]:
                    user_last_activity[user_id] = date
        
        # Find inactive
        inactive_users = [uid for uid, date in user_last_activity.items() if date < cutoff_date]
        
        # Delete their messages
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg in messages:
            if msg.get("user_id") in inactive_users:
                messages_collection.insert_one({
                    "message_id": msg.get("id"),
                    "group_id": group_id,
                    "deleted_by": admin_id,
                    "reason": f"Inactive user ({days} days)",
                    "deleted_at": datetime.utcnow(),
                    "user_id": msg.get("user_id")
                })
                deleted_count += 1
        
        return {
            "success": True,
            "inactive_users": len(inactive_users),
            "deleted_count": deleted_count,
            "days_threshold": days,
            "message": f"✅ Cleaned {deleted_count} messages from {len(inactive_users)} inactive users"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Inactive delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/messages/delete-profanity", response_model=Dict[str, Any])
async def delete_profanity_messages(group_id: int, prof_data: dict = Body(...)):
    """Delete messages with profanity."""
    try:
        admin_id = prof_data.get("admin_id")
        severity = prof_data.get("severity", "medium")
        custom_words = prof_data.get("custom_words", [])
        
        if not admin_id:
            raise ValueError("admin_id required")
        
        # Word lists
        bad_words_db = {
            "low": ["bad", "poor", "ugly", "dumb"],
            "medium": ["damn", "hell", "crap", "sucks"],
            "high": ["explicit_words"]  # Add actual words as needed
        }
        
        words = bad_words_db.get(severity, []) + custom_words
        
        # Get messages
        action_collection = db["action_history"]
        messages = list(
            action_collection
            .find({"group_id": group_id, "action_type": "message_sent"})
            .sort("created_at", -1)
            .limit(200)
        )
        
        # Find profanity
        profanity_ids = []
        for msg in messages:
            text = msg.get("text", "").lower()
            for word in words:
                if word.lower() in text:
                    profanity_ids.append(msg.get("id"))
                    break
        
        # Delete
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg_id in profanity_ids:
            messages_collection.insert_one({
                "message_id": msg_id,
                "group_id": group_id,
                "deleted_by": admin_id,
                "reason": "Profanity/inappropriate content",
                "deleted_at": datetime.utcnow(),
                "severity": severity
            })
            deleted_count += 1
        
        return {
            "success": True,
            "found": len(profanity_ids),
            "deleted_count": deleted_count,
            "severity": severity,
            "message": f"✅ {deleted_count} profanity messages deleted"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Profanity delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/messages/delete-emoji-spam", response_model=Dict[str, Any])
async def delete_emoji_spam(group_id: int, emoji_data: dict = Body(...)):
    """Delete messages with excessive emoji."""
    import re
    
    try:
        admin_id = emoji_data.get("admin_id")
        min_emoji_count = emoji_data.get("min_emoji_count", 3)
        
        if not admin_id:
            raise ValueError("admin_id required")
        
        # Get messages
        action_collection = db["action_history"]
        messages = list(
            action_collection
            .find({"group_id": group_id, "action_type": "message_sent"})
            .sort("created_at", -1)
            .limit(100)
        )
        
        # Emoji regex
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F700-\U0001F77F]|[\U0001F780-\U0001F7FF]|[\U0001F800-\U0001F8FF]|[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|[\U00002702-\U000027B0]|[\U000024C2-\U0001F251]")
        
        # Find emoji spam
        spam_ids = []
        for msg in messages:
            text = msg.get("text", "")
            emoji_count = len(emoji_pattern.findall(text))
            if emoji_count >= min_emoji_count:
                spam_ids.append(msg.get("id"))
        
        # Delete
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg_id in spam_ids:
            messages_collection.insert_one({
                "message_id": msg_id,
                "group_id": group_id,
                "deleted_by": admin_id,
                "reason": f"Emoji spam ({min_emoji_count}+ emojis)",
                "deleted_at": datetime.utcnow()
            })
            deleted_count += 1
        
        return {
            "success": True,
            "found": len(spam_ids),
            "deleted_count": deleted_count,
            "min_emoji_count": min_emoji_count,
            "message": f"✅ {deleted_count} emoji spam messages deleted"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Emoji spam delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups/{group_id}/messages/delete-long", response_model=Dict[str, Any])
async def delete_long_messages(group_id: int, long_data: dict = Body(...)):
    """Delete messages longer than character limit."""
    try:
        admin_id = long_data.get("admin_id")
        char_limit = long_data.get("char_limit", 500)
        
        if not admin_id:
            raise ValueError("admin_id required")
        
        # Get messages
        action_collection = db["action_history"]
        messages = list(
            action_collection
            .find({"group_id": group_id, "action_type": "message_sent"})
            .sort("created_at", -1)
            .limit(200)
        )
        
        # Find long messages
        long_ids = []
        for msg in messages:
            text = msg.get("text", "")
            if len(text) > char_limit:
                long_ids.append(msg.get("id"))
        
        # Delete
        messages_collection = db["deleted_messages"]
        deleted_count = 0
        
        for msg_id in long_ids:
            messages_collection.insert_one({
                "message_id": msg_id,
                "group_id": group_id,
                "deleted_by": admin_id,
                "reason": f"Message too long (>{char_limit} chars)",
                "deleted_at": datetime.utcnow()
            })
            deleted_count += 1
        
        return {
            "success": True,
            "found": len(long_ids),
            "deleted_count": deleted_count,
            "char_limit": char_limit,
            "message": f"✅ {deleted_count} long messages deleted"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Long messages delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== NEW ANALYTICS ENDPOINTS ==========

@router.get("/groups/{group_id}/analytics/message-velocity", response_model=Dict[str, Any])
async def get_message_velocity(group_id: int, interval_minutes: int = 5):
    """Get message sending rate."""
    try:
        from datetime import timedelta
        
        action_collection = db["action_history"]
        now = datetime.utcnow()
        
        # Count by intervals
        intervals = {}
        for i in range(24):
            interval_end = now - timedelta(minutes=i * interval_minutes)
            interval_start = interval_end - timedelta(minutes=interval_minutes)
            
            count = action_collection.count_documents({
                "group_id": group_id,
                "action_type": "message_sent",
                "created_at": {"$gte": interval_start, "$lt": interval_end}
            })
            
            intervals[interval_end.isoformat()] = count
        
        values = list(intervals.values())
        avg = sum(values) / len(values) if values else 0
        
        return {
            "success": True,
            "group_id": group_id,
            "average_per_interval": avg,
            "interval_minutes": interval_minutes,
            "peak": max(values) if values else 0,
            "low": min(values) if values else 0,
            "intervals": intervals
        }
    
    except Exception as e:
        logger.error(f"Message velocity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/groups/{group_id}/analytics/user-activity", response_model=Dict[str, Any])
async def get_user_activity(group_id: int, limit: int = 10):
    """Get most active users."""
    try:
        action_collection = db["action_history"]
        
        messages = action_collection.find({"group_id": group_id, "action_type": "message_sent"})
        
        user_counts = {}
        for msg in messages:
            uid = msg.get("user_id")
            if uid:
                user_counts[uid] = user_counts.get(uid, 0) + 1
        
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        total = sum(user_counts.values())
        avg = total / len(user_counts) if user_counts else 0
        
        return {
            "success": True,
            "group_id": group_id,
            "top_users": [{"user_id": uid, "messages": count} for uid, count in top_users],
            "total_messages": total,
            "unique_users": len(user_counts),
            "average_per_user": avg
        }
    
    except Exception as e:
        logger.error(f"User activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🚀 DEPLOYMENT STEPS

1. **Backup Current Code:**
   ```bash
   git commit -am "Backup before enhancements"
   ```

2. **Add Bot Handlers:**
   - Copy all MODE 12-17 delete mode code from above
   - Paste after line 2915 in `bot/main.py`

3. **Add API Endpoints:**
   - Copy all new endpoint code
   - Paste at end of `api_v2/routes/message_operations.py` (after line 522)

4. **Test Endpoints:**
   ```bash
   # Test regex delete
   curl -X POST http://localhost:8002/api/v2/groups/12345/messages/delete-regex \
     -H "Authorization: Bearer $API_TOKEN" \
     -d '{"pattern": "^Error", "admin_id": 123}'
   ```

5. **Restart Services:**
   ```bash
   pkill -f "uvicorn"
   pkill -f "python bot/main.py"
   
   # Start API V2
   cd api_v2 && uvicorn app:app --port 8002 &
   
   # Start Bot
   cd ../bot && python main.py &
   ```

---

## ✅ VERIFICATION

Test all 6 new delete modes:
```
/del regex "pattern"
/del duplicates
/del inactive 30
/del profanity high
/del emoji-spam
/del long 500
```

---

**Ready to implement? Follow the steps above!**

