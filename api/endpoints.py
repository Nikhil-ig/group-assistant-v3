"""
API Endpoints for V3 Bot with RBAC.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from pydantic import BaseModel, Field
import logging

from ..config.settings import config
from ..services.database import DatabaseService, UserRole, ActionType
from ..services.auth import AuthService
from ..services.telegram_api import TelegramAPIService

logger = logging.getLogger(__name__)


# ===== PYDANTIC MODELS =====

class LoginRequest(BaseModel):
    user_id: int = Field(..., description="Telegram user ID")
    username: str = Field(..., description="Telegram username")
    first_name: str = Field(..., description="User's first name")


class LoginResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    role: Optional[str] = None
    message: str


class ModActionRequest(BaseModel):
    action_type: str
    target_user_id: int
    target_username: Optional[str] = None
    reason: Optional[str] = None
    duration_hours: Optional[int] = None


class RestrictPermissionsRequest(BaseModel):
    target_user_id: int
    target_username: Optional[str] = None
    blocked_types: List[str] = Field(..., description="List of permission types to block")
    duration_hours: Optional[int] = None
    reason: Optional[str] = None


class ModActionResponse(BaseModel):
    ok: bool
    action_id: Optional[str] = None
    message: str
    timestamp: datetime


class AuditLogEntry(BaseModel):
    action_type: str
    admin_username: str
    target_username: Optional[str]
    reason: Optional[str]
    timestamp: datetime


class AuditLogsResponse(BaseModel):
    ok: bool
    group_id: int
    logs: List[AuditLogEntry]
    total_count: int
    page: int
    page_size: int


class MetricsResponse(BaseModel):
    ok: bool
    group_id: int
    total_actions: int
    actions_breakdown: dict = {}
    last_action_at: Optional[datetime] = None


class GroupInfo(BaseModel):
    group_id: int
    group_name: str
    created_at: datetime
    is_active: bool


class GroupsListResponse(BaseModel):
    ok: bool
    groups: List[GroupInfo]
    total_count: int


# ===== ROUTER SETUP =====

router = APIRouter(prefix=config.API_PREFIX, tags=["moderation"])


# ===== Additional models for members / blacklist =====


class MemberEntry(BaseModel):
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_bot: bool = False
    last_seen: Optional[datetime] = None


class MembersListResponse(BaseModel):
    ok: bool
    group_id: int
    members: List[MemberEntry]
    total_count: int
    page: int
    page_size: int


class BlacklistEntry(BaseModel):
    user_id: int
    username: Optional[str] = None
    reason: Optional[str] = None
    added_by: Optional[int] = None
    added_at: Optional[datetime] = None


class BlacklistResponse(BaseModel):
    ok: bool
    group_id: int
    entries: List[BlacklistEntry]
    total_count: int
    page: int
    page_size: int


# ===== NEW COMMAND MODELS (Free, ID, Settings, Promote, Demote) =====

class FreeRequest(BaseModel):
    group_id: int = Field(..., description="Group ID")
    target_user_id: int = Field(..., description="User ID to free")
    target_username: Optional[str] = None


class FreeResponse(BaseModel):
    ok: bool
    message: str
    action_id: Optional[str] = None


class UserIDRequest(BaseModel):
    group_id: int = Field(..., description="Group ID (optional, for context)")
    target_user_id: Optional[int] = None


class UserInfo(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool
    group_id: Optional[int] = None
    group_name: Optional[str] = None


class UserIDResponse(BaseModel):
    ok: bool
    user: Optional[UserInfo] = None
    message: str


class AdminInfo(BaseModel):
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    custom_title: Optional[str] = None


class GroupSettings(BaseModel):
    group_id: int
    group_name: str
    group_type: str  # "group", "supergroup", etc
    member_count: int
    admins: List[AdminInfo] = []
    description: Optional[str] = None


class SettingsResponse(BaseModel):
    ok: bool
    settings: Optional[GroupSettings] = None
    message: str


class PromoteRequest(BaseModel):
    group_id: int = Field(..., description="Group ID")
    target_user_id: int = Field(..., description="User ID to promote")
    target_username: Optional[str] = None
    custom_title: Optional[str] = Field(None, description="Max 16 characters")


class PromoteResponse(BaseModel):
    ok: bool
    message: str
    action_id: Optional[str] = None
    title_set: Optional[bool] = None


class DemoteRequest(BaseModel):
    group_id: int = Field(..., description="Group ID")
    target_user_id: int = Field(..., description="User ID to demote")
    target_username: Optional[str] = None


class DemoteResponse(BaseModel):
    ok: bool
    message: str
    action_id: Optional[str] = None


async def get_db_service(request: Request) -> DatabaseService:
    """Get database service instance from FastAPI app state (initialized at startup)."""
    svc = getattr(request.app.state, "db_service", None)
    if not svc:
        raise HTTPException(status_code=503, detail="Database service not available")
    return svc


async def get_auth_service(request: Request, db_service: DatabaseService = Depends(get_db_service)) -> AuthService:
    """Get auth service instance from FastAPI app state (initialized at startup)."""
    auth = getattr(request.app.state, "auth_service", None)
    if auth:
        return auth
    # Fallback: construct one from db_service
    return AuthService(db_service, config.JWT_SECRET)


async def get_telegram_api_service(request: Request) -> TelegramAPIService:
    """Get Telegram API service instance from FastAPI app state.
    
    Returns TelegramAPIService if telegram_app is available, otherwise returns a stub
    that logs actions without executing Telegram API calls (useful for API-only testing).
    """
    try:
        telegram_app = getattr(request.app.state, "telegram_app", None)
        if telegram_app and hasattr(telegram_app, "bot"):
            return TelegramAPIService(telegram_app.bot)
    except Exception as e:
        logger.debug(f"Could not create TelegramAPIService: {e}")
    
    # Return None - caller should handle gracefully
    return None


async def verify_token(
    authorization: str = Header(None),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Verify JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.replace("Bearer ", "")
    payload = auth_service.validate_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Normalize role value to UserRole enum so downstream RBAC checks work
    try:
        role_val = payload.get("role")
        if role_val and not isinstance(role_val, UserRole):
            # payload stores role as string (e.g. 'user'), convert to enum
            try:
                payload["role"] = UserRole(role_val)
            except Exception:
                # leave as-is if conversion fails
                pass
    except Exception:
        # Be defensive: don't fail token verification because of role parsing
        pass

    return payload


# ===== ENDPOINTS =====

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate user and get JWT token."""
    try:
        token = await auth_service.authenticate_user(
            user_id=request.user_id,
            username=request.username,
            first_name=request.first_name,
        )
        
        if not token:
            return LoginResponse(ok=False, message="Authentication failed")
        
        role = await auth_service.db.get_user_role(request.user_id)
        
        return LoginResponse(
            ok=True,
            token=token,
            role=role,
            message="Login successful",
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return LoginResponse(ok=False, message=f"Login failed: {str(e)}")


@router.get("/groups", response_model=GroupsListResponse)
async def get_groups(
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> GroupsListResponse:
    """Get groups for user: SUPERADMIN sees all, GROUP_ADMIN sees own."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        if role == UserRole.USER:
            return GroupsListResponse(ok=False, groups=[], total_count=0)
        
        groups = await db_service.get_groups_for_user(user_id)
        
        return GroupsListResponse(
            ok=True,
            groups=[
                GroupInfo(
                    group_id=g["group_id"],
                    group_name=g["group_name"],
                    created_at=g["created_at"],
                    is_active=g.get("is_active", True),
                )
                for g in groups
            ],
            total_count=len(groups),
        )
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return GroupsListResponse(ok=False, groups=[], total_count=0)


@router.post("/groups/{group_id}/actions", response_model=ModActionResponse)
async def execute_action(
    group_id: int,
    action: ModActionRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> ModActionResponse:
    """Execute moderation action with RBAC check and actual Telegram API call.
    
    Flow:
    1. Verify user is authorized (SUPERADMIN or GROUP_ADMIN for this group)
    2. Call Telegram API to execute action (ban, mute, kick, etc.)
    3. Log action to database (for audit trail)
    4. Update metrics
    
    Returns success only if both Telegram API and database operations succeed.
    """
    try:
        user_id = token_data.get("user_id")
        username = token_data.get("username")
        role = token_data.get("role")
        
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        action_type = action.action_type.upper()
        action_enum = ActionType[action_type]
        
        # Execute action on Telegram (if service available)
        telegram_success = True
        telegram_error = None
        
        if telegram_api:
            logger.info(
                f"📤 Executing {action_type} action for user {action.target_user_id} "
                f"in group {group_id} via Telegram API"
            )
            
            if action_type == "BAN":
                telegram_success, telegram_error = await telegram_api.ban_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                    reason=action.reason,
                )
            elif action_type == "UNBAN":
                telegram_success, telegram_error = await telegram_api.unban_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                )
            elif action_type == "KICK":
                telegram_success, telegram_error = await telegram_api.kick_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                    reason=action.reason,
                )
            elif action_type == "MUTE":
                telegram_success, telegram_error = await telegram_api.mute_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                    duration_hours=action.duration_hours,
                    reason=action.reason,
                )
            elif action_type == "UNMUTE":
                telegram_success, telegram_error = await telegram_api.unmute_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                    reason=action.reason,
                )
            elif action_type == "WARN":
                telegram_success, telegram_error = await telegram_api.warn_user(
                    group_id=group_id,
                    user_id=action.target_user_id,
                    reason=action.reason,
                    admin_name=username,
                )
            
            if not telegram_success:
                logger.error(
                    f"❌ Telegram API call failed for {action_type}: {telegram_error}"
                )
        else:
            logger.warning(
                f"⚠️ Telegram API service not available, logging action without execution"
            )
        
        # Log action to database (always, even if Telegram API fails)
        db_success = await db_service.log_action(
            group_id=group_id,
            action_type=action_enum,
            admin_id=user_id,
            admin_username=username,
            target_user_id=action.target_user_id,
            target_username=action.target_username,
            reason=action.reason,
            duration_hours=action.duration_hours,
        )
        
        # Update metrics only if database logging succeeded
        if db_success:
            await db_service.update_metrics(group_id, action_enum)
        
        # Overall success = both Telegram and DB success (or Telegram N/A)
        overall_success = (telegram_success or not telegram_api) and db_success
        
        return ModActionResponse(
            ok=overall_success,
            message=(
                "Success" if overall_success 
                else f"Failed: {telegram_error or 'Database error'}"
            ),
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Action execution failed")


@router.post("/groups/{group_id}/restrict", response_model=ModActionResponse)
async def restrict_user_permissions(
    group_id: int,
    restrict_request: RestrictPermissionsRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> ModActionResponse:
    """Restrict specific permissions for a user.
    
    Allows admins to selectively block specific content types (stickers, GIFs, media, etc.)
    while allowing other permissions.
    
    Blocked types:
    - media: All media (photos, videos, documents, audio, voice)
    - stickers: Stickers
    - gifs: GIFs/animations
    - polls: Polls
    - links: Web page previews
    - voice: Voice messages
    - video: Videos
    - audio: Audio files
    - documents: Documents
    - photos: Photos
    - all_messages: All messages
    """
    try:
        user_id = token_data.get("user_id")
        username = token_data.get("username")
        role = token_data.get("role")
        
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Validate blocked_types
        valid_types = {
            "media", "stickers", "gifs", "polls", "links", "voice", 
            "video", "audio", "documents", "photos", "all_messages"
        }
        for block_type in restrict_request.blocked_types:
            if block_type.lower() not in valid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid block type: {block_type}. Valid types: {', '.join(valid_types)}"
                )
        
        # Execute restriction on Telegram
        telegram_success = True
        telegram_error = None
        
        if telegram_api:
            logger.info(
                f"📤 Restricting user {restrict_request.target_user_id} in group {group_id} "
                f"- Blocked: {', '.join(restrict_request.blocked_types)}"
            )
            
            telegram_success, telegram_error = await telegram_api.restrict_user_permissions(
                group_id=group_id,
                user_id=restrict_request.target_user_id,
                blocked_types=restrict_request.blocked_types,
                duration_hours=restrict_request.duration_hours,
                reason=restrict_request.reason or f"Blocked by {username}: {', '.join(restrict_request.blocked_types)}",
            )
            
            if not telegram_success:
                logger.error(
                    f"❌ Telegram API call failed for restrict: {telegram_error}"
                )
        else:
            logger.warning(
                f"⚠️ Telegram API service not available, logging action without execution"
            )
        
        # Log action to database as MUTE action type (no specific RESTRICT type exists)
        db_success = await db_service.log_action(
            group_id=group_id,
            action_type=ActionType.MUTE,
            admin_id=user_id,
            admin_username=username,
            target_user_id=restrict_request.target_user_id,
            target_username=restrict_request.target_username,
            reason=f"Restrict: {', '.join(restrict_request.blocked_types)}" + 
                   (f" for {restrict_request.duration_hours}h" if restrict_request.duration_hours else ""),
            duration_hours=restrict_request.duration_hours,
        )
        
        # Update metrics only if database logging succeeded
        if db_success:
            await db_service.update_metrics(group_id, ActionType.MUTE)
        
        # Overall success = both Telegram and DB success (or Telegram N/A)
        overall_success = (telegram_success or not telegram_api) and db_success
        
        blocked_str = ", ".join(restrict_request.blocked_types)
        duration_str = f" for {restrict_request.duration_hours} hours" if restrict_request.duration_hours else " (permanent)"
        
        return ModActionResponse(
            ok=overall_success,
            message=(
                f"✅ User {restrict_request.target_user_id} restricted - Blocked: {blocked_str}{duration_str}" 
                if overall_success 
                else f"⚠️ Restriction logged but Telegram action failed: {telegram_error}"
            ),
            timestamp=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restricting user permissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Restriction failed")


@router.get("/groups/{group_id}/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    group_id: int,
    authorization: str = Header(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> AuditLogsResponse:
    """Get audit logs with RBAC: SUPERADMIN all groups, GROUP_ADMIN own only."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        skip = (page - 1) * page_size
        logs = await db_service.get_audit_logs(
            group_id=group_id,
            limit=page_size,
            skip=skip,
        )
        
        total_count = await db_service.get_audit_logs_count(group_id=group_id)
        
        return AuditLogsResponse(
            ok=True,
            group_id=group_id,
            logs=[
                AuditLogEntry(
                    action_type=log["action_type"],
                    admin_username=log["admin_username"],
                    target_username=log.get("target_username"),
                    reason=log.get("reason"),
                    timestamp=log["timestamp"],
                )
                for log in logs
            ],
            total_count=total_count,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


@router.get("/groups/{group_id}/metrics", response_model=MetricsResponse)
async def get_metrics(
    group_id: int,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> MetricsResponse:
    """Get metrics for group with RBAC: SUPERADMIN all, GROUP_ADMIN own only."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        metrics = await db_service.get_metrics(group_id)
        
        if not metrics:
            return MetricsResponse(
                ok=False,
                group_id=group_id,
                total_actions=0,
                actions_breakdown={},
                last_action_at=None,
            )
        
        return MetricsResponse(
            ok=True,
            group_id=group_id,
            total_actions=metrics.get("total_actions", 0),
            actions_breakdown=metrics.get("actions", {}),
            last_action_at=metrics.get("last_action"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/health")
async def health_check(db_service: DatabaseService = Depends(get_db_service)):
    """Health check endpoint."""
    try:
        is_healthy = await db_service.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/groups/{group_id}/members", response_model=MembersListResponse)
async def get_members(
    group_id: int,
    authorization: str = Header(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> MembersListResponse:
    """Return paginated members for a group (RBAC enforced)."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")

        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)

        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")

        skip = (page - 1) * page_size
        members = await db_service.get_members(group_id=group_id, limit=page_size, skip=skip)
        total = await db_service.db["members"].count_documents({"group_id": group_id})

        return MembersListResponse(
            ok=True,
            group_id=group_id,
            members=[
                MemberEntry(
                    user_id=m.get("user_id"),
                    username=m.get("username"),
                    first_name=m.get("first_name"),
                    is_bot=m.get("is_bot", False),
                    last_seen=m.get("last_seen"),
                )
                for m in members
            ],
            total_count=total,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting members: {e}")
        raise HTTPException(status_code=500, detail="Failed to get members")


@router.get("/groups/{group_id}/blacklist", response_model=BlacklistResponse)
async def get_blacklist(
    group_id: int,
    authorization: str = Header(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> BlacklistResponse:
    """Return paginated blacklist entries for a group (RBAC enforced)."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")

        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)

        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized")

        skip = (page - 1) * page_size
        entries = await db_service.get_blacklist_entries(group_id=group_id, limit=page_size, skip=skip)
        total = await db_service.db["blacklist"].count_documents({"group_id": group_id})

        return BlacklistResponse(
            ok=True,
            group_id=group_id,
            entries=[
                BlacklistEntry(
                    user_id=e.get("user_id"),
                    username=e.get("target_username") or e.get("username"),
                    reason=e.get("reason"),
                    added_by=e.get("added_by"),
                    added_at=e.get("added_at"),
                )
                for e in entries
            ],
            total_count=total,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting blacklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blacklist")


# ===== NEW COMMAND ENDPOINTS (Free, ID, Settings, Promote, Demote) =====

@router.post("/commands/free", response_model=FreeResponse)
async def free_user(
    request: FreeRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> FreeResponse:
    """Remove all restrictions from a user - REST API endpoint for /free command."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        # Check authorization (admin or owner)
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, request.group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized - admin required")
        
        # Execute unmute via Telegram API
        if telegram_api:
            await telegram_api.unmute_user(request.group_id, request.target_user_id)
        
        # Log action to database
        await db_service.log_action(
            group_id=request.group_id,
            action_type=ActionType.UNMUTE,
            admin_id=user_id,
            target_user_id=request.target_user_id,
            reason="Freed via API endpoint"
        )
        
        logger.info(f"User {request.target_user_id} freed from restrictions in group {request.group_id}")
        
        return FreeResponse(
            ok=True,
            message=f"✅ User freed from restrictions",
            action_id=f"free_{request.group_id}_{request.target_user_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error freeing user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to free user: {str(e)}")


@router.post("/commands/id", response_model=UserIDResponse)
async def get_user_id(
    request: UserIDRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    token_data: dict = Depends(verify_token),
) -> UserIDResponse:
    """Get user ID and information - REST API endpoint for /id command."""
    try:
        user_id = token_data.get("user_id")
        
        # Use provided user_id or fall back to authenticated user
        target_id = request.target_user_id or user_id
        
        # Get user info from database
        user_doc = await db_service.db["users"].find_one({"user_id": target_id})
        
        if not user_doc:
            return UserIDResponse(
                ok=False,
                message="User not found"
            )
        
        user_info = UserInfo(
            user_id=user_doc.get("user_id"),
            first_name=user_doc.get("first_name"),
            last_name=user_doc.get("last_name"),
            username=user_doc.get("username"),
            is_bot=user_doc.get("is_bot", False),
            group_id=request.group_id,
        )
        
        return UserIDResponse(
            ok=True,
            user=user_info,
            message="User info retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user ID: {str(e)}")


@router.get("/commands/settings/{group_id}", response_model=SettingsResponse)
async def get_group_settings(
    group_id: int,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> SettingsResponse:
    """Get group settings and admin list - REST API endpoint for /settings command."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        # Check authorization (admin or owner)
        is_authorized = False
        if role == UserRole.SUPERADMIN:
            is_authorized = True
        elif role == UserRole.GROUP_ADMIN:
            is_authorized = await db_service.is_group_admin(user_id, group_id)
        
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized - admin required")
        
        # Get group info
        group_doc = await db_service.db["groups"].find_one({"group_id": group_id})
        
        if not group_doc:
            return SettingsResponse(
                ok=False,
                message="Group not found"
            )
        
        # Get admins from database
        admin_docs = await db_service.db["admins"].find(
            {"group_id": group_id}
        ).limit(10).to_list(None)
        
        admins = [
            AdminInfo(
                user_id=a.get("user_id"),
                username=a.get("username"),
                first_name=a.get("first_name"),
                last_name=a.get("last_name"),
                custom_title=a.get("custom_title")
            )
            for a in admin_docs
        ]
        
        settings = GroupSettings(
            group_id=group_id,
            group_name=group_doc.get("group_name", ""),
            group_type=group_doc.get("group_type", "group"),
            member_count=group_doc.get("member_count", 0),
            admins=admins,
            description=group_doc.get("description")
        )
        
        return SettingsResponse(
            ok=True,
            settings=settings,
            message="Group settings retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.post("/commands/promote", response_model=PromoteResponse)
async def promote_user(
    request: PromoteRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> PromoteResponse:
    """Promote user to admin - REST API endpoint for /promote command."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        # Check authorization (owner only)
        if role != UserRole.SUPERADMIN:
            is_owner = await db_service.is_group_owner(user_id, request.group_id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Not authorized - owner required")
        
        # Promote via Telegram API
        if telegram_api:
            await telegram_api.promote_chat_member(
                request.group_id,
                request.target_user_id,
                can_delete_messages=True,
                can_restrict_members=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_pin_messages=True
            )
        
        # Set custom title if provided
        title_set = False
        if request.custom_title and telegram_api:
            try:
                await telegram_api.set_chat_administrator_custom_title(
                    request.group_id,
                    request.target_user_id,
                    request.custom_title[:16]  # Limit to 16 chars
                )
                title_set = True
            except Exception as e:
                logger.warning(f"Could not set custom title: {e}")
        
        # Store admin info in database
        await db_service.db["admins"].update_one(
            {"group_id": request.group_id, "user_id": request.target_user_id},
            {
                "$set": {
                    "group_id": request.group_id,
                    "user_id": request.target_user_id,
                    "username": request.target_username,
                    "custom_title": request.custom_title,
                    "promoted_at": datetime.utcnow(),
                    "promoted_by": user_id
                }
            },
            upsert=True
        )
        
        # Log action to database
        await db_service.log_action(
            group_id=request.group_id,
            action_type=ActionType.WARN,
            admin_id=user_id,
            target_user_id=request.target_user_id,
            reason=f"Promoted to admin with title: {request.custom_title or 'none'}"
        )
        
        logger.info(f"User {request.target_user_id} promoted to admin in group {request.group_id}")
        
        return PromoteResponse(
            ok=True,
            message=f"✅ User promoted to admin" + (f" with title: {request.custom_title}" if request.custom_title else ""),
            action_id=f"promote_{request.group_id}_{request.target_user_id}",
            title_set=title_set
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to promote user: {str(e)}")


@router.post("/commands/demote", response_model=DemoteResponse)
async def demote_user(
    request: DemoteRequest,
    authorization: str = Header(None),
    db_service: DatabaseService = Depends(get_db_service),
    telegram_api: TelegramAPIService = Depends(get_telegram_api_service),
    token_data: dict = Depends(verify_token),
) -> DemoteResponse:
    """Demote admin back to regular user - REST API endpoint for /demote command."""
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        
        # Check authorization (owner only)
        if role != UserRole.SUPERADMIN:
            is_owner = await db_service.is_group_owner(user_id, request.group_id)
            if not is_owner:
                raise HTTPException(status_code=403, detail="Not authorized - owner required")
        
        # Demote via Telegram API (remove all admin powers)
        if telegram_api:
            await telegram_api.promote_chat_member(
                request.group_id,
                request.target_user_id,
                can_delete_messages=False,
                can_restrict_members=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_pin_messages=False
            )
        
        # Remove from admin list in database
        await db_service.db["admins"].delete_one({
            "group_id": request.group_id,
            "user_id": request.target_user_id
        })
        
        # Log action to database
        await db_service.log_action(
            group_id=request.group_id,
            action_type=ActionType.WARN,
            admin_id=user_id,
            target_user_id=request.target_user_id,
            reason="Demoted from admin"
        )
        
        logger.info(f"User {request.target_user_id} demoted from admin in group {request.group_id}")
        
        return DemoteResponse(
            ok=True,
            message="✅ User demoted to regular member",
            action_id=f"demote_{request.group_id}_{request.target_user_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error demoting user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to demote user: {str(e)}")

