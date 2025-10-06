#!/usr/bin/env python3
"""
Script para resetear la contraseña de un usuario existente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db import models
from app.core.auth import get_password_hash
from sqlalchemy.orm import Session

def reset_user_password():
    """Resetea la contraseña del usuario vlad"""
    db = SessionLocal()
    try:
        # Buscar el usuario existente
        user = db.query(models.User).filter(models.User.username == "vlad").first()
        if not user:
            print("❌ El usuario 'vlad' no existe")
            return
        
        # Actualizar contraseña
        user.password_hash = get_password_hash("parol777")
        user.is_active = True  # Asegurar que esté activo
        
        db.commit()
        db.refresh(user)
        
        print("✅ Contraseña actualizada exitosamente!")
        print("📧 Username: vlad")
        print("🔑 Password: parol777")
        print(f"👑 Rol: {'Administrador' if user.is_admin else 'Usuario'}")
        print(f"🟢 Estado: {'Activo' if user.is_active else 'Inactivo'}")
        print("")
        print("🌐 Puedes acceder a:")
        print("   Frontend: http://localhost:5173")
        print("   Backend API: http://localhost:8000")
        print("   Documentación: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error actualizando contraseña: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_user_password()