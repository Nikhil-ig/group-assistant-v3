"""
Authentication Service with JWT tokens and role-based authorization.

Handles:
- JWT token generation and validation
- User role verification
- Permission checking for actions
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging

from .database import DatabaseService, UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and authorization."""
    
    def __init__(self, db_service: DatabaseService, secret_key: str, expiration_hours: int = 24):
        """Initialize auth service.
        
        Args:
            db_service: Database service instance
            secret_key: JWT secret key
            expiration_hours: Token expiration time in hours
        """
        self.db = db_service
        self.secret_key = secret_key
        self.expiration_hours = expiration_hours
    
    def generate_token(
        self,
        user_id: int,
        username: str,
        first_name: str,
        role: UserRole,
        group_id: Optional[int] = None,
    ) -> str:
        """Generate JWT token for user.
        
        Args:
            user_id: Telegram user ID
            username: Username
            first_name: First name
            role: User role (SUPERADMIN, GROUP_ADMIN, USER)
            group_id: Group ID (for GROUP_ADMIN)
        
        Returns:
            JWT token string
        """
        try:
            now = datetime.now(timezone.utc)
            expiration = now + timedelta(hours=self.expiration_hours)
            
            payload = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "role": role.value,
                "group_id": group_id,
                "iat": now.timestamp(),
                "exp": expiration.timestamp(),
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            logger.info(f"✓ Token generated for {username} with role {role.value}")
            return token
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Token payload dict if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def authenticate_user(
        self,
        user_id: int,
        username: str,
        first_name: str,
        group_id: Optional[int] = None,
    ) -> Optional[str]:
        """Authenticate user and generate token.
        
        Automatically determines user's role:
        1. SUPERADMIN if configured
        2. GROUP_ADMIN if admin of group
        3. USER (default)
        
        Args:
            user_id: Telegram user ID
            username: Username
            first_name: First name
            group_id: Group ID (optional)
        
        Returns:
            JWT token if successful, None if failed
        """
        try:
            # Get user's role
            role = await self.db.get_user_role(user_id, group_id)
            
            # Generate token
            token = self.generate_token(user_id, username, first_name, role, group_id)
            return token
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def check_permission(
        self,
        user_id: int,
        action: str,
        group_id: Optional[int] = None,
    ) -> bool:
        """Check if user has permission to perform action.
        
        Args:
            user_id: User ID
            action: Action to perform (e.g., 'ban', 'view_logs')
            group_id: Group ID for group-specific actions
        
        Returns:
            True if user has permission, False otherwise
        """
        try:
            role = await self.db.get_user_role(user_id, group_id)
            
            # SUPERADMIN can do anything
            if role == UserRole.SUPERADMIN:
                return True
            
            # GROUP_ADMIN can perform actions in their group
            if role == UserRole.GROUP_ADMIN:
                if group_id:
                    is_admin = await self.db.is_group_admin(user_id, group_id)
                    return is_admin
                return False
            
            # USER can only view logs
            if action in ("view_logs", "view_metrics"):
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from database.
        
        Args:
            user_id: User ID
        
        Returns:
            User info dict or None
        """
        try:
            role = await self.db.get_user_role(user_id)
            return {
                "user_id": user_id,
                "role": role.value,
            }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
