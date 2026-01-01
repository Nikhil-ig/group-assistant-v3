"""
Lightweight debug runner for Telegram bot polling only.

This script bypasses the FastAPI server and starts the telegram `Application`
in polling mode so you can quickly verify handlers are registered and the
bot is able to receive commands. It is intentionally defensive to work
with multiple python-telegram-bot versions.

Usage:
  cd v3
  python debug_run_bot.py

Note: This will require your `.env` to contain a valid TELEGRAM_BOT_TOKEN.
"""

import logging
import asyncio
import os
import sys

from dotenv import load_dotenv

HERE = os.path.dirname(__file__)
load_dotenv(os.path.join(HERE, ".env"))

from config.settings import config

# Import register_handlers (this registers command handlers on the app).
# Attempt package import first (when running as module), then fall back to
# adjusting sys.path so script can be run directly from the `v3` folder.
register_handlers = None
# Ensure the package parent dir is on sys.path so `v3` can be imported when
# running this script directly from the `v3/` folder.
parent = os.path.dirname(HERE)
if parent not in sys.path:
    sys.path.insert(0, parent)

try:
    # Preferred import path for package-aware execution: import the v3 package
    # This ensures relative imports inside handlers (e.g. `from ..config.settings`) work.
    import importlib
    try:
        mod = importlib.import_module("v3.bot.handlers")
        register_handlers = getattr(mod, "register_handlers")
        logging.getLogger(__name__).info("Imported register_handlers via v3.bot.handlers")
    except Exception:
        # Fallback to trying to import bare 'bot.handlers' if package layout is different
        mod = importlib.import_module("bot.handlers")
        register_handlers = getattr(mod, "register_handlers")
        logging.getLogger(__name__).info("Imported register_handlers via bot.handlers fallback")
except Exception:
    try:
        # Final fallback: attempt direct import by manipulating sys.path so the
        # `v3` directory itself is importable as a top-level package name.
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        mod = importlib.import_module("bot.handlers")
        register_handlers = getattr(mod, "register_handlers")
        logging.getLogger(__name__).info("Imported register_handlers via direct bot.handlers import")
    except Exception as e:  # pragma: no cover - best-effort import
        register_handlers = None
        logging.getLogger(__name__).warning(f"Could not import register_handlers: {e}")


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.DEBUG),
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()],
    )


def main():
    setup_logging()
    logger = logging.getLogger("debug_run_bot")

    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env - cannot start bot")
        sys.exit(1)

    # Import telegram Application lazily to provide a clearer error message
    try:
        from telegram.ext import Application
    except Exception as e:
        logger.error("python-telegram-bot not installed or failed to import: %s", e)
        sys.exit(1)

    # Build application
    try:
        app = Application.builder().token(token).build()
        logger.info("✅ Telegram Application built: %s", type(app))
    except Exception as e:
        logger.exception("Failed to build Telegram Application: %s", e)
        sys.exit(1)

    # Register handlers if available
    try:
        if register_handlers:
            # Defer DatabaseService creation until the Application event loop
            # is running. Creating motor clients before the app's loop can bind
            # them to a closed loop and later cause "Event loop is closed".
            # We schedule a one-time deferred DB init in `bot/handlers.register_handlers`
            # which will create the AsyncIOMotorClient inside the running loop.
            db_service = None
            logger.info("⚙️ Skipping synchronous DatabaseService init in debug runner; deferred init will run inside Application loop")

            # register_handlers expects (application, db_service)
            register_handlers(app, db_service)
            logger.info("✅ Handlers registered (debug_run_bot)")
        else:
            logger.warning("register_handlers not available; no handlers registered")
    except Exception as e:
        logger.exception("Error while registering handlers: %s", e)

    # Start polling. Try the modern API first, then fallback to older style.
    try:
        logger.info("🔁 Starting polling using app.run_polling()...")
        # Ensure an asyncio event loop is set for libraries that call get_event_loop()
        try:
            import asyncio as _asyncio
            try:
                _asyncio.get_running_loop()
            except RuntimeError:
                loop = _asyncio.new_event_loop()
                _asyncio.set_event_loop(loop)
        except Exception:
            # best-effort; if this fails we'll let app.run_polling handle event loop creation
            pass

        # In PTB v20+ this is a blocking convenience method
        app.run_polling()
    except AttributeError:
        # Older versions may not have run_polling; start with initialize/updater
        logger.info("Fallback: using async initialize + updater start")

        async def _run():
            try:
                await app.initialize()
                # Some versions expose updater
                if hasattr(app, "updater") and app.updater:
                    await app.updater.initialize()
                    await app.updater.start_polling()
                    logger.info("✅ Updater polling started (fallback)")

                # Keep running until interrupted
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
            except Exception as e:
                logger.exception("Polling error: %s", e)

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received; shutting down")


if __name__ == "__main__":
    main()
