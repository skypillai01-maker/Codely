from pydantic import BaseModel, EmailStr
from typing import Optional

class MagicLinkRequest(BaseModel):
    email: str
    display_name: Optional[str] = None

class VerifyTokenRequest(BaseModel):
    token: str

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    email: str
    display_name: str
    expires_at: str

class UserInfo(BaseModel):
    user_id: str
    email: str
    display_name: str
    created_at: str
    last_login: Optional[str] = None
