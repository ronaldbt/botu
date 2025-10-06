#!/usr/bin/env python3

"""
Script para hacer administrador a un usuario
"""

import os
import sys
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import crud_users

def make_admin(username: str):
    """Hace administrador a un usuario"""
    
    db = SessionLocal()
    
    try:
        # Buscar el usuario
        user = crud_users.get_user_by_username(db, username)
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return
        
        # Verificar si ya es admin
        if user.is_admin:
            print(f"⚠️ El usuario '{username}' ya es administrador")
            return
        
        # Actualizar a admin
        from app.schemas.user_schema import UserUpdate
        user_update = UserUpdate(is_admin=True)
        
        updated_user = crud_users.update_user(db, user.id, user_update)
        
        print(f"✅ Usuario '{username}' ahora es administrador!")
        print(f"   ID: {updated_user.id}")
        print(f"   Username: {updated_user.username}")
        print(f"   Admin: {updated_user.is_admin}")
        print(f"   Activo: {updated_user.is_active}")
        
    except Exception as e:
        print(f"❌ Error haciendo admin al usuario: {e}")
        db.rollback()
    finally:
        db.close()

def list_users():
    """Lista todos los usuarios"""
    db = SessionLocal()
    
    try:
        users = crud_users.get_users(db, skip=0, limit=100)
        print("\n📋 Lista de usuarios:")
        print("-" * 50)
        for user in users:
            admin_text = "✅ Admin" if user.is_admin else "   Usuario"
            active_text = "✅ Activo" if user.is_active else "❌ Inactivo"
            telegram_text = "📱 Telegram" if user.telegram_subscribed else "   No conectado"
            print(f"{user.id:2d} | {user.username:15s} | {admin_text} | {active_text} | {telegram_text}")
        
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python make_admin.py <username>")
        print("Ejemplo: python make_admin.py vlad")
        print("\nListando usuarios actuales:")
        list_users()
    else:
        username = sys.argv[1]
        print(f"🔄 Haciendo administrador a '{username}'...")
        make_admin(username)
        print("\nListando usuarios actualizados:")
        list_users()