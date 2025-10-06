# backend/app/telegram/telegram_bot.py

import os
import logging
import asyncio
import requests
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User
from app.db import crud_users
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.user_connections: Dict[int, str] = {}  # user_id -> telegram_chat_id
        self.pending_connections: Dict[str, Dict] = {}  # connection_code -> {user_id, expires_at}
        
        if not self.bot_token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado - Las notificaciones de Telegram estarán deshabilitadas")
        else:
            logger.info(f"✅ Telegram Bot inicializado correctamente")
            # Intentar configurar webhook automáticamente si está en desarrollo
            self._setup_webhook_if_needed()
    
    def is_configured(self) -> bool:
        """Verifica si el bot de Telegram está configurado"""
        return self.bot_token is not None and self.base_url is not None
    
    def generate_connection_code(self, user_id: int) -> tuple[str, str]:
        """
        Genera un código de conexión único para un usuario y devuelve el código y QR
        
        Returns:
            tuple: (connection_code, qr_code_base64)
        """
        if not self.is_configured():
            raise ValueError("Telegram Bot no está configurado")
        
        # Generar código único
        import uuid
        connection_code = str(uuid.uuid4())[:8].upper()
        
        # Guardar conexión pendiente (expira en 10 minutos)
        self.pending_connections[connection_code] = {
            'user_id': user_id,
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        
        # Crear enlace de bot de Telegram
        bot_username = self._get_bot_username()
        if not bot_username:
            raise ValueError("No se pudo obtener el username del bot de Telegram")
        
        # Comando para iniciar conexión
        telegram_link = f"https://t.me/{bot_username}?start={connection_code}"
        
        # Generar QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(telegram_link)
        qr.make(fit=True)
        
        # Crear imagen QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        logger.info(f"🔗 Código de conexión generado para usuario {user_id}: {connection_code}")
        
        return connection_code, qr_base64
    
    def _get_bot_username(self) -> Optional[str]:
        """Obtiene el username del bot de Telegram"""
        try:
            response = requests.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data['result']['username']
        except Exception as e:
            logger.error(f"Error obteniendo username del bot: {e}")
        return None
    
    def process_telegram_update(self, update: dict) -> dict:
        """
        Procesa una actualización de Telegram (webhook)
        
        Args:
            update: Datos del webhook de Telegram
            
        Returns:
            dict: Respuesta de procesamiento
        """
        try:
            if 'message' in update:
                message = update['message']
                chat_id = str(message['chat']['id'])
                text = message.get('text', '')
                
                # Procesar comando /start con token de conexión
                if text.startswith('/start '):
                    telegram_token = text.split(' ')[1]  # No usar upper() porque el token es case-sensitive
                    return self._handle_connection(chat_id, telegram_token)
                
                # Procesar otros comandos
                elif text == '/start':
                    return self._send_message(chat_id, 
                        "¡Hola! 👋\n\n" +
                        "Soy el Bitcoin Bot de BotU. Para conectar tu cuenta:\n\n" +
                        "1. Ve a la sección Bitcoin Bot en BotU\n" +
                        "2. Selecciona Modo Manual\n" +
                        "3. Escanea el código QR o usa el código de conexión\n\n" +
                        "¿Necesitas ayuda? Usa /help"
                    )
                elif text == '/help':
                    return self._send_message(chat_id,
                        "🤖 **Bitcoin Bot - Comandos disponibles:**\n\n" +
                        "/start - Iniciar bot\n" +
                        "/status - Ver estado de conexión\n" +
                        "/disconnect - Desconectar cuenta\n" +
                        "/help - Mostrar esta ayuda\n\n" +
                        "Para conectar tu cuenta, usa el código QR desde la aplicación BotU."
                    )
                elif text == '/status':
                    user_id = self._get_user_by_chat_id(chat_id)
                    if user_id:
                        return self._send_message(chat_id, "✅ Tu cuenta está conectada correctamente.")
                    else:
                        return self._send_message(chat_id, "❌ No tienes una cuenta conectada.")
                elif text == '/disconnect':
                    return self._handle_disconnect(chat_id)
                
            return {'status': 'ok', 'message': 'Actualización procesada'}
            
        except Exception as e:
            logger.error(f"Error procesando actualización de Telegram: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_connection(self, chat_id: str, telegram_token: str) -> dict:
        """Maneja la conexión de un usuario con token"""
        try:
            session = SessionLocal()
            try:
                # Validar token usando nuestro sistema
                user = crud_users.get_user_by_telegram_token(session, telegram_token)
                
                if not user:
                    return self._send_message(chat_id, 
                        "❌ Token de conexión inválido o expirado.\n\n" +
                        "Por favor genera un nuevo código QR desde la aplicación BotU."
                    )
                
                if not user.is_active:
                    return self._send_message(chat_id,
                        "❌ Tu cuenta está inactiva.\n\n" +
                        "Por favor contacta al administrador para reactivar tu cuenta."
                    )
                
                # Actualizar suscripción en la base de datos
                crud_users.update_telegram_subscription(session, user.id, chat_id, True)
                
                # También guardar en memoria para compatibilidad
                self.user_connections[user.id] = chat_id
                
                logger.info(f"✅ Usuario {user.id} ({user.username}) conectado a Telegram chat {chat_id}")
                
                return self._send_message(chat_id,
                    f"✅ **¡Conexión exitosa!**\n\n" +
                    f"Hola {user.username}, tu cuenta BotU está ahora conectada.\n\n" +
                    f"🔔 Recibirás alertas del Bitcoin Bot aquí cuando:\n" +
                    f"• Se detecte un patrón U en Bitcoin\n" +
                    f"• Se genere una señal de compra/venta\n" +
                    f"• Se ejecuten trades automáticamente\n\n" +
                    f"Usa /status para verificar tu conexión en cualquier momento."
                )
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error manejando conexión: {e}")
            return self._send_message(chat_id, "❌ Error interno. Intenta nuevamente más tarde.")
    
    def _handle_disconnect(self, chat_id: str) -> dict:
        """Desconecta un usuario del bot"""
        try:
            session = SessionLocal()
            try:
                # Buscar usuario en la base de datos
                user = crud_users.get_user_by_telegram_chat_id(session, chat_id)
                
                if user and user.telegram_subscribed:
                    # Desuscribir en la base de datos
                    crud_users.update_telegram_subscription(session, user.id, chat_id, False)
                    
                    # Remover de memoria
                    if user.id in self.user_connections:
                        del self.user_connections[user.id]
                    
                    logger.info(f"🔌 Usuario {user.id} ({user.username}) desconectado del chat {chat_id}")
                    return self._send_message(chat_id, "✅ Tu cuenta ha sido desconectada correctamente.")
                else:
                    return self._send_message(chat_id, "❌ No tienes una cuenta conectada.")
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error desconectando usuario: {e}")
            return self._send_message(chat_id, "❌ Error interno. Intenta nuevamente más tarde.")
    
    def _get_user_by_chat_id(self, chat_id: str) -> Optional[int]:
        """Busca el user_id por chat_id en la base de datos"""
        try:
            session = SessionLocal()
            try:
                user = crud_users.get_user_by_telegram_chat_id(session, chat_id)
                return user.id if user else None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error buscando usuario por chat_id: {e}")
            return None
    
    def _get_user_info(self, user_id: int) -> Optional[dict]:
        """Obtiene información del usuario desde la base de datos"""
        try:
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    return {
                        'username': user.username,
                        'is_admin': user.is_admin
                    }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error obteniendo información del usuario {user_id}: {e}")
        return None
    
    def _send_message(self, chat_id: str, text: str) -> dict:
        """Envía un mensaje a Telegram"""
        try:
            if not self.is_configured():
                return {'status': 'error', 'message': 'Bot no configurado'}
            
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(f"{self.base_url}/sendMessage", json=data)
            if response.status_code == 200:
                return {'status': 'ok', 'message': 'Mensaje enviado'}
            else:
                logger.error(f"Error enviando mensaje: {response.text}")
                return {'status': 'error', 'message': 'Error enviando mensaje'}
                
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_bitcoin_alert(self, user_id: int, alert_data: dict) -> bool:
        """
        Envía una alerta de Bitcoin a un usuario específico (con validación profesional)
        
        Args:
            user_id: ID del usuario
            alert_data: Datos de la alerta
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            if not self.is_configured():
                logger.warning("Telegram Bot no configurado - Alerta no enviada")
                return False
            
            session = SessionLocal()
            try:
                # Validar que el usuario está activo y suscrito
                user = crud_users.get_user(session, user_id)
                if not user:
                    logger.info(f"Usuario {user_id} no encontrado - Alerta no enviada")
                    return False
                
                if not user.is_active:
                    logger.info(f"Usuario {user_id} inactivo - Alerta no enviada")
                    return False
                
                if not user.telegram_subscribed or user.subscription_status != 'active':
                    logger.info(f"Usuario {user_id} no suscrito a Telegram - Alerta no enviada")
                    # Enviar mensaje de suscripción expirada
                    if user.telegram_chat_id:
                        self._send_message(
                            user.telegram_chat_id,
                            "⚠️ **Suscripción Expirada**\n\n"
                            "Tu suscripción a las alertas de BotU ha expirado.\n\n"
                            "Para seguir recibiendo alertas, renueva tu cuenta en: https://tu-app.com\n\n"
                            "¿Necesitas ayuda? Contacta soporte."
                        )
                    return False
                
                if not user.telegram_chat_id:
                    logger.info(f"Usuario {user_id} no tiene chat_id - Alerta no enviada")
                    return False
                
                # Actualizar última actividad
                crud_users.update_user_activity(session, user_id)
                
                chat_id = user.telegram_chat_id
                
                # Formatear mensaje de alerta
                alert_type = alert_data.get('type', 'INFO')
                symbol = alert_data.get('symbol', 'BTC')
                price = alert_data.get('price', 0)
                message_text = alert_data.get('message', 'Nueva alerta')
                
                emoji_map = {
                    'BUY': '🟢 📈',
                    'SELL': '🔴 📉',
                    'INFO': '🔵 ℹ️',
                    'WARNING': '🟡 ⚠️'
                }
                
                emoji = emoji_map.get(alert_type, '🔵')
                
                telegram_message = f"{emoji} **Bitcoin Bot Alert**\n\n"
                telegram_message += f"**{alert_type}** - {symbol}\n"
                telegram_message += f"💰 Precio: ${price:,.2f}\n\n"
                telegram_message += f"{message_text}\n\n"
                telegram_message += f"🕒 {datetime.now().strftime('%H:%M:%S')}"
                
                result = self._send_message(chat_id, telegram_message)
                
                if result.get('status') == 'ok':
                    logger.info(f"✅ Alerta Bitcoin enviada a usuario {user_id} ({user.username}) - chat: {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Error enviando alerta a usuario {user_id}: {result}")
                    return False
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error enviando alerta Bitcoin: {e}")
            return False
    
    def broadcast_alert(self, alert_data: dict, user_list: Optional[List[int]] = None) -> dict:
        """
        Envía una alerta a múltiples usuarios (sistema profesional con validación)
        
        Args:
            alert_data: Datos de la alerta
            user_list: Lista de user_ids (si None, envía a todos los usuarios activos)
            
        Returns:
            dict: Estadísticas del envío
        """
        try:
            if not self.is_configured():
                return {'sent': 0, 'failed': 0, 'message': 'Bot no configurado'}
            
            session = SessionLocal()
            try:
                # Si no se especifica lista, obtener todos los usuarios activos
                if user_list is None:
                    active_users = crud_users.get_active_telegram_users(session)
                    target_users = [user.id for user in active_users]
                    logger.info(f"📢 Broadcast a {len(target_users)} usuarios activos suscritos")
                else:
                    target_users = user_list
                    logger.info(f"📢 Broadcast a {len(target_users)} usuarios específicos")
                
                sent_count = 0
                failed_count = 0
                
                for user_id in target_users:
                    if self.send_bitcoin_alert(user_id, alert_data):
                        sent_count += 1
                    else:
                        failed_count += 1
                
                logger.info(f"📢 Broadcast completado: {sent_count} enviados, {failed_count} fallidos de {len(target_users)} totales")
                
                return {
                    'sent': sent_count,
                    'failed': failed_count,
                    'total_targets': len(target_users),
                    'message': f'Broadcast completado: {sent_count}/{len(target_users)} enviados'
                }
                
            finally:
                session.close()
            
        except Exception as e:
            logger.error(f"Error en broadcast: {e}")
            return {'sent': 0, 'failed': 0, 'message': str(e)}
    
    def get_connection_status(self, user_id: int) -> dict:
        """Obtiene el estado de conexión de un usuario desde la base de datos"""
        try:
            session = SessionLocal()
            try:
                user = crud_users.get_user(session, user_id)
                if user:
                    return {
                        'connected': user.telegram_subscribed and user.subscription_status == 'active',
                        'chat_id': user.telegram_chat_id,
                        'subscription_status': user.subscription_status,
                        'bot_configured': self.is_configured()
                    }
                else:
                    return {
                        'connected': False,
                        'chat_id': None,
                        'subscription_status': 'inactive',
                        'bot_configured': self.is_configured()
                    }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error obteniendo estado de conexión: {e}")
            return {
                'connected': False,
                'chat_id': None,
                'subscription_status': 'error',
                'bot_configured': self.is_configured()
            }
    
    def cleanup_expired_connections(self):
        """Limpia códigos de conexión expirados"""
        now = datetime.now()
        expired_codes = [
            code for code, data in self.pending_connections.items()
            if now > data['expires_at']
        ]
        
        for code in expired_codes:
            del self.pending_connections[code]
        
        if expired_codes:
            logger.info(f"🧹 Limpiados {len(expired_codes)} códigos de conexión expirados")
    
    def _setup_webhook_if_needed(self):
        """Configura el webhook automáticamente para desarrollo local"""
        try:
            # Para desarrollo local, usamos ngrok o simplemente informamos
            webhook_url = "https://tu-servidor.com/telegram/webhook"  # Cambiar por tu URL real
            
            # En desarrollo local, solo loggeamos la información
            if "localhost" in webhook_url or not webhook_url.startswith("https://"):
                logger.info(f"🔧 Para configurar webhook manualmente:")
                logger.info(f"   Ejecuta: curl -X POST 'https://api.telegram.org/bot{self.bot_token}/setWebhook' \\")
                logger.info(f"            -H 'Content-Type: application/json' \\")
                logger.info(f"            -d '{{\"url\": \"TU_URL_PUBLICA/telegram/webhook\"}}'")
                logger.info(f"🔧 O usar polling manual (getUpdates) para desarrollo local")
                return
                
            # En producción, configurar webhook automáticamente
            response = requests.post(f"{self.base_url}/setWebhook", json={"url": webhook_url})
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"✅ Webhook configurado: {webhook_url}")
                else:
                    logger.warning(f"⚠️ Error configurando webhook: {result.get('description')}")
            else:
                logger.warning(f"⚠️ Error HTTP configurando webhook: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ No se pudo configurar webhook automáticamente: {e}")
    
    def setup_manual_polling(self):
        """Para desarrollo local - usar polling manual en lugar de webhook"""
        try:
            if not self.is_configured():
                return
                
            response = requests.get(f"{self.base_url}/getUpdates")
            if response.status_code == 200:
                updates = response.json()
                if updates.get('ok'):
                    logger.info(f"📱 Polling manual disponible - {len(updates.get('result', []))} mensajes pendientes")
                    # Procesar mensajes pendientes
                    for update in updates.get('result', []):
                        self.process_telegram_update(update)
                        
        except Exception as e:
            logger.error(f"Error en polling manual: {e}")
    
    def broadcast_alert_crypto(self, alert_data: dict, crypto: str) -> dict:
        """
        Envía alerta al bot específico de una criptomoneda
        
        Args:
            alert_data: Datos de la alerta
            crypto: Tipo de crypto ('bitcoin', 'ethereum', 'bnb')
        
        Returns:
            dict: Resultado del envío
        """
        try:
            # Importar aquí para evitar import circular
            from app.telegram.crypto_bots import crypto_bots
            
            # Usar el bot específico de la crypto
            result = crypto_bots.broadcast_alert(crypto, alert_data)
            
            # Si el bot específico no está configurado, usar el bot principal como fallback
            if result.get('sent', 0) == 0 and result.get('errors'):
                logger.warning(f"⚠️ Bot {crypto} no disponible, usando bot principal como fallback")
                return self.broadcast_alert(alert_data)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en broadcast_alert_crypto para {crypto}: {e}")
            # Fallback al bot principal
            return self.broadcast_alert(alert_data)

# Instancia global del bot
telegram_bot = TelegramBot()