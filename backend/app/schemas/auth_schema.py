# app/schemas/auth_schema.py

from pydantic import BaseModel

# Para crear usuario (ya lo tenías)
class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False

# Para devolver usuario (ya lo tenías)
class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True  # Para compatibilidad con SQLAlchemy

# 👉 Nuevo: para login request (se envía desde LoginView.vue)
class UserLoginRequest(BaseModel):
    username: str
    password: str
