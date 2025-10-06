import sys
import os
import django
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import user_crud

def main():
    print("🚀 Crear usuario ADMIN para BotU")

    username = input("👉 Ingrese nombre de usuario: ").strip()
    password = input("👉 Ingrese contraseña: ").strip()

    if not username or not password:
        print("❌ Username y contraseña son obligatorios.")
        sys.exit(1)

    db: Session = SessionLocal()

    existing_user = user_crud.get_user_by_username(db, username)
    if existing_user:
        print(f"⚠️ El usuario '{username}' ya existe.")
        db.close()
        sys.exit(1)

    admin_user = user_crud.create_user(db, username=username, password=password, is_admin=True)

    db.close()

    print(f"✅ Usuario ADMIN '{admin_user.username}' creado correctamente.")

if __name__ == "__main__":
    main()
