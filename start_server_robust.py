#!/usr/bin/env python3
"""
Inicio robusto del servidor optimizado para producción
"""

import uvicorn
import os
import sys

# Configurar path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

if __name__ == "__main__":
    # Configuración optimizada para servidor
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,  # Sin reload en producción
        "workers": 1,  # Un solo worker para evitar problemas
        "timeout_keep_alive": 120,  # 2 minutos keep alive
        "timeout_graceful_shutdown": 30,  # 30s para shutdown
        "limit_concurrency": 10,  # Máximo 10 requests concurrentes
        "limit_max_requests": 1000,  # Reiniciar worker cada 1000 requests
        "log_level": "info",
        "access_log": False,  # Deshabilitar access log para performance
    }
    
    print("🚀 Iniciando servidor robusto...")
    print("⚙️ Configuración optimizada para producción")
    print("📊 Memoria optimizada | Timeouts configurados | Concurrencia limitada")
    print("="*60)
    
    uvicorn.run(**config)