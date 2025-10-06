# backend/app/telegram/handlers/bitcoin_handler.py

import os
import requests
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_users

logger = logging.getLogger(__name__)

class BitcoinTelegramHandler:
    """Handler específico para el bot de Bitcoin de Telegram"""
    
    def __init__(self):
        self.crypto_type = "btc"
        self.crypto_name = "Bitcoin"
        self.crypto_symbol = "₿"
        self.crypto_display = "Bitcoin ₿"
        self.bot_token = os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN') 
        self.bot_username = "@BotuBitcoinBot"
        
    def handle_status_command(self, chat_id: str) -> Dict[str, Any]:
        """Maneja el comando /status específico para Bitcoin"""
        try:
            # Buscar usuario por chat_id Bitcoin
            db = SessionLocal()
            try:
                from app.db.models import User
                
                user = db.query(User).filter(
                    User.telegram_chat_id_btc == chat_id
                ).first()
                
                if user:
                    # Verificar suscripción a Bitcoin
                    is_subscribed = user.telegram_subscribed_btc or False
                    
                    message = f"""✅ *Cuenta conectada*

👤 Usuario: {user.username}
📱 Bot: {self.crypto_display}
📊 Suscripción: {user.subscription_status}
🔔 Alertas: {'Activas' if is_subscribed else 'Inactivas'}

¡Todo funcionando correctamente! 🚀"""
                    
                    return self._send_message(chat_id, message)
                else:
                    message = """❌ *No tienes una cuenta conectada*

Para conectar tu cuenta:
1. Ve a la aplicación web BotU
2. Inicia sesión con tu cuenta  
3. Ve a la sección Bitcoin Bot
4. Genera un código QR y escanéalo"""
                    
                    return self._send_message(chat_id, message)
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en Bitcoin status command: {e}")
            return {"status": "error", "message": str(e)}
    
    def _send_message(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Envía mensaje usando bot Bitcoin"""
        try:
            if not self.bot_token:
                logger.warning("⚠️ Bitcoin Bot token no configurado")
                return {"status": "error", "message": "Bot not configured"}
                
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📤 Bitcoin mensaje enviado a chat {chat_id}")
                return {"status": "ok", "message": "Message sent"}
            else:
                logger.error(f"❌ Error Bitcoin Bot: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Error en Bitcoin send_message: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_disconnect_command(self, chat_id: str) -> Dict[str, Any]:
        """Maneja el comando /disconnect específico para Bitcoin"""
        try:
            db = SessionLocal()
            try:
                from app.db.models import User
                
                # Buscar usuario por chat_id Bitcoin
                user = db.query(User).filter(
                    User.telegram_chat_id_btc == chat_id
                ).first()
                
                if user:
                    # Desconectar usuario de Bitcoin específicamente
                    user.telegram_subscribed_btc = False
                    user.telegram_chat_id_btc = None
                    db.commit()
                    
                    message = f"""❌ *Cuenta desconectada*

👤 Usuario: {user.username}
🤖 Bot: {self.crypto_display}

Ya no recibirás alertas de Bitcoin.

Para reconectarte:
1. Ve a la aplicación web BotU
2. Sección Bitcoin Bot
3. Genera un nuevo código QR"""
                    
                    return self._send_message(chat_id, message)
                else:
                    message = "❌ No tienes una cuenta conectada para desconectar."
                    return self._send_message(chat_id, message)
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en Bitcoin disconnect command: {e}")
            message = "❌ Error desconectando la cuenta. Intenta nuevamente."
            self._send_message(chat_id, message)
            return {"status": "error", "message": str(e)}

# Instancia global
bitcoin_handler = BitcoinTelegramHandler()
