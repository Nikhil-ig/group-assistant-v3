"""
History & Logging Endpoints
Handles command logging and history tracking
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/advanced/history", tags=["history"])


@router.post("/log-command", response_model=Dict[str, Any])
async def log_command_execution(command_log: dict = Body(...)):
    """Log command execution to history"""
    try:
        # Extract command data
        group_id = command_log.get("group_id")
        user_id = command_log.get("user_id")
        command = command_log.get("command")
        args = command_log.get("args", "")
        status = command_log.get("status", "completed")
        result = command_log.get("result", "")
        
        # Log the command
        logger.info(
            f"Command logged: {command} with args '{args}' "
            f"by user {user_id} in group {group_id} - Status: {status}"
        )
        
        # Return success response with command record
        return {
            "success": True,
            "data": {
                "id": str(uuid.uuid4()),
                "group_id": group_id,
                "user_id": user_id,
                "command": command,
                "args": args,
                "status": status,
                "result": result,
                "created_at": datetime.now().isoformat()
            },
            "message": "Command logged successfully"
        }
    except Exception as e:
        logger.error(f"Failed to log command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log command: {str(e)}")
