# app/api/v1/auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import user_crud
from app.core import auth
from app.core.config import settings
from datetime import timedelta
from app.schemas.auth_schema import UserLoginRequest, UserOut  # 👈 importar UserOut para devolverlo

router = APIRouter(tags=["auth"])

@router.post("/login")
def login(user_in: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_username(db, user_in.username)
    if not user or not auth.verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Registrar login
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    user_crud.log_user_login(db, user.id, ip_address, user_agent)

    # Crear JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Devolver también el user (para que Sidebar pueda funcionar bien)
    user_out = UserOut(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_out
    }
