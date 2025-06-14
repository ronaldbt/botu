# app/schemas/user_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserLoginSchema(BaseModel):
    id: int
    user_id: int
    login_time: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        from_attributes = True  # compatible con Pydantic v2

class UserSchema(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True
