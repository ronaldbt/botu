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
        models.User.telegram_chat_id_btc.isnot(None),
        models.User.telegram_subscribed_btc == True
    ).all()

def get_or_create_telegram_token_crypto(db: Session, user_id: int, crypto: str) -> str:
    """Obtiene o crea un token de Telegram para un usuario y crypto específica"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Mapear crypto a campos del modelo
    token_field = f"telegram_token_{crypto}"
    token_created_field = f"telegram_token_{crypto}_created"
    
    current_token = getattr(db_user, token_field, None)
    token_created = getattr(db_user, token_created_field, None)
    
    # Verificar si el token existe y no ha expirado (3 minutos)
    token_expired = False
    if token_created:
        from datetime import datetime, timezone, timedelta
        expiration_time = token_created + timedelta(minutes=3)
        token_expired = datetime.now(timezone.utc) > expiration_time
    
    # Si no hay token o ha expirado, crear uno nuevo
    if not current_token or token_expired:
        new_token = generate_telegram_token()
        setattr(db_user, token_field, new_token)
        setattr(db_user, token_created_field, datetime.now(timezone.utc))
        db.commit()
        db.refresh(db_user)
        return new_token
    
    return current_token

def get_user_by_telegram_token_crypto(db: Session, token: str, crypto: str):
    """Obtiene un usuario por su token de Telegram de una crypto específica"""
    token_field = f"telegram_token_{crypto}"
    return db.query(models.User).filter(getattr(models.User, token_field) == token).first()

def get_active_telegram_users_by_crypto(db: Session, crypto: str):
    """Obtiene usuarios con suscripción activa de Telegram para una crypto específica"""
    import logging
    logger = logging.getLogger(__name__)
    
    subscribed_field = f"telegram_subscribed_{crypto}"
    chat_id_field = f"telegram_chat_id_{crypto}"
    
    logger.info(f"🔍 Buscando usuarios para crypto: {crypto}")
    logger.info(f"🔍 Campos: {subscribed_field}, {chat_id_field}")
    
    # Obtener todos los usuarios primero para debug
    all_users = db.query(models.User).all()
    logger.info(f"🔍 Total usuarios en BD: {len(all_users)}")
    
    for user in all_users:
        subscribed = getattr(user, subscribed_field, None)
        chat_id = getattr(user, chat_id_field, None)
        logger.info(f"🔍 Usuario {user.username}: subscribed={subscribed}, chat_id={chat_id}, status={user.subscription_status}, active={user.is_active}")
    
    # Query original con logs
    result = db.query(models.User).filter(
        getattr(models.User, subscribed_field) == True,
        models.User.subscription_status == 'active',
        models.User.is_active == True,
        getattr(models.User, chat_id_field).isnot(None)
    ).all()
    
    logger.info(f"🔍 Usuarios encontrados para {crypto}: {len(result)}")
    for user in result:
        chat_id = getattr(user, chat_id_field)
        logger.info(f"✅ Usuario activo: {user.username} (chat_id: {chat_id})")
    
    return result

def update_telegram_subscription_crypto(db: Session, user_id: int, chat_id: str, crypto: str, subscribed: bool = True):
    """Actualiza la suscripción de Telegram de un usuario para una crypto específica"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Mapear crypto a campos del modelo
    chat_id_field = f"telegram_chat_id_{crypto}"
    subscribed_field = f"telegram_subscribed_{crypto}"
    
    setattr(db_user, chat_id_field, chat_id)
    setattr(db_user, subscribed_field, subscribed)
    db_user.subscription_status = 'active' if subscribed else 'inactive'
    db_user.last_activity = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def regenerate_telegram_token_crypto(db: Session, user_id: int, crypto: str) -> str:
    """Regenera un nuevo token de Telegram para un usuario y crypto específica"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Mapear crypto a campos del modelo
    token_field = f"telegram_token_{crypto}"
    token_created_field = f"telegram_token_{crypto}_created"
    
    # Generar nuevo token
    new_token = generate_telegram_token()
    setattr(db_user, token_field, new_token)
    setattr(db_user, token_created_field, datetime.now(timezone.utc))
    
    db.commit()
    db.refresh(db_user)
    return new_token

def get_telegram_token_info_crypto(db: Session, user_id: int, crypto: str) -> dict:
    """Obtiene información del token de una crypto específica incluyendo tiempo restante"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    token_field = f"telegram_token_{crypto}"
    token_created_field = f"telegram_token_{crypto}_created"
    
    current_token = getattr(db_user, token_field, None)
    token_created = getattr(db_user, token_created_field, None)
    
    if not current_token or not token_created:
        return {"token": None, "expires_in_seconds": 0, "expired": True}
    
    from datetime import datetime, timezone, timedelta
    expiration_time = token_created + timedelta(minutes=3)
    now = datetime.now(timezone.utc)
    
    expires_in_seconds = max(0, int((expiration_time - now).total_seconds()))
    expired = expires_in_seconds <= 0
    
    return {
        "token": current_token,
        "created_at": token_created,
        "expires_in_seconds": expires_in_seconds,
        "expired": expired
    }