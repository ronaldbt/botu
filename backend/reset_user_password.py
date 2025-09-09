#!/usr/bin/env python3

"""
Script para resetear la contraseña de un usuario
"""

import os
import sys
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import crud_users
from app.core.auth import get_password_hash

def reset_password(username: str, new_password: str):
    """Resetea la contraseña de un usuario"""
    
    db = SessionLocal()
    
    try:
        # Buscar el usuario
        user = crud_users.get_user_by_username(db, username)
        if not user:
            print(f"❌ Usuario '{username}' no encontrado")
            return False
        
        # Hashear la nueva contraseña
        hashed_password = get_password_hash(new_password)
        
        # Actualizar la contraseña directamente en la base de datos
        from sqlalchemy import text
        db.execute(text("UPDATE users SET password_hash = :hash WHERE id = :user_id"), {
            'hash': hashed_password, 
            'user_id': user.id
        })
        db.commit()
        
        print(f"✅ Contraseña actualizada para '{username}'!")
        print(f"   Nueva contraseña: {new_password}")
        print(f"   Usuario ID: {user.id}")
        print(f"   Es admin: {user.is_admin}")
        print(f"   Está activo: {user.is_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando contraseña: {e}")
        db.rollback()
        return False
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
            print(f"{user.id:2d} | {user.username:15s} | {admin_text} | {active_text}")
        
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reset_user_password.py <username> <nueva_contraseña>")
        print("Ejemplo: python reset_user_password.py vlad parol777")
        print("\nListando usuarios actuales:")
        list_users()
    else:
        username = sys.argv[1]
        new_password = sys.argv[2]
        print(f"🔄 Reseteando contraseña para '{username}'...")
        if reset_password(username, new_password):
            print(f"\n🎉 ¡Listo! Ahora puedes hacer login con:")
            print(f"   Usuario: {username}")
            print(f"   Contraseña: {new_password}")
        list_users()