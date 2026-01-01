"""
V3 Telegram Moderation Bot Package

Guardian Bot - Complete Telegram group moderation system with admin dashboard.

Features:
- Role-based access control (SUPERADMIN, GROUP_ADMIN, USER)
- Real-time Telegram group moderation actions (ban, mute, kick, warn)
- REST API with JWT authentication
- MongoDB for persistent storage
- Admin dashboard for group management
"""

__version__ = "3.0.0"
__author__ = "Guardian Bot Team"

# Package exports
__all__ = [
    "main",
    "config",
    "api",
    "bot",
    "core",
    "services",
    "utils",
]
