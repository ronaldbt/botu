# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os
from dotenv import load_dotenv
from app.db import models
from app.db.database import engine
from app.api.v1 import u_routes, auth_routes, ordenes_routes, alertas_routes, users_routes, bitcoin_bot_routes, telegram_routes, eth_bot_routes, bnb_bot_routes, profile_routes, health_routes, health_telegram_routes, trading_routes, debug_routes
from app.services.health_monitor_service import health_monitor

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    try:
        logger.info("🚀 BOTU SERVER STARTING UP...")
        
        # Inicializar crypto bots
        try:
            from app.telegram.crypto_bots import crypto_bots
            logger.info("🤖 Crypto Bots inicializados correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando crypto bots: {e}")
        
        # Iniciar Health Monitor automáticamente
        success = await health_monitor.start_monitoring()
        if success:
            logger.info("✅ Health Monitor iniciado automáticamente")
        else:
            logger.error("❌ Error iniciando Health Monitor automáticamente")
        
        # Iniciar Alert Sender automáticamente
        try:
            from app.telegram.alert_sender import alert_sender
            # Ejecutar en background sin bloquear
            asyncio.create_task(alert_sender.start_monitoring())
            logger.info("✅ Alert Sender iniciado automáticamente")
        except Exception as e:
            logger.error(f"❌ Error iniciando Alert Sender: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error en startup automático: {e}")
    
    yield
    
    # Shutdown
    try:
        logger.info("🛑 BOTU SERVER SHUTTING DOWN...")
        await health_monitor.stop_monitoring()
        logger.info("✅ Health Monitor detenido correctamente")
        
        # Detener Alert Sender
        try:
            from app.telegram.alert_sender import alert_sender
            alert_sender.stop_monitoring()
            logger.info("✅ Alert Sender detenido correctamente")
        except Exception as e:
            logger.error(f"❌ Error deteniendo Alert Sender: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {e}")

# Inicializar FastAPI
app = FastAPI(
    title="BotU API",
    description="API para BotU - Monitoreo de patrones U",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS dinámicamente según el entorno
environment = os.getenv("ENVIRONMENT", "development")
cors_origins_env = os.getenv("CORS_ORIGINS", "")

if cors_origins_env:
    # Usar orígenes desde variables de entorno
    origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Fallback a configuración por defecto (desarrollo + producción)
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://botut.net",
        "https://www.botut.net",
    ]

logger.info(f"🌐 CORS configurado para {environment} - Orígenes permitidos: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint raíz (ping)
@app.get("/")
def read_root():
    return {"message": "BotU API running 🚀"}

# Routers
app.include_router(u_routes.router)             # Ya tiene prefix="/signals"
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(ordenes_routes.router)       # Ya tiene prefix="/ordenes"
app.include_router(alertas_routes.router)       # Ya tiene prefix="/alertas"
app.include_router(users_routes.router)         # Ya tiene prefix="/users"
app.include_router(bitcoin_bot_routes.router, tags=["bitcoin-bot"])  # Bitcoin Bot endpoints
app.include_router(eth_bot_routes.router, tags=["eth-bot"])      # Ethereum Bot endpoints
app.include_router(bnb_bot_routes.router, tags=["bnb-bot"])      # BNB Bot endpoints
app.include_router(profile_routes.router, tags=["profile"])      # Profile and subscription endpoints
app.include_router(telegram_routes.router)      # Ya tiene prefix="/telegram"
app.include_router(trading_routes.router, tags=["trading"])      # Trading automático endpoints
app.include_router(health_routes.router, tags=["health"])        # Health Monitor endpoints
app.include_router(health_telegram_routes.router, tags=["health-telegram"])  # Health Telegram Bot endpoints
app.include_router(debug_routes.router, tags=["debug"])                   # Debug endpoints
