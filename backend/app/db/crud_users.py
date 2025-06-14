# app/db/crud_users.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas.auth_schema import UserCreate
from passlib.context import CryptContext
from datetime import datetime

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Obtener usuario por username
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Crear nuevo usuario
def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, password_hash=hashed_password, is_admin=user.is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Verificar password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Registrar login en tabla user_logins
def log_user_login(db: Session, user_id: int, ip_address: str = None, user_agent: str = None):
    login_entry = models.UserLogin(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(login_entry)
    db.commit()
    db.refresh(login_entry)
    return login_entry

# Actualizar last_login (opcional, si tu modelo User tiene last_login)
# Si no tienes esta columna, puedes borrar esta función.
def update_last_login(db: Session, user: models.User):
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
