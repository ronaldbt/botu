# backend/app/db/crud_users.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.auth import get_password_hash, verify_password
from typing import List, Optional
import secrets
import string
from datetime import datetime, timezone

def get_user(db: Session, user_id: int):
    """Obtiene un usuario por ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """Obtiene un usuario por nombre de usuario"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene una lista de usuarios"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    """Crea un nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        is_admin=user.is_admin,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    """Actualiza un usuario existente"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    
    # Actualizar campos básicos
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.is_admin is not None:
        db_user.is_admin = user_update.is_admin
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    
    # Actualizar campos de Telegram
    if user_update.telegram_chat_id is not None:
        db_user.telegram_chat_id = user_update.telegram_chat_id
    if user_update.telegram_subscribed is not None:
        db_user.telegram_subscribed = user_update.telegram_subscribed
    if user_update.subscription_status is not None:
        db_user.subscription_status = user_update.subscription_status
    
    # Actualizar contraseña si se proporciona
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """Elimina un usuario"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def authenticate_user(db: Session, username: str, password: str):
    """Autentica un usuario"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

# Funciones específicas de Telegram

def generate_telegram_token() -> str:
    """Genera un token único para Telegram"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def get_or_create_telegram_token(db: Session, user_id: int) -> str:
    """Obtiene o crea un token de Telegram para un usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    if not db_user.telegram_token:
        db_user.telegram_token = generate_telegram_token()
        db.commit()
        db.refresh(db_user)
    
    return db_user.telegram_token

def get_user_by_telegram_token(db: Session, token: str):
    """Obtiene un usuario por su token de Telegram"""
    return db.query(models.User).filter(models.User.telegram_token == token).first()

def get_user_by_telegram_chat_id(db: Session, chat_id: str):
    """Obtiene un usuario por su chat_id de Telegram"""
    return db.query(models.User).filter(models.User.telegram_chat_id == chat_id).first()

def update_telegram_subscription(db: Session, user_id: int, chat_id: str, subscribed: bool = True):
    """Actualiza la suscripción de Telegram de un usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    db_user.telegram_chat_id = chat_id
    db_user.telegram_subscribed = subscribed
    db_user.subscription_status = 'active' if subscribed else 'inactive'
    db_user.last_activity = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_active_telegram_users(db: Session):
    """Obtiene usuarios con suscripción activa de Telegram"""
    return db.query(models.User).filter(
        models.User.telegram_subscribed == True,
        models.User.subscription_status == 'active',
        models.User.is_active == True,
        models.User.telegram_chat_id.isnot(None)
    ).all()

def update_user_activity(db: Session, user_id: int):
    """Actualiza la última actividad del usuario"""
    db_user = get_user(db, user_id)
    if db_user:
        db_user.last_activity = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
    return db_user

def get_admin_telegram_users(db: Session):
    """Obtiene administradores con Telegram configurado para alertas de salud"""
    return db.query(models.User).filter(
        models.User.is_admin == True,
        models.User.is_active == True,
        models.User.telegram_chat_id.isnot(None),
        models.User.telegram_subscribed == True
    ).all()