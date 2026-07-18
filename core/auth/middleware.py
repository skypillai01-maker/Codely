import logging
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth.database import validate_session, cleanup_expired_sessions

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    cleanup_expired_sessions()

    session = validate_session(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return {
        "user_id": session["user_id"],
        "email": session["email"],
        "display_name": session["display_name"],
        "session_id": session["session_id"]
    }

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict | None:
    if not credentials:
        return None

    cleanup_expired_sessions()
    session = validate_session(credentials.credentials)
    if not session:
        return None

    return {
        "user_id": session["user_id"],
        "email": session["email"],
        "display_name": session["display_name"],
        "session_id": session["session_id"]
    }
