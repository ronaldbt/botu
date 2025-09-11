# backend/app/api/v1/telegram_routes.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import qrcode
from io import BytesIO
import base64
from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User
from app.db import crud_users
from app.schemas.user_schema import TelegramSubscription, TelegramStatusUpdate
from app.telegram.telegram_bot import telegram_bot

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Configurar logging
logger = logging.getLogger(__name__)

# Pydantic models
class TelegramConnectionResponse(BaseModel):
    telegram_token: str
    qr_code_base64: str
    telegram_link: str
    expires_in_minutes: int = 10

class TelegramStatusResponse(BaseModel):
    connected: bool
    chat_id: Optional[str] = None
    subscription_status: str
    bot_configured: bool

class SendAlertRequest(BaseModel):
    type: str  # BUY, SELL, INFO, WARNING
    symbol: str = "BTCUSDT"
    price: Optional[float] = None
    message: str
    user_ids: Optional[list[int]] = None  # Si None, envía a todos

class WebhookUpdate(BaseModel):
    """Modelo para recibir updates del webhook de Telegram"""
    pass  # Acepta cualquier estructura de datos

@router.get("/status", response_model=TelegramStatusResponse)
async def get_telegram_status(
    crypto: str = "btc",  # Parámetro de query para especificar crypto
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado de conexión de Telegram para el usuario actual y crypto específica"""
    try:
        # Mapear crypto a campos del modelo
        crypto = crypto.lower()
        if crypto == "bitcoin":
            crypto = "btc"
        elif crypto == "ethereum":
            crypto = "eth"
        
        subscribed = False
        chat_id = None
        
        if crypto == "btc":
            subscribed = current_user.telegram_subscribed_btc or False
            chat_id = current_user.telegram_chat_id_btc
        elif crypto == "eth":
            subscribed = current_user.telegram_subscribed_eth or False
            chat_id = current_user.telegram_chat_id_eth
        elif crypto == "bnb":
            subscribed = current_user.telegram_subscribed_bnb or False
            chat_id = current_user.telegram_chat_id_bnb
        
        return TelegramStatusResponse(
            connected=subscribed,
            chat_id=chat_id,
            subscription_status=current_user.subscription_status,
            bot_configured=telegram_bot.is_configured()
        )
    except Exception as e:
        logger.error(f"Error obteniendo estado de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo estado de Telegram"
        )

@router.post("/connect", response_model=TelegramConnectionResponse)
async def generate_telegram_connection(
    crypto: str = "btc",  # Parámetro para especificar la crypto
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera un token único y QR para conectar Telegram a una crypto específica"""
    try:
        # Normalizar crypto para obtener bot
        crypto_for_bot = crypto.lower()
        if crypto_for_bot == "btc":
            crypto_for_bot = "bitcoin"
        elif crypto_for_bot == "eth":
            crypto_for_bot = "ethereum"
        # bnb se mantiene como bnb
        
        # Mantener crypto original para campos de DB
        crypto = crypto.lower()
        
        # Verificar si el bot específico está configurado
        from app.telegram.crypto_bots import crypto_bots
        crypto_bot = crypto_bots.get_bot(crypto_for_bot)
        
        if not crypto_bot or not crypto_bot.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"El bot de {crypto.upper()} no está configurado en el servidor"
            )
        
        # Obtener o generar token único para esta crypto
        telegram_token = crud_users.get_or_create_telegram_token_crypto(db, current_user.id, crypto)
        if not telegram_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Crear link de Telegram con el bot específico
        bot_username = crypto_bot.bot_username.replace('@', '')
        if not bot_username:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo obtener información del bot"
            )
            
        telegram_link = f"https://t.me/{bot_username}?start={telegram_token}"
        
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(telegram_link)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qr_base64 = base64.b64encode(buf.read()).decode()
        
        return TelegramConnectionResponse(
            telegram_token=telegram_token,
            qr_code_base64=qr_base64,
            telegram_link=telegram_link,
            expires_in_minutes=10
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando conexión de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno generando código de conexión"
        )

@router.post("/validate-token")
async def validate_telegram_token(
    token: str,
    chat_id: str,
    crypto: str = "btc",  # Parámetro para especificar la crypto
    db: Session = Depends(get_db)
):
    """Valida un token de Telegram y registra la conexión (usado por el bot crypto específico)"""
    try:
        # Normalizar crypto
        crypto = crypto.lower()
        if crypto == "bitcoin":
            crypto = "btc"
        elif crypto == "ethereum":
            crypto = "eth"
        
        # Buscar usuario por token específico de crypto
        user = crud_users.get_user_by_telegram_token_crypto(db, token, crypto)
        if not user:
            return {
                "valid": False,
                "message": "Token inválido o expirado"
            }
        
        if not user.is_active:
            return {
                "valid": False,
                "message": "Usuario inactivo"
            }
        
        # Actualizar suscripción para la crypto específica
        crud_users.update_telegram_subscription_crypto(db, user.id, chat_id, crypto, True)
        
        return {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
            "message": f"¡Bienvenido {user.username}! Te has suscrito exitosamente a las alertas de BotU."
        }
        
    except Exception as e:
        logger.error(f"Error validando token de Telegram: {e}")
        return {
            "valid": False,
            "message": "Error interno del servidor"
        }

@router.post("/disconnect")
async def disconnect_telegram(current_user: User = Depends(get_current_user)):
    """Desconecta la cuenta de Telegram del usuario actual"""
    try:
        user_id = current_user.id
        
        if user_id in telegram_bot.user_connections:
            chat_id = telegram_bot.user_connections[user_id]
            del telegram_bot.user_connections[user_id]
            
            # Notificar al usuario en Telegram
            telegram_bot._send_message(
                chat_id, 
                "🔌 Tu cuenta BotU ha sido desconectada desde la aplicación web."
            )
            
            logger.info(f"Usuario {user_id} desconectado de Telegram")
            
        return {"message": "Desconectado exitosamente de Telegram"}
        
    except Exception as e:
        logger.error(f"Error desconectando de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error desconectando de Telegram"
        )

@router.get("/active-users")
async def get_active_telegram_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista de usuarios activos suscritos (solo para admins)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden ver usuarios activos"
            )
        
        active_users = crud_users.get_active_telegram_users(db)
        
        return {
            "total_active": len(active_users),
            "users": [
                {
                    "user_id": user.id,
                    "username": user.username,
                    "chat_id": user.telegram_chat_id,
                    "subscription_status": user.subscription_status,
                    "last_activity": user.last_activity
                }
                for user in active_users
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo usuarios activos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo usuarios activos"
        )

@router.post("/send-alert")
async def send_telegram_alert(
    alert_request: SendAlertRequest,
    current_user: User = Depends(get_current_user)
):
    """Envía una alerta de prueba a Telegram (solo para testing)"""
    try:
        if not telegram_bot.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot de Telegram no configurado"
            )
        
        alert_data = {
            'type': alert_request.type,
            'symbol': alert_request.symbol,
            'price': alert_request.price,
            'message': alert_request.message
        }
        
        # Si se especifican user_ids, enviar broadcast, sino solo al usuario actual
        if alert_request.user_ids:
            # Solo admins pueden enviar a múltiples usuarios
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden enviar alertas masivas"
                )
            
            result = telegram_bot.broadcast_alert(alert_data, alert_request.user_ids)
        else:
            # Enviar solo al usuario actual
            success = telegram_bot.send_bitcoin_alert(current_user.id, alert_data)
            result = {
                'sent': 1 if success else 0,
                'failed': 0 if success else 1,
                'total_targets': 1,
                'message': 'Alerta enviada' if success else 'Error enviando alerta'
            }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enviando alerta de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno enviando alerta"
        )

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint para recibir updates del webhook de Telegram"""
    try:
        if not telegram_bot.is_configured():
            return {"status": "error", "message": "Bot no configurado"}
        
        # Obtener los datos del webhook
        update_data = await request.json()
        
        logger.info(f"Webhook recibido: {update_data}")
        
        # Procesar la actualización
        result = telegram_bot.process_telegram_update(update_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error procesando webhook de Telegram: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/bot-info")
async def get_bot_info(current_user: User = Depends(get_current_user)):
    """Obtiene información del bot de Telegram"""
    try:
        if not telegram_bot.is_configured():
            return {
                "configured": False,
                "message": "Bot de Telegram no configurado"
            }
        
        bot_username = telegram_bot._get_bot_username()
        
        return {
            "configured": True,
            "bot_username": bot_username,
            "connected_users": len(telegram_bot.user_connections),
            "pending_connections": len(telegram_bot.pending_connections)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo información del bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo información del bot"
        )

@router.post("/cleanup")
async def cleanup_connections(current_user: User = Depends(get_current_user)):
    """Limpia conexiones expiradas (solo para admins)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden realizar limpieza"
            )
        
        initial_count = len(telegram_bot.pending_connections)
        telegram_bot.cleanup_expired_connections()
        final_count = len(telegram_bot.pending_connections)
        cleaned = initial_count - final_count
        
        return {
            "message": f"Limpieza completada: {cleaned} conexiones expiradas removidas",
            "cleaned_count": cleaned,
            "remaining_pending": final_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en limpieza: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error realizando limpieza"
        )

@router.post("/poll-messages")
async def poll_telegram_messages(current_user: User = Depends(get_current_user)):
    """Verifica mensajes pendientes de Telegram manualmente (para desarrollo local)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden hacer polling manual"
            )
        
        if not telegram_bot.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bot de Telegram no configurado"
            )
        
        # Hacer polling manual para verificar mensajes
        telegram_bot.setup_manual_polling()
        
        return {
            "message": "Polling manual completado - revisa los logs para ver mensajes procesados",
            "bot_configured": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en polling manual: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en polling manual"
        )