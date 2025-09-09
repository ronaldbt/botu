# backend/app/schemas/user_schema.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    is_admin: bool = False
    is_active: bool = True
    telegram_subscribed: bool = False
    subscription_status: str = 'inactive'

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    telegram_subscribed: Optional[bool] = None
    subscription_status: Optional[str] = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TelegramSubscription(BaseModel):
    telegram_token: str
    qr_code_data: str
    bot_link: str

class TelegramStatusUpdate(BaseModel):
    telegram_chat_id: str
    telegram_subscribed: bool
    subscription_status: str