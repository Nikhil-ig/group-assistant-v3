# Telegram Authentication Backend Example (FastAPI)

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import hashlib
import hmac
import time
from datetime import datetime, timedelta
import os
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"


class TelegramAuthRequest(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str = ""
    username: str = ""
    photo_url: str = ""
    auth_date: int
    hash: str


class AuthResponse(BaseModel):
    access_token: str
    user: dict


def verify_telegram_auth(auth_data: TelegramAuthRequest) -> bool:
    """
    Verify Telegram authentication hash to prevent spoofing.
    
    Follows Telegram's official verification algorithm:
    https://core.telegram.org/widgets/login#checking-authorization
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")
    
    # Check if auth_date is not too old (e.g., max 10 minutes)
    if int(time.time()) - auth_data.auth_date > 600:
        return False
    
    # Create the data check string (sorted by key)
    data_dict = {
        'id': auth_data.telegram_id,
        'first_name': auth_data.first_name,
        'last_name': auth_data.last_name,
        'username': auth_data.username,
        'photo_url': auth_data.photo_url,
        'auth_date': auth_data.auth_date,
    }
    
    # Remove empty strings
    data_dict = {k: v for k, v in data_dict.items() if v}
    
    # Create data check string
    data_check_string = '\n'.join(
        f'{k}={v}' for k, v in sorted(data_dict.items())
    )
    
    # Calculate hash
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare hashes
    return computed_hash == auth_data.hash


def create_or_update_telegram_user(auth_data: TelegramAuthRequest) -> dict:
    """
    Create or update user from Telegram data.
    You should implement this based on your database.
    """
    # TODO: Implement database operations
    user_data = {
        'id': auth_data.telegram_id,
        'username': auth_data.username or f"telegram_{auth_data.telegram_id}",
        'email': f"{auth_data.username or auth_data.telegram_id}@telegram.local",
        'first_name': auth_data.first_name,
        'last_name': auth_data.last_name,
        'photo_url': auth_data.photo_url,
        'role': 'admin',  # Adjust based on your business logic
        'permissions': [
            {'action': 'manage_groups', 'scope': 'system', 'allowed': True},
            {'action': 'manage_users', 'scope': 'system', 'allowed': True},
            {'action': 'manage_actions', 'scope': 'system', 'allowed': True},
        ]
    }
    return user_data


def create_jwt_token(user_id: int, user_data: dict) -> str:
    """Create JWT token for authenticated user."""
    payload = {
        'sub': str(user_id),
        'user': user_data,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


@router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(auth_data: TelegramAuthRequest):
    """
    Authenticate user via Telegram OAuth.
    
    This endpoint receives verified Telegram user data from the frontend
    and exchanges it for a JWT token.
    """
    try:
        # Verify the hash signature
        if not verify_telegram_auth(auth_data):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication hash"
            )
        
        # Create or update user in database
        user_data = create_or_update_telegram_user(auth_data)
        
        # Generate JWT token
        access_token = create_jwt_token(auth_data.telegram_id, user_data)
        
        return AuthResponse(
            access_token=access_token,
            user=user_data
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed"
        )


@router.post("/telegram/verify")
async def verify_telegram_token(token: str):
    """
    Optional: Verify if a Telegram token is still valid.
    Can be used for session management.
    """
    try:
        # TODO: Implement token verification
        return {"valid": True}
    except Exception:
        return {"valid": False}


# Example usage in main app:
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(router)
