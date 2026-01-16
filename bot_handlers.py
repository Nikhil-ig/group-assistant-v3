"""
Telegram Bot Handler for Auto-Group Registration
Demonstrates how to use the auto-registration API with your Telegram bot

This handler automatically registers groups when:
1. Bot joins a new group
2. Bot receives messages from unknown groups
3. Bot is removed from a group
"""

import logging
import httpx
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8001/api"
AUTO_REGISTER_ENABLED = True
PERIODIC_STATS_UPDATE_ENABLED = True

# ============================================================================
# PYROGRAM INTEGRATION
# ============================================================================

async def ensure_group_registered_pyrogram(client, group_id: int):
    """
    Pyrogram: Ensure group is registered in database
    
    Usage:
        from pyrogram import Client
        from bot_handlers import ensure_group_registered_pyrogram
        
        @app.on_message(filters.group)
        async def on_group_message(client, message):
            await ensure_group_registered_pyrogram(client, message.chat.id)
    """
    if not AUTO_REGISTER_ENABLED:
        return
    
    try:
        # Get group info
        chat = await client.get_chat(group_id)
        
        # Get member count
        members_count = await client.get_chat_members_count(group_id)
        
        # Get admin count
        admin_count = 0
        async for member in client.get_chat_members(group_id, filter="administrators"):
            admin_count += 1
        
        # Call auto-registration API
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f'{API_BASE_URL}/groups/auto-register',
                json={
                    'group_id': group_id,
                    'group_name': chat.title,
                    'group_type': chat.type,
                    'member_count': members_count,
                    'admin_count': admin_count,
                    'description': chat.description or '',
                    'photo_url': str(chat.photo.big_file_id) if chat.photo else '',
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Group {chat.title}: {result['action']} (members: {members_count}, admins: {admin_count})")
            else:
                logger.warning(f"Failed to register group {group_id}: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error registering group {group_id}: {e}")


# Pyrogram: On bot join group
async def on_bot_join_pyrogram(client, message):
    """
    Pyrogram Handler: Called when bot joins a new group
    
    Usage:
        from pyrogram import filters
        
        @app.on_message(filters.status_update.new_chat_members)
        async def on_bot_join(client, message):
            # Check if bot was added
            for member in message.new_chat_members:
                if member.is_bot and member.is_self:
                    await on_bot_join_pyrogram(client, message)
                    break
    """
    try:
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        # Auto-register the group
        await ensure_group_registered_pyrogram(client, chat_id)
        
        # Send welcome message
        await message.reply(
            "👋 Hello! I've been added to this group.\n"
            "I'll help maintain order and manage moderation here."
        )
        
        logger.info(f"Bot joined group: {chat_title} ({chat_id})")
        
    except Exception as e:
        logger.error(f"Error in on_bot_join: {e}")


# Pyrogram: On bot removed from group
async def on_bot_removed_pyrogram(client, message):
    """
    Pyrogram Handler: Called when bot is removed from a group
    
    Usage:
        @app.on_message(filters.status_update.left_chat_members)
        async def on_bot_left(client, message):
            for member in message.left_chat_members:
                if member.is_self:
                    await on_bot_removed_pyrogram(client, message)
                    break
    """
    try:
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        # Deactivate group in database (if endpoint exists)
        # async with httpx.AsyncClient() as http:
        #     await http.put(f'{API_BASE_URL}/groups/{chat_id}/deactivate')
        
        logger.info(f"Bot removed from group: {chat_title} ({chat_id})")
        
    except Exception as e:
        logger.error(f"Error in on_bot_removed: {e}")


# ============================================================================
# PYTHON-TELEGRAM-BOT INTEGRATION
# ============================================================================

from telegram import Update
from telegram.ext import ContextTypes


async def ensure_group_registered_ptb(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Python-Telegram-Bot: Ensure group is registered
    
    Usage:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from bot_handlers import ensure_group_registered_ptb
        
        async def on_group_message(update, context):
            await ensure_group_registered_ptb(context, update.message.chat_id)
    """
    if not AUTO_REGISTER_ENABLED:
        return
    
    try:
        # Get group info
        chat = await context.bot.get_chat(chat_id)
        chat_members_count = await context.bot.get_chat_member_count(chat_id)
        
        # Count administrators
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_count = len(admins)
        
        # Call auto-registration API
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f'{API_BASE_URL}/groups/auto-register',
                json={
                    'group_id': chat_id,
                    'group_name': chat.title,
                    'group_type': chat.type,
                    'member_count': chat_members_count,
                    'admin_count': admin_count,
                    'description': chat.description or '',
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Group {chat.title}: {result['action']}")
            else:
                logger.warning(f"Failed to register group {chat_id}: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error registering group {chat_id}: {e}")


# PTB: On bot join group
async def on_bot_join_ptb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Python-Telegram-Bot Handler: Bot joined a group
    
    Usage:
        from telegram import filters
        
        app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            on_bot_join_ptb
        ))
    """
    if not update.message or not update.message.new_chat_members:
        return
    
    try:
        # Check if bot was the one added
        for member in update.message.new_chat_members:
            if member.is_bot and member.id == context.bot.id:
                # Auto-register the group
                await ensure_group_registered_ptb(context, update.message.chat_id)
                
                # Send welcome message
                await update.message.reply_text(
                    "👋 Hello! I've been added to this group.\n"
                    "I'll help maintain order and manage moderation here."
                )
                
                logger.info(f"Bot joined group: {update.message.chat.title}")
                break
                
    except Exception as e:
        logger.error(f"Error in on_bot_join: {e}")


# PTB: On bot removed from group
async def on_bot_removed_ptb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Python-Telegram-Bot Handler: Bot removed from group
    
    Usage:
        app.add_handler(MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBERS,
            on_bot_removed_ptb
        ))
    """
    if not update.message or not update.message.left_chat_member:
        return
    
    try:
        # Check if bot was the one removed
        if update.message.left_chat_member.id == context.bot.id:
            logger.info(f"Bot removed from group: {update.message.chat.title}")
            
    except Exception as e:
        logger.error(f"Error in on_bot_removed: {e}")


# PTB: For any group message
async def ensure_group_on_message_ptb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Python-Telegram-Bot Handler: Ensure group registered on any message
    
    Usage:
        app.add_handler(MessageHandler(
            filters.ChatType.GROUPS,
            ensure_group_on_message_ptb
        ))
    """
    if update.message and update.message.chat_id < 0:  # Group chat
        await ensure_group_registered_ptb(context, update.message.chat_id)


# ============================================================================
# PERIODIC STATS UPDATE
# ============================================================================

async def periodic_update_group_stats(context: ContextTypes.DEFAULT_TYPE, client=None):
    """
    Update statistics for all registered groups
    Call this periodically (e.g., every hour) to keep stats current
    
    For Python-Telegram-Bot:
        app.job_queue.run_repeating(
            periodic_update_group_stats,
            interval=3600,  # Every hour
            first=10
        )
    """
    if not PERIODIC_STATS_UPDATE_ENABLED:
        return
    
    try:
        logger.info("Starting periodic stats update...")
        
        # Get list of all active groups (would need to fetch from database)
        # For now, this is a placeholder
        
        # Example: Update a specific group
        # async with httpx.AsyncClient() as http:
        #     response = await http.put(
        #         f'{API_BASE_URL}/groups/update-stats/-100123456789',
        #         json={'member_count': 150, 'admin_count': 3}
        #     )
        
        logger.info("Periodic stats update complete")
        
    except Exception as e:
        logger.error(f"Error in periodic stats update: {e}")


# ============================================================================
# PTB SETUP EXAMPLE
# ============================================================================

def setup_bot_handlers(application):
    """
    Python-Telegram-Bot: Setup all group registration handlers
    
    Usage:
        from telegram.ext import Application
        
        def main():
            app = Application.builder().token("YOUR_BOT_TOKEN").build()
            setup_bot_handlers(app)
            app.run_polling()
        
        if __name__ == '__main__':
            main()
    """
    from telegram import filters
    from telegram.ext import MessageHandler, PicklePersistence
    
    # Handler: Bot joined group
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        on_bot_join_ptb
    ))
    
    # Handler: Bot removed from group
    application.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBERS,
        on_bot_removed_ptb
    ))
    
    # Handler: Any group message (auto-register backup)
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL,
        ensure_group_on_message_ptb
    ))
    
    # Job: Periodic stats update (every hour)
    if PERIODIC_STATS_UPDATE_ENABLED:
        application.job_queue.run_repeating(
            periodic_update_group_stats,
            interval=3600,
            first=10
        )
    
    logger.info("✅ Bot handlers configured for auto-group registration")


# ============================================================================
# BULK IMPORT FROM EXISTING GROUPS
# ============================================================================

async def bulk_register_groups(groups_data: list):
    """
    Bulk register multiple groups at once
    
    Useful when:
    - Bot is deployed to handle existing groups
    - Migrating data from another system
    - Initializing dashboard with known groups
    
    Usage:
        groups = [
            {'group_id': -1001234567890, 'group_name': 'Group 1', 'member_count': 100},
            {'group_id': -1001234567891, 'group_name': 'Group 2', 'member_count': 250},
        ]
        
        result = await bulk_register_groups(groups)
        print(result)
    """
    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f'{API_BASE_URL}/groups/bulk-register',
                json={'groups': groups_data},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Bulk registration: {result['created']} created, "
                    f"{result['updated']} updated, {result['failed']} failed"
                )
                return result
            else:
                logger.error(f"Bulk registration failed: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error in bulk registration: {e}")
        return None


# ============================================================================
# EXAMPLE: Using with python-telegram-bot
# ============================================================================

"""
COMPLETE EXAMPLE:

from telegram.ext import Application, JobQueue
from bot_handlers import setup_bot_handlers

def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    # Setup auto-registration handlers
    setup_bot_handlers(application)
    
    # Add your other handlers here...
    
    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
"""


# ============================================================================
# EXAMPLE: Using with Pyrogram
# ============================================================================

"""
COMPLETE EXAMPLE:

from pyrogram import Client, filters
from bot_handlers import on_bot_join_pyrogram, on_bot_removed_pyrogram

app = Client("my_bot", api_id=12345, api_hash="...")

@app.on_message(filters.status_update.new_chat_members)
async def on_bot_join(client, message):
    for member in message.new_chat_members:
        if member.is_bot and member.is_self:
            await on_bot_join_pyrogram(client, message)
            break

@app.on_message(filters.status_update.left_chat_members)
async def on_bot_left(client, message):
    for member in message.left_chat_members:
        if member.is_self:
            await on_bot_removed_pyrogram(client, message)
            break

app.run()
"""
