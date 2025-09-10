# backend/app/api/v1/health_telegram_routes.py

from fastapi import APIRouter, Request, HTTPException
import logging
from typing import Dict, Any

from app.telegram.health_bot import health_bot

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/health-telegram/webhook")
async def health_telegram_webhook(request: Request):
    """Webhook para el bot de Telegram de salud"""
    try:
        # Obtener datos del webhook
        update = await request.json()
        
        # Procesar update
        result = health_bot.handle_webhook(update)
        
        logger.info(f"🏥 Health webhook procesado: {result}")
        
        return {"status": "ok", "result": result}
        
    except Exception as e:
        logger.error(f"❌ Error en health webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando webhook: {str(e)}")

@router.get("/health-telegram/info")
async def health_telegram_info():
    """Información del bot de salud"""
    try:
        return {
            "bot_name": "@BotuHealthBot",
            "description": "Bot de monitoreo de salud del sistema BotU",
            "features": [
                "Reportes automáticos 2 veces al día",
                "Alertas críticas inmediatas", 
                "Comandos interactivos para administradores",
                "Monitoreo 24/7 del sistema"
            ],
            "commands": [
                "/start - Iniciar monitoreo",
                "/status - Estado del sistema",
                "/report - Reporte completo",
                "/help - Ayuda"
            ],
            "webhook_url": "/health-telegram/webhook",
            "admin_only": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info del health bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))