# backend/app/api/v1/telegram_routes.py

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import qrcode
from io import BytesIO
import base64
import requests
import os
from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User, TradingEvent
from app.db import crud_users
from app.schemas.user_schema import TelegramSubscription, TelegramStatusUpdate
from app.telegram.telegram_bot import telegram_bot
from app.db.models import TelegramConnection
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Configurar logging
logger = logging.getLogger(__name__)

# Pydantic models
class TelegramConnectionResponse(BaseModel):
    telegram_token: str
    qr_code_base64: str
    telegram_link: str
    expires_in_seconds: int
    expires_in_minutes: int = 3  # Ahora es 3 minutos
    created_at: Optional[str] = None

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

# -----------------------------
# Endpoints unificados (single bot)
# -----------------------------

class UnifiedStatusResponse(BaseModel):
    connected: bool
    chat_id: Optional[str]
    bot_configured: bool
    connection_id: Optional[int]
    token_expires_at: Optional[str]

@router.get("/status-main", response_model=UnifiedStatusResponse)
async def get_status_main(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        bot_configured = True if os.getenv('TELEGRAM_BOT_TOKEN') else False
        conn = db.query(TelegramConnection).filter(TelegramConnection.user_id == current_user.id).order_by(TelegramConnection.connected_at.desc().nullslast(), TelegramConnection.created_at.desc()).first()
        connected = bool(conn and conn.connected and conn.chat_id)
        return UnifiedStatusResponse(
            connected=connected,
            chat_id=conn.chat_id if conn else None,
            bot_configured=bot_configured,
            connection_id=conn.id if conn else None,
            token_expires_at=conn.token_expires_at.isoformat() if conn and conn.token_expires_at else None
        )
    except Exception as e:
        logger.error(f"Error status-main: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado")

class UnifiedConnectResponse(BaseModel):
    token: str
    qr_code_base64: str
    telegram_link: str
    expires_in_seconds: int

@router.post("/connect-main", response_model=UnifiedConnectResponse)
async def connect_main(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            raise HTTPException(status_code=503, detail="Bot de Telegram no configurado")

        # Generar/actualizar conexión y token (expira en 3 minutos)
        token = uuid.uuid4().hex
        expires_at = datetime.utcnow() + timedelta(minutes=3)

        conn = db.query(TelegramConnection).filter(TelegramConnection.user_id == current_user.id).first()
        if not conn:
            conn = TelegramConnection(user_id=current_user.id)
            db.add(conn)
        conn.token = token
        conn.token_expires_at = expires_at
        conn.connected = bool(conn.chat_id)
        db.commit()
        db.refresh(conn)

        # Construir link
        bot_username = os.getenv('TELEGRAM_BOT_USERNAME', '').replace('@','')
        telegram_link = f"https://t.me/{bot_username}?start={token}" if bot_username else f"tg://resolve?domain=&start={token}"

        # QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(telegram_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        return UnifiedConnectResponse(
            token=token,
            qr_code_base64=qr_base64,
            telegram_link=telegram_link,
            expires_in_seconds=int((expires_at - datetime.utcnow()).total_seconds())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connect-main: {e}")
        raise HTTPException(status_code=500, detail="Error generando conexión")

class ValidateMainRequest(BaseModel):
    token: str
    chat_id: str

@router.post("/validate-main")
async def validate_main(req: ValidateMainRequest, db: Session = Depends(get_db)):
    try:
        conn = db.query(TelegramConnection).filter(
            TelegramConnection.token == req.token
        ).first()
        if not conn:
            return {"valid": False, "message": "Token inválido"}
        if conn.token_expires_at and datetime.utcnow() > conn.token_expires_at:
            return {"valid": False, "message": "Token expirado"}

        conn.chat_id = req.chat_id
        conn.connected = True
        conn.connected_at = datetime.utcnow()
        # invalidar token tras usarlo
        conn.token = None
        conn.token_expires_at = None
        db.commit()

        return {"valid": True, "user_id": conn.user_id, "message": "Conexión verificada"}
    except Exception as e:
        logger.error(f"Error validate-main: {e}")
        raise HTTPException(status_code=500, detail="Error validando token")

class RevokeRequest(BaseModel):
    user_id: int

@router.post("/admin/revoke")
async def admin_revoke(req: RevokeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        conn = db.query(TelegramConnection).filter(TelegramConnection.user_id == req.user_id).first()
        if not conn:
            return {"message": "No existe conexión"}
        conn.connected = False
        conn.revoked_at = datetime.utcnow()
        conn.revoked_by_user_id = current_user.id
        conn.chat_id = None
        db.commit()
        return {"message": "Conexión revocada"}
    except Exception as e:
        logger.error(f"Error admin_revoke: {e}")
        raise HTTPException(status_code=500, detail="Error revocando conexión")

@router.get("/admin/connections")
async def admin_list_connections(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        conns = db.query(TelegramConnection).order_by(TelegramConnection.connected.desc(), TelegramConnection.created_at.desc()).all()
        return {
            "total": len(conns),
            "connections": [
                {
                    "id": c.id,
                    "user_id": c.user_id,
                    "chat_id": c.chat_id,
                    "connected": c.connected,
                    "connected_at": c.connected_at.isoformat() if c.connected_at else None,
                    "token_expires_at": c.token_expires_at.isoformat() if c.token_expires_at else None,
                    "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                } for c in conns
            ]
        }
    except Exception as e:
        logger.error(f"Error list connections: {e}")
        raise HTTPException(status_code=500, detail="Error listando conexiones")

@router.post("/admin/force-disconnect")
async def admin_force_disconnect(req: RevokeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        conn = db.query(TelegramConnection).filter(TelegramConnection.user_id == req.user_id).first()
        if not conn:
            return {"message": "No existe conexión"}
        # Intento opcional de notificación
        try:
            if os.getenv('TELEGRAM_BOT_TOKEN') and conn.chat_id:
                requests.post(
                    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                    json={"chat_id": conn.chat_id, "text": "🔌 Tu conexión ha sido desconectada por el administrador."},
                    timeout=5
                )
        except Exception:
            pass
        conn.connected = False
        conn.chat_id = None
        conn.revoked_at = datetime.utcnow()
        conn.revoked_by_user_id = current_user.id
        db.commit()
        return {"message": "Usuario desconectado"}
    except Exception as e:
        logger.error(f"Error force-disconnect: {e}")
        raise HTTPException(status_code=500, detail="Error forzando desconexión")

@router.get("/alert-sender-status")
async def get_alert_sender_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        from app.telegram.alert_sender import alert_sender
        
        # Obtener métricas básicas
        pending_events = db.query(TradingEvent).filter(TradingEvent.status == 'PENDING').count()
        sent_today = db.query(TradingEvent).filter(
            TradingEvent.status == 'SENT',
            TradingEvent.processed_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Obtener usuarios conectados
        connected_users = db.query(TelegramConnection).filter(
            TelegramConnection.connected == True,
            TelegramConnection.chat_id.isnot(None)
        ).count()
        
        # Solo mostrar errores si es admin
        errors = []
        if current_user.is_admin:
            recent_errors = db.query(TradingEvent).filter(
                TradingEvent.status == 'FAILED',
                TradingEvent.processed_at >= datetime.now() - timedelta(hours=24)
            ).order_by(TradingEvent.processed_at.desc()).limit(10).all()
            
            errors = [{"id": e.id, "message": e.error_message, "created_at": e.created_at.isoformat()} for e in recent_errors]
        
        return {
            "is_running": alert_sender.is_running,
            "last_check": alert_sender.last_check.isoformat() if alert_sender.last_check else None,
            "pending_events": pending_events,
            "sent_today": sent_today,
            "connected_users": connected_users,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado AlertSender: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado")

@router.get("/admin/alert-sender-status")
async def get_alert_sender_status_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Solo administradores")
    try:
        from app.telegram.alert_sender import alert_sender
        
        # Obtener métricas básicas
        pending_events = db.query(TradingEvent).filter(TradingEvent.status == 'PENDING').count()
        sent_today = db.query(TradingEvent).filter(
            TradingEvent.status == 'SENT',
            TradingEvent.processed_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Últimos errores
        recent_errors = db.query(TradingEvent).filter(
            TradingEvent.status == 'FAILED',
            TradingEvent.processed_at >= datetime.now() - timedelta(hours=24)
        ).order_by(TradingEvent.processed_at.desc()).limit(10).all()
        
        errors = [{"id": e.id, "message": e.error_message, "created_at": e.created_at.isoformat()} for e in recent_errors]
        
        # Obtener usuarios conectados
        connected_users = db.query(TelegramConnection).filter(
            TelegramConnection.connected == True,
            TelegramConnection.chat_id.isnot(None)
        ).count()
        
        return {
            "is_running": alert_sender.is_running,
            "last_check": alert_sender.last_check.isoformat() if alert_sender.last_check else None,
            "pending_events": pending_events,
            "sent_today": sent_today,
            "connected_users": connected_users,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado AlertSender: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado")

@router.post("/disconnect-main")
async def disconnect_main(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        conn = db.query(TelegramConnection).filter(TelegramConnection.user_id == current_user.id).first()
        if conn:
            conn.connected = False
            conn.chat_id = None
            conn.revoked_at = datetime.utcnow()
            db.commit()
        return {"message": "Desconectado correctamente"}
    except Exception as e:
        logger.error(f"Error disconnect-main: {e}")
        raise HTTPException(status_code=500, detail="Error desconectando")

@router.post("/send-test-alert")
async def send_test_alert(
    alert_data: SendAlertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verificar feature flag
        if not os.getenv('TELEGRAM_ALERTS_ENABLED', 'false').lower() in ('true', '1', 'yes'):
            raise HTTPException(status_code=503, detail="Alertas de Telegram deshabilitadas")
            
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            raise HTTPException(status_code=503, detail="Bot de Telegram no configurado")
        
        # Buscar conexión del usuario
        conn = db.query(TelegramConnection).filter(
            TelegramConnection.user_id == current_user.id,
            TelegramConnection.connected == True,
            TelegramConnection.chat_id.isnot(None)
        ).first()
        
        if not conn:
            raise HTTPException(status_code=400, detail="Usuario no conectado a Telegram")
        
        # Enviar mensaje de prueba
        import requests
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
        payload = {
            'chat_id': conn.chat_id,
            'text': f"🧪 **Alerta de Prueba**\n\n{alert_data.message}\n\n📊 Símbolo: {alert_data.symbol}\n💰 Precio: ${alert_data.price or 'N/A'}\n🕒 {datetime.now().strftime('%H:%M:%S')}",
            'parse_mode': 'Markdown'
        }
        
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return {"message": "Alerta de prueba enviada correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error enviando mensaje")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error send-test-alert: {e}")
        raise HTTPException(status_code=500, detail="Error enviando alerta de prueba")

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
        
        # Obtener bot específico para verificar configuración
        crypto_for_bot = crypto.lower()
        if crypto_for_bot == "btc":
            crypto_for_bot = "bitcoin"
        elif crypto_for_bot == "eth":
            crypto_for_bot = "ethereum"
        
        # Con un solo bot, leemos de env TELEGRAM_BOT_TOKEN
        bot_configured = True if os.getenv('TELEGRAM_BOT_TOKEN') else False
        
        # Usuario está conectado si está subscrito Y tiene chat_id
        connected = bool(subscribed and chat_id)
        
        return TelegramStatusResponse(
            connected=connected,
            chat_id=chat_id,
            subscription_status=current_user.subscription_status,
            bot_configured=bot_configured
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
        # Validar que el único bot está configurado
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Bot de Telegram no configurado en el servidor"
            )
        
        # Obtener o generar token único para esta crypto
        telegram_token = crud_users.get_or_create_telegram_token_crypto(db, current_user.id, crypto)
        if not telegram_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener información del token incluyendo expiración
        token_info = crud_users.get_telegram_token_info_crypto(db, current_user.id, crypto)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo obtener información del token"
            )
        
        # Crear link de Telegram con el bot específico
        # En modo single bot no conocemos username por API; usamos link genérico si se configuró TELEGRAM_BOT_USERNAME opcional
        bot_username = os.getenv('TELEGRAM_BOT_USERNAME', '').replace('@','')
        telegram_link = f"https://t.me/{bot_username}?start={telegram_token}" if bot_username else f"tg://resolve?domain=&start={telegram_token}"
        
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
            expires_in_seconds=token_info["expires_in_seconds"],
            expires_in_minutes=3,
            created_at=token_info.get("created_at").isoformat() if token_info.get("created_at") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando conexión de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno generando código de conexión"
        )

@router.post("/regenerate-token", response_model=TelegramConnectionResponse)
async def regenerate_telegram_token(
    crypto: str = "btc",  # Parámetro para especificar la crypto
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenera un nuevo token de Telegram para una crypto específica"""
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
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Bot de Telegram no configurado en el servidor"
            )
        
        # Regenerar token para esta crypto
        telegram_token = crud_users.regenerate_telegram_token_crypto(db, current_user.id, crypto)
        if not telegram_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener información del token incluyendo expiración
        token_info = crud_users.get_telegram_token_info_crypto(db, current_user.id, crypto)
        if not token_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se pudo obtener información del token"
            )
        
        # Crear link de Telegram con el bot específico
        bot_username = os.getenv('TELEGRAM_BOT_USERNAME', '').replace('@','')
        telegram_link = f"https://t.me/{bot_username}?start={telegram_token}" if bot_username else f"tg://resolve?domain=&start={telegram_token}"
        
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
            expires_in_seconds=token_info["expires_in_seconds"],
            expires_in_minutes=3,
            created_at=token_info.get("created_at").isoformat() if token_info.get("created_at") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerando token de Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno regenerando token"
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
                    "bitcoin_chat_id": user.telegram_chat_id_btc,
                    "ethereum_chat_id": user.telegram_chat_id_eth,
                    "bnb_chat_id": user.telegram_chat_id_bnb,
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
    """Endpoint genérico para webhooks (fallback)"""
    return await process_webhook_generic(request, "generic")

@router.post("/webhook/bitcoin")
async def telegram_webhook_bitcoin(request: Request):
    """Endpoint específico para el bot de Bitcoin"""
    return await process_webhook_generic(request, "bitcoin")

@router.post("/webhook/ethereum") 
async def telegram_webhook_ethereum(request: Request):
    """Endpoint específico para el bot de Ethereum"""
    return await process_webhook_generic(request, "ethereum")

@router.post("/webhook/bnb")
async def telegram_webhook_bnb(request: Request):
    """Endpoint específico para el bot de BNB"""
    return await process_webhook_generic(request, "bnb")

@router.post("/webhook/health")
async def telegram_webhook_health(request: Request):
    """Endpoint específico para el bot de Health"""
    return await process_webhook_generic(request, "health")

async def process_webhook_generic(request: Request, crypto_type: str) -> dict:
    """Procesa webhook con el tipo de crypto específico"""
    try:
        # Obtener los datos del webhook
        update_data = await request.json()
        logger.info(f"Webhook {crypto_type} recibido: {update_data}")
        
        # Obtener el token correcto según el tipo
        import os
        token_map = {
            "bitcoin": os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN'),
            "ethereum": os.getenv('TELEGRAM_ETHEREUM_BOT_TOKEN'),
            "bnb": os.getenv('TELEGRAM_BNB_BOT_TOKEN'), 
            "health": os.getenv('TELEGRAM_HEALTH_BOT_TOKEN'),
            "generic": os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN')  # fallback
        }
        
        bot_token = token_map.get(crypto_type)
        if not bot_token:
            logger.error(f"Token no encontrado para {crypto_type}")
            return {"status": "error", "message": "Bot no configurado"}
        
        # Procesar mensaje con el bot correcto
        if 'message' in update_data:
            message = update_data['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '')
            
            # Procesar comandos con el bot específico
            result = await process_crypto_bot_message(update_data, chat_id, text, bot_token, crypto_type)
            return result
        
        return {"status": "ok", "message": "Webhook procesado"}
        
    except Exception as e:
        logger.error(f"Error procesando webhook {crypto_type}: {e}")
        return {"status": "error", "message": str(e)}

def detect_bot_from_request(request: Request) -> str:
    """Detecta qué bot envió el mensaje basado en la URL o headers"""
    try:
        import os
        
        # Por ahora, como todos usan el mismo webhook, necesitamos otra estrategia
        # Podríamos usar diferentes endpoints por bot, pero mientras tanto
        # retornamos el token de Bitcoin por defecto
        # TODO: Implementar URLs específicas por bot
        
        # Verificar qué bots están configurados y retornar el primero
        tokens = {
            'bitcoin': os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN'),
            'ethereum': os.getenv('TELEGRAM_ETHEREUM_BOT_TOKEN'), 
            'bnb': os.getenv('TELEGRAM_BNB_BOT_TOKEN'),
            'health': os.getenv('TELEGRAM_HEALTH_BOT_TOKEN')
        }
        
        # Por ahora retornar el de bitcoin, pero esto necesita mejorarse
        return tokens['bitcoin']
        
    except Exception as e:
        logger.error(f"Error detectando bot: {e}")
        return None

async def process_crypto_bot_message(update_data: dict, chat_id: str, text: str, bot_token: str, crypto_type: str = "bitcoin") -> dict:
    """Procesa mensajes de los bots crypto"""
    try:
        from app.telegram.crypto_bots import crypto_bots
        
        # Comandos principales
        if text.startswith('/start'):
            return handle_start_command(chat_id, text, bot_token, crypto_type)
        elif text.startswith('/status'):
            return handle_status_command(chat_id, bot_token, crypto_type)
        elif text.startswith('/disconnect'):
            return handle_disconnect_command(chat_id, bot_token, crypto_type)
        elif text.startswith('/help'):
            return handle_help_command(chat_id, bot_token, crypto_type)
        else:
            # Comando no reconocido
            return send_message_with_bot(chat_id, "Comando no reconocido. Usa /help para ver comandos disponibles.", bot_token)
            
    except Exception as e:
        logger.error(f"Error procesando mensaje crypto bot: {e}")
        return {"status": "error", "message": str(e)}

def handle_start_command(chat_id: str, text: str, bot_token: str, crypto_type: str) -> dict:
    """Maneja el comando /start"""
    try:
        # Extraer token de conexión si existe
        parts = text.split(' ')
        if len(parts) > 1:
            connection_token = parts[1]
            # Procesar conexión con token
            return process_connection_token(chat_id, connection_token, bot_token, crypto_type)
        else:
            # Mensaje de bienvenida
            message = """🤖 ¡Bienvenido a BotU!

Para conectar tu cuenta:
1. Ve a la aplicación web
2. Genera un código QR en la sección de Telegram
3. Escanéalo o usa el link que te proporciona

Comandos disponibles:
/status - Ver tu estado de conexión
/help - Ver esta ayuda"""
            return send_message_with_bot(chat_id, message, bot_token)
            
    except Exception as e:
        logger.error(f"Error en comando start: {e}")
        return {"status": "error", "message": str(e)}

def handle_status_command(chat_id: str, bot_token: str, crypto_type: str) -> dict:
    """Maneja el comando /status"""
    try:
        # Buscar usuario por chat_id en cualquier crypto  
        from app.db.database import SessionLocal
        session = SessionLocal()
        try:
            from app.db.models import User
            
            user = session.query(User).filter(
                (User.telegram_chat_id_btc == chat_id) |
                (User.telegram_chat_id_eth == chat_id) |
                (User.telegram_chat_id_bnb == chat_id)
            ).first()
            
            if user:
                # Determinar qué crypto está usando
                crypto_type = "desconocido"
                if user.telegram_chat_id_btc == chat_id:
                    crypto_type = "Bitcoin ₿"
                elif user.telegram_chat_id_eth == chat_id:
                    crypto_type = "Ethereum Ξ"
                elif user.telegram_chat_id_bnb == chat_id:
                    crypto_type = "BNB 🟡"
                
                message = f"""✅ *Cuenta conectada*

👤 Usuario: {user.username}
📱 Bot: {crypto_type}
📊 Suscripción: {user.subscription_status}
🔔 Alertas: {'Activas' if user.telegram_subscribed_btc or user.telegram_subscribed_eth or user.telegram_subscribed_bnb else 'Inactivas'}

¡Todo funcionando correctamente! 🚀"""
            else:
                message = """❌ *No tienes una cuenta conectada*

Para conectar tu cuenta:
1. Ve a la aplicación web BotU
2. Inicia sesión con tu cuenta
3. Ve a la sección de Telegram  
4. Genera un código QR y escanéalo

¿No tienes cuenta? Regístrate en la aplicación web."""
            
            return send_message_with_bot(chat_id, message, bot_token)
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error en comando status: {e}")
        return {"status": "error", "message": str(e)}

def handle_help_command(chat_id: str, bot_token: str, crypto_type: str) -> dict:
    """Maneja el comando /help"""
    message = """*Comandos BotU*

/start - Iniciar o conectar cuenta
/status - Ver estado de tu conexión
/disconnect - Desconectar tu cuenta
/help - Ver esta ayuda

*Como usar?*
1. Conecta tu cuenta desde la app web
2. Recibiras alertas automaticas de trading
3. Usa /status para verificar tu conexion
4. Usa /disconnect para desconectar cuando quieras

*Aplicacion web*
Inicia sesion en tu navegador para gestionar alertas y configuracion."""
    
    return send_message_with_bot(chat_id, message, bot_token)

def handle_disconnect_command(chat_id: str, bot_token: str, crypto_type: str) -> dict:
    """Maneja el comando /disconnect"""
    try:
        from app.db.database import SessionLocal
        session = SessionLocal()
        try:
            from app.db.models import User
            
            # Buscar usuario por chat_id en cualquier crypto
            user = session.query(User).filter(
                (User.telegram_chat_id_btc == chat_id) |
                (User.telegram_chat_id_eth == chat_id) |
                (User.telegram_chat_id_bnb == chat_id)
            ).first()
            
            if not user:
                return send_message_with_bot(chat_id, "No tienes una cuenta conectada.", bot_token)
            
            # Determinar qué crypto está usando y desconectarla
            disconnected_crypto = None
            if user.telegram_chat_id_btc == chat_id:
                user.telegram_chat_id_btc = None
                user.telegram_subscribed_btc = False
                disconnected_crypto = "Bitcoin"
            elif user.telegram_chat_id_eth == chat_id:
                user.telegram_chat_id_eth = None
                user.telegram_subscribed_eth = False
                disconnected_crypto = "Ethereum"
            elif user.telegram_chat_id_bnb == chat_id:
                user.telegram_chat_id_bnb = None
                user.telegram_subscribed_bnb = False
                disconnected_crypto = "BNB"
            
            session.commit()
            
            message = f"*Cuenta desconectada exitosamente*\n\nTu cuenta ha sido desconectada del bot de {disconnected_crypto}.\n\nPuedes volver a conectarte en cualquier momento desde la aplicacion web."
            return send_message_with_bot(chat_id, message, bot_token)
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error en comando disconnect: {e}")
        return {"status": "error", "message": str(e)}

def process_connection_token(chat_id: str, token: str, bot_token: str, crypto_type: str) -> dict:
    """Procesa un token de conexión crypto-específico"""
    try:
        # Normalizar crypto para validación
        crypto_db = crypto_type.lower()
        if crypto_db == "bitcoin":
            crypto_db = "btc"
        elif crypto_db == "ethereum":
            crypto_db = "eth"
        # bnb se mantiene como bnb
        
        # Usar el nuevo sistema crypto-específico con validación de expiración
        from app.db.database import SessionLocal
        session = SessionLocal()
        try:
            # Buscar usuario por token crypto-específico y verificar expiración
            user = crud_users.get_user_by_telegram_token_crypto(session, token, crypto_db)
            if not user:
                return send_message_with_bot(chat_id, "❌ Token de conexión inválido o expirado. Genera uno nuevo desde la aplicación web.", bot_token)
            
            if not user.is_active:
                return send_message_with_bot(chat_id, "❌ Usuario inactivo. Contacta al administrador.", bot_token)
            
            # Verificar si el token no ha expirado (3 minutos)
            token_info = crud_users.get_telegram_token_info_crypto(session, user.id, crypto_db)
            if not token_info or token_info.get("expired", True):
                return send_message_with_bot(chat_id, "❌ Token de conexión expirado. Genera uno nuevo desde la aplicación web.", bot_token)
            
            # Conectar al crypto específico según el bot
            crypto_updated = crud_users.update_telegram_subscription_crypto(session, user.id, chat_id, crypto_db, True)
            if not crypto_updated:
                return send_message_with_bot(chat_id, "❌ Error conectando la cuenta. Intenta nuevamente.", bot_token)
            
            crypto_name = get_crypto_display_name(crypto_type)
            return send_message_with_bot(chat_id, f"✅ ¡Cuenta conectada exitosamente!\n\n👤 Usuario: {user.username}\n🤖 Bot: {crypto_name}\n\n¡Ya puedes recibir alertas de trading!", bot_token)
                    
        finally:
            session.close()
        
    except Exception as e:
        logger.error(f"Error procesando token de conexión crypto: {e}")
        return send_message_with_bot(chat_id, "❌ Error interno del servidor. Intenta nuevamente.", bot_token)

def send_message_with_bot(chat_id: str, message: str, bot_token: str) -> dict:
    """Envía mensaje usando el bot específico"""
    try:
        if not bot_token:
            return {"status": "error", "message": "Token de bot no proporcionado"}
            
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            return {"status": "ok", "message": "Mensaje enviado"}
        else:
            logger.error(f"Error enviando mensaje: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"Error HTTP: {response.status_code}"}
        
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return {"status": "error", "message": str(e)}

def get_crypto_display_name(crypto_type: str) -> str:
    """Obtiene el nombre de display para cada crypto"""
    names = {
        'bitcoin': 'Bitcoin ₿',
        'ethereum': 'Ethereum Ξ', 
        'bnb': 'BNB 🟡',
        'health': 'Health Monitor 🏥'
    }
    return names.get(crypto_type, crypto_type.title())

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