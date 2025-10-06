# backend/app/api/v1/debug_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.core.auth import get_current_user

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/telegram-users")
async def get_telegram_users_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug: Ver estado de conexiones de Telegram de todos los usuarios"""
    
    if not current_user.is_admin:
        return {"error": "Solo admins pueden ver este debug"}
    
    users = db.query(User).all()
    user_status = []
    
    for user in users:
        user_info = {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "subscription_status": user.subscription_status,
            "telegram_connections": {
                "bitcoin": {
                    "chat_id": user.telegram_chat_id_btc,
                    "subscribed": user.telegram_subscribed_btc
                },
                "ethereum": {
                    "chat_id": user.telegram_chat_id_eth,
                    "subscribed": user.telegram_subscribed_eth
                },
                "bnb": {
                    "chat_id": user.telegram_chat_id_bnb,
                    "subscribed": user.telegram_subscribed_bnb
                }
            }
        }
        user_status.append(user_info)
    
    return {
        "total_users": len(users),
        "users": user_status
    }

@router.post("/fix-telegram-connection")
async def fix_telegram_connection(
    crypto: str,
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fix: Reparar conexión de Telegram manualmente"""
    
    if not current_user.is_admin:
        return {"error": "Solo admins pueden usar este fix"}
    
    # Mapear crypto a campos del modelo
    chat_id_field = f"telegram_chat_id_{crypto}"
    subscribed_field = f"telegram_subscribed_{crypto}"
    
    try:
        # Actualizar base de datos directamente
        setattr(current_user, chat_id_field, chat_id)
        setattr(current_user, subscribed_field, True)
        current_user.subscription_status = 'active'
        
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": f"Conexión {crypto} reparada para usuario {current_user.username}",
            "chat_id": chat_id,
            "crypto": crypto
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/setup-webhook")
async def setup_webhook(
    crypto: str,
    current_user: User = Depends(get_current_user)
):
    """Setup: Configurar webhook para un bot específico"""
    
    if not current_user.is_admin:
        return {"error": "Solo admins pueden configurar webhooks"}
    
    import os
    import requests
    
    # Obtener token según crypto
    token_map = {
        "bitcoin": os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN'),
        "ethereum": os.getenv('TELEGRAM_ETHEREUM_BOT_TOKEN'), 
        "bnb": os.getenv('TELEGRAM_BNB_BOT_TOKEN')
    }
    
    token = token_map.get(crypto)
    if not token:
        return {"error": f"Token de {crypto} no configurado"}
    
    # URL del webhook (telegram_routes tiene prefix="/telegram")
    webhook_url = f"https://api.botut.net/telegram/webhook/{crypto}"
    
    try:
        # Configurar webhook en Telegram
        telegram_api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(telegram_api_url, json=payload, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            return {
                "success": True,
                "message": f"Webhook {crypto} configurado correctamente",
                "webhook_url": webhook_url,
                "telegram_response": result
            }
        else:
            return {
                "success": False,
                "error": result
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }