from sqlalchemy.orm import Session
from app.db import models
from app.schemas import user_schema
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utils

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# CRUD

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, username: str, password: str, is_admin: bool = False):
    hashed_password = hash_password(password)
    db_user = models.User(
        username=username,
        password_hash=hashed_password,
        is_admin=is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def log_user_login(db: Session, user_id: int, ip_address: str = None, user_agent: str = None):
    login_entry = models.UserLogin(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
        # login_time se setea automáticamente con func.now()
    )
    db.add(login_entry)
    db.commit()
    db.refresh(login_entry)
    return login_entry
