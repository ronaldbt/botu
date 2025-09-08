#!/usr/bin/env python3
"""
Script para crear un usuario administrador en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db import models
from app.core.auth import get_password_hash
from sqlalchemy.orm import Session

def create_admin_user():
    """Crea un usuario administrador"""
    db = SessionLocal()
    try:
        # Verificar si ya existe un admin
        existing_admin = db.query(models.User).filter(models.User.username == "admin").first()
        if existing_admin:
            print("❌ El usuario 'admin' ya existe")
            return
        
        # Crear usuario administrador
        admin_user = models.User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuario administrador creado exitosamente!")
        print("📧 Username: admin")
        print("🔑 Password: admin123")
        print("👑 Rol: Administrador")
        print("")
        print("🌐 Puedes acceder a:")
        print("   Frontend: http://localhost:5173")
        print("   Backend API: http://localhost:8000")
        print("   Documentación: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
