# backend/app/telegram/handlers/bnb_handler.py

import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_users

logger = logging.getLogger(__name__)

class BnbTelegramHandler:
    """Handler específico para el bot de BNB de Telegram"""
    
    def __init__(self):
        self.crypto_type = "bnb"
        self.crypto_name = "BNB"
        self.crypto_symbol = "🟡"
        self.crypto_display = "BNB 🟡"
        self.bot_token = os.getenv('TELEGRAM_BNB_BOT_TOKEN')
        self.bot_username = "@BotuBnbBot"
        
    def is_configured(self) -> bool:
        """Verifica si el bot está configurado"""
        return bool(self.bot_token)
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Envía un mensaje usando el bot de BNB"""
        try:
            if not self.is_configured():
                logger.warning(f"⚠️ BNB Bot no configurado")
                return False
                
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📤 BNB mensaje enviado a chat {chat_id}")
                return True
            else:
                logger.error(f"❌ Error BNB Bot: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en BNB Bot send_message: {e}")
            return False
    
    def handle_status_command(self, chat_id: str, user_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Maneja el comando /status específico para BNB"""
        try:
            # Buscar usuario por chat_id
            db = SessionLocal()
            try:
                from app.db.models import User
                
                user = db.query(User).filter(
                    User.telegram_chat_id_bnb == chat_id
                ).first()
                
                if user:
                    # Verificar suscripción a BNB
                    is_subscribed = user.telegram_subscribed_bnb or False
                    
                    message = f"""✅ *Cuenta conectada*

👤 Usuario: {user.username}
📱 Bot: {self.crypto_display}
📊 Suscripción: {user.subscription_status}
🔔 Alertas: {'Activas' if is_subscribed else 'Inactivas'}

¡Todo funcionando correctamente! 🚀"""
                    
                    success = self.send_message(chat_id, message)
                    return {
                        "status": "ok" if success else "error",
                        "message": "Status sent" if success else "Failed to send status"
                    }
                else:
                    message = """❌ *No tienes una cuenta conectada*

Para conectar tu cuenta:
1. Ve a la aplicación web BotU
2. Inicia sesión con tu cuenta
3. Ve a la sección BNB Bot
4. Genera un código QR y escanéalo

¿No tienes cuenta? Regístrate en la aplicación web."""
                    
                    self.send_message(chat_id, message)
                    return {"status": "ok", "message": "User not connected"}
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en BNB status command: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_start_command(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Maneja el comando /start específico para BNB"""
        try:
            # Extraer token de conexión si existe
            parts = text.split(' ')
            if len(parts) > 1:
                connection_token = parts[1]
                return self._process_connection_token(chat_id, connection_token)
            else:
                # Mensaje de bienvenida
                message = f"""🟡 *BNB Bot - BotU*

¡Bienvenido al bot oficial de alertas de BNB!

Para conectar tu cuenta:
1. Ve a la aplicación web BotU  
2. Genera un código QR en la sección BNB Bot
3. Escanéalo o usa el link que te proporciona

Comandos disponibles:
/status - Ver tu estado de conexión
/help - Ver esta ayuda

🟡 Recibe alertas automáticas de patrones U en BNB"""
                
                success = self.send_message(chat_id, message)
                return {"status": "ok" if success else "error"}
                
        except Exception as e:
            logger.error(f"❌ Error en BNB start command: {e}")
            return {"status": "error", "message": str(e)}
    
    def handle_disconnect_command(self, chat_id: str) -> Dict[str, Any]:
        """Maneja el comando /disconnect específico para BNB"""
        try:
            db = SessionLocal()
            try:
                from app.db.models import User
                
                # Buscar usuario por chat_id BNB
                user = db.query(User).filter(
                    User.telegram_chat_id_bnb == chat_id
                ).first()
                
                if user:
                    # Desconectar usuario de BNB específicamente
                    user.telegram_subscribed_bnb = False
                    user.telegram_chat_id_bnb = None
                    db.commit()
                    
                    message = f"""❌ *Cuenta desconectada*

👤 Usuario: {user.username}
🤖 Bot: {self.crypto_display}

Ya no recibirás alertas de BNB.

Para reconectarte:
1. Ve a la aplicación web BotU
2. Sección BNB Bot
3. Genera un nuevo código QR"""
                    
                    success = self.send_message(chat_id, message)
                    return {"status": "ok" if success else "error", "message": "Disconnected successfully"}
                else:
                    message = "❌ No tienes una cuenta conectada para desconectar."
                    success = self.send_message(chat_id, message)
                    return {"status": "ok" if success else "error", "message": "No account connected"}
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en BNB disconnect command: {e}")
            message = "❌ Error desconectando la cuenta. Intenta nuevamente."
            self.send_message(chat_id, message)
            return {"status": "error", "message": str(e)}

    def handle_help_command(self, chat_id: str) -> Dict[str, Any]:
        """Maneja el comando /help específico para BNB"""
        message = f"""🟡 *BNB Bot - Ayuda*

🤖 *Comandos disponibles:*

/start - Iniciar o conectar cuenta
/status - Ver estado de tu conexión
/disconnect - Desconectar tu cuenta  
/help - Ver esta ayuda

📊 *Funciones:*
• Alertas de patrones U detectados en BNB
• Notificaciones de compra/venta automáticas
• Señales basadas en algoritmos probados
• Actualizaciones en tiempo real

🌐 *Aplicación web*
Gestiona tu cuenta y configuración en BotU

{self.bot_username} - Bot exclusivo para usuarios registrados"""
        
        success = self.send_message(chat_id, message)
        return {"status": "ok" if success else "error"}
    
    def _process_connection_token(self, chat_id: str, token: str) -> Dict[str, Any]:
        """Procesa un token de conexión específico para BNB"""
        try:
            db = SessionLocal()
            try:
                # Buscar usuario por token BNB específico
                user = crud_users.get_user_by_telegram_token_crypto(db, token, "bnb")
                if not user:
                    message = "❌ Token de conexión inválido o expirado. Genera uno nuevo desde la aplicación web."
                    self.send_message(chat_id, message)
                    return {"status": "error", "message": "Invalid token"}
                
                if not user.is_active:
                    message = "❌ Usuario inactivo. Contacta al administrador."
                    self.send_message(chat_id, message)
                    return {"status": "error", "message": "User inactive"}
                
                # Verificar si el token no ha expirado (3 minutos)
                token_info = crud_users.get_telegram_token_info_crypto(db, user.id, "bnb")
                if not token_info or token_info.get("expired", True):
                    message = "❌ Token de conexión expirado. Genera uno nuevo desde la aplicación web."
                    self.send_message(chat_id, message)
                    return {"status": "error", "message": "Token expired"}
                
                # Conectar usuario a BNB específicamente
                updated = crud_users.update_telegram_subscription_crypto(db, user.id, chat_id, "bnb", True)
                if not updated:
                    message = "❌ Error conectando la cuenta. Intenta nuevamente."
                    self.send_message(chat_id, message)
                    return {"status": "error", "message": "Connection failed"}
                
                message = f"""✅ ¡Cuenta conectada exitosamente!

👤 Usuario: {user.username}
🤖 Bot: {self.crypto_display}

¡Ya puedes recibir alertas de trading BNB!"""
                
                success = self.send_message(chat_id, message)
                return {"status": "ok" if success else "error", "message": "Connected successfully"}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando token de conexión BNB: {e}")
            message = "❌ Error interno del servidor. Intenta nuevamente."
            self.send_message(chat_id, message)
            return {"status": "error", "message": str(e)}
    
    def handle_webhook(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa webhook del bot BNB"""
        try:
            if 'message' not in update_data:
                return {"status": "ignored", "reason": "No message"}
            
            message = update_data['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            
            logger.info(f"BNB Bot procesando: {text} de chat {chat_id}")
            
            # Procesar comandos
            if text.startswith('/start'):
                return self.handle_start_command(chat_id, text)
            elif text.startswith('/status'):
                return self.handle_status_command(chat_id)
            elif text.startswith('/disconnect'):
                return self.handle_disconnect_command(chat_id)
            elif text.startswith('/help'):
                return self.handle_help_command(chat_id)
            else:
                message_text = "❓ Comando no reconocido. Usa /help para ver comandos disponibles."
                success = self.send_message(chat_id, message_text)
                return {"status": "ok" if success else "error", "message": "Unknown command"}
                
        except Exception as e:
            logger.error(f"❌ Error en BNB webhook: {e}")
            return {"status": "error", "error": str(e)}

# Instancia global del handler BNB
bnb_handler = BnbTelegramHandler()