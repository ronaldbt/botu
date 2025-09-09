# backend/app/api/v1/alertas_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.db import crud_alertas, crud_users
from app.schemas.alerta_schema import AlertaCreate, AlertaResponse, AlertaUpdate
from app.core.auth import get_current_user
from app.db.models import User
from app.telegram.telegram_bot import telegram_bot
import logging

router = APIRouter(prefix="/alertas", tags=["alertas"])
logger = logging.getLogger(__name__)

# Schemas adicionales para alertas Telegram
class TelegramAlertCreate(BaseModel):
    tipo_alerta: str  # 'BUY', 'SELL', 'INFO', 'WARNING'
    ticker: str = "BTCUSDT"
    mensaje: str
    precio_actual: Optional[float] = None
    nivel_ruptura: Optional[float] = None
    send_to_telegram: bool = True
    user_ids: Optional[List[int]] = None  # Si None, envía a todos los usuarios activos

class BroadcastResponse(BaseModel):
    alerta_id: int
    telegram_sent: int
    telegram_failed: int
    total_targets: int
    message: str

@router.post("/", response_model=AlertaResponse)
def create_alerta(
    alerta: AlertaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva alerta"""
    return crud_alertas.create_alerta(db=db, alerta=alerta, usuario_id=current_user.id)

@router.get("/", response_model=List[AlertaResponse])
def get_alertas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ticker: Optional[str] = Query(None),
    tipo_alerta: Optional[str] = Query(None),
    leida: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de alertas con filtros opcionales"""
    return crud_alertas.get_alertas(db=db, skip=skip, limit=limit, ticker=ticker, tipo_alerta=tipo_alerta, leida=leida)

@router.get("/{alerta_id}", response_model=AlertaResponse)
def get_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener una alerta específica por ID"""
    alerta = crud_alertas.get_alerta(db=db, alerta_id=alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta

@router.put("/{alerta_id}", response_model=AlertaResponse)
def update_alerta(
    alerta_id: int,
    alerta_update: AlertaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una alerta"""
    alerta = crud_alertas.update_alerta(db=db, alerta_id=alerta_id, alerta_update=alerta_update)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta

@router.delete("/{alerta_id}")
def delete_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar una alerta"""
    alerta = crud_alertas.delete_alerta(db=db, alerta_id=alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta eliminada exitosamente"}

@router.get("/no-leidas/", response_model=List[AlertaResponse])
def get_alertas_no_leidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas no leídas"""
    return crud_alertas.get_alertas_no_leidas(db=db)

@router.post("/marcar-leidas/")
def marcar_alertas_como_leidas(
    alerta_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar múltiples alertas como leídas"""
    crud_alertas.marcar_alertas_como_leidas(db=db, alerta_ids=alerta_ids)
    return {"message": f"{len(alerta_ids)} alertas marcadas como leídas"}

@router.get("/ticker/{ticker}", response_model=List[AlertaResponse])
def get_alertas_por_ticker(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas de un ticker específico"""
    return crud_alertas.get_alertas_por_ticker(db=db, ticker=ticker)

@router.get("/usuario/mis-alertas", response_model=List[AlertaResponse])
def get_mis_alertas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas del usuario actual"""
    return crud_alertas.get_alertas_por_usuario(db=db, usuario_id=current_user.id)

# Endpoints profesionales para Telegram
@router.post("/telegram/broadcast", response_model=BroadcastResponse)
def create_and_broadcast_alert(
    alerta_data: TelegramAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una alerta y enviarla por Telegram con validaciones profesionales"""
    try:
        # Crear alerta en la base de datos
        alerta_create = AlertaCreate(
            ticker=alerta_data.ticker,
            tipo_alerta=alerta_data.tipo_alerta,
            mensaje=alerta_data.mensaje,
            precio_actual=alerta_data.precio_actual,
            nivel_ruptura=alerta_data.nivel_ruptura,
            usuario_id=current_user.id
        )
        
        alerta = crud_alertas.create_alerta(db=db, alerta=alerta_create, usuario_id=current_user.id)
        
        telegram_sent = 0
        telegram_failed = 0
        total_targets = 0
        
        # Enviar por Telegram si está habilitado
        if alerta_data.send_to_telegram and telegram_bot.is_configured():
            
            # Preparar datos para Telegram
            telegram_alert_data = {
                'type': alerta_data.tipo_alerta,
                'symbol': alerta_data.ticker,
                'price': alerta_data.precio_actual or 0,
                'message': alerta_data.mensaje
            }
            
            if alerta_data.user_ids:
                # Envío específico a usuarios
                if not current_user.is_admin:
                    raise HTTPException(
                        status_code=403,
                        detail="Solo administradores pueden enviar alertas a usuarios específicos"
                    )
                
                # Validar que los usuarios están activos y suscritos
                active_users = []
                for user_id in alerta_data.user_ids:
                    user = crud_users.get_user(db, user_id)
                    if (user and user.is_active and user.telegram_subscribed and 
                        user.subscription_status == 'active' and user.telegram_chat_id):
                        active_users.append(user_id)
                        
                total_targets = len(active_users)
                
                for user_id in active_users:
                    if telegram_bot.send_bitcoin_alert(user_id, telegram_alert_data):
                        telegram_sent += 1
                    else:
                        telegram_failed += 1
                        
            else:
                # Broadcast a todos los usuarios activos
                broadcast_result = telegram_bot.broadcast_alert(telegram_alert_data)
                telegram_sent = broadcast_result.get('sent', 0)
                telegram_failed = broadcast_result.get('failed', 0)
                total_targets = broadcast_result.get('total_targets', 0)
            
            logger.info(
                f"Alerta {alerta.id} enviada: {telegram_sent} exitosos, "
                f"{telegram_failed} fallidos de {total_targets} usuarios"
            )
        
        return BroadcastResponse(
            alerta_id=alerta.id,
            telegram_sent=telegram_sent,
            telegram_failed=telegram_failed,
            total_targets=total_targets,
            message=f"Alerta creada y enviada a {telegram_sent}/{total_targets} usuarios"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando/enviando alerta: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/telegram/active-subscribers")
def get_active_telegram_subscribers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de suscriptores activos de Telegram (solo para admins)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden ver estadísticas"
            )
        
        active_users = crud_users.get_active_telegram_users(db)
        
        return {
            "total_active_subscribers": len(active_users),
            "bot_configured": telegram_bot.is_configured(),
            "subscribers": [
                {
                    "user_id": user.id,
                    "username": user.username,
                    "subscription_status": user.subscription_status,
                    "last_activity": user.last_activity,
                    "has_chat_id": bool(user.telegram_chat_id)
                }
                for user in active_users
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo suscriptores activos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/telegram/test-broadcast")
def test_telegram_broadcast(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enviar alerta de prueba a todos los suscriptores activos (solo para admins)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden enviar alertas de prueba"
            )
        
        if not telegram_bot.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Bot de Telegram no configurado"
            )
        
        test_alert_data = {
            'type': 'INFO',
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'message': '🧪 ALERTA DE PRUEBA: Esta es una prueba del sistema de alertas BotU. Si recibes este mensaje, tu suscripción funciona correctamente!'
        }
        
        result = telegram_bot.broadcast_alert(test_alert_data)
        
        return {
            "message": "Alerta de prueba enviada",
            "sent": result.get('sent', 0),
            "failed": result.get('failed', 0),
            "total_targets": result.get('total_targets', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enviando alerta de prueba: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

