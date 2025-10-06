#!/usr/bin/env python3

"""
Script para crear el usuario de prueba 'juan'
"""

import os
import sys
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import crud_users
from app.schemas.user_schema import UserCreate

def create_test_user():
    """Crea el usuario de prueba 'juan'"""
    
    db = SessionLocal()
    
    try:
        # Verificar si el usuario ya existe
        existing_user = crud_users.get_user_by_username(db, "juan")
        if existing_user:
            print("⚠️ El usuario 'juan' ya existe")
            print(f"   ID: {existing_user.id}")
            print(f"   Admin: {existing_user.is_admin}")
            print(f"   Activo: {existing_user.is_active}")
            print(f"   Telegram: {existing_user.telegram_subscribed}")
            return
        
        # Crear el nuevo usuario
        user_data = UserCreate(
            username="juan",
            password="juan123",
            is_admin=False,
            is_active=True,
            telegram_subscribed=False,
            subscription_status="inactive"
        )
        
        new_user = crud_users.create_user(db, user_data)
        
        print("✅ Usuario de prueba 'juan' creado exitosamente!")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Admin: {new_user.is_admin}")
        print(f"   Activo: {new_user.is_active}")
        print(f"   Password: juan123")
        print(f"   Telegram token: {new_user.telegram_token or 'Se generará al conectar'}")
        
    except Exception as e:
        print(f"❌ Error creando usuario de prueba: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Creando usuario de prueba 'juan'...")
    create_test_user()