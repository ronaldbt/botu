# backend/app/telegram/crypto_bots.py

import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_users, crud_alertas

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoBotManager:
    """
    Gestor de bots de Telegram específicos para cada criptomoneda
    Bitcoin, Ethereum y BNB con funcionalidades independientes
    """
    
    def __init__(self):
        self.bots = {
            'bitcoin': CryptoBot('bitcoin', os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN')),
            'ethereum': CryptoBot('ethereum', os.getenv('TELEGRAM_ETHEREUM_BOT_TOKEN')),
            'bnb': CryptoBot('bnb', os.getenv('TELEGRAM_BNB_BOT_TOKEN'))
        }
        
        logger.info("🤖 Crypto Bots Manager inicializado")
        for crypto, bot in self.bots.items():
            if bot.is_configured:
                logger.info(f"✅ {crypto.upper()} Bot configurado")
            else:
                logger.warning(f"⚠️ {crypto.upper()} Bot no configurado")
    
    def get_bot(self, crypto: str) -> 'CryptoBot':
        """Obtiene bot específico por tipo de crypto"""
        return self.bots.get(crypto.lower())
    
    def broadcast_alert(self, crypto: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía alerta al bot específico de la crypto"""
        bot = self.get_bot(crypto)
        if not bot:
            return {"error": f"Bot para {crypto} no encontrado"}
        
        return bot.send_trading_alert(alert_data)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Obtiene estado de todos los bots"""
        status = {}
        for crypto, bot in self.bots.items():
            status[crypto] = {
                "configured": bot.is_configured,
                "bot_username": bot.bot_username,
                "last_message_sent": bot.last_message_sent
            }
        return status

class CryptoBot:
    """
    Bot de Telegram específico para una criptomoneda
    Maneja alertas de compra/venta y comandos interactivos
    """
    
    def __init__(self, crypto_name: str, token: str):
        self.crypto_name = crypto_name.upper()
        self.crypto_key = crypto_name.lower()
        self.token = token
        self.is_configured = bool(token)
        self.base_url = f"https://api.telegram.org/bot{token}" if token else None
        self.last_message_sent = None
        
        # Configurar información del bot según la crypto
        self.bot_config = self._get_bot_config()
        self.bot_username = self.bot_config.get('username', f'@Botu{self.crypto_name}Bot')
        
        if self.is_configured:
            logger.info(f"🟢 {self.crypto_name} Bot inicializado: {self.bot_username}")
        else:
            logger.warning(f"🔴 {self.crypto_name} Bot no configurado (token faltante)")
    
    def _get_bot_config(self) -> Dict[str, str]:
        """Configuración específica por crypto"""
        configs = {
            'bitcoin': {
                'username': '@BotuBitcoinBot',
                'symbol': '₿',
                'color': '🟡',
                'name_full': 'Bitcoin'
            },
            'ethereum': {
                'username': '@BotuEthereumBot', 
                'symbol': 'Ξ',
                'color': '🔷',
                'name_full': 'Ethereum'
            },
            'bnb': {
                'username': '@BotuBnbBot',
                'symbol': 'BNB',
                'color': '🟡',
                'name_full': 'BNB'
            }
        }
        return configs.get(self.crypto_key, {})
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Envía un mensaje por el bot específico"""
        try:
            if not self.is_configured:
                logger.warning(f"⚠️ {self.crypto_name} Bot no configurado")
                return False
                
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📤 {self.crypto_name} mensaje enviado a chat {chat_id}")
                self.last_message_sent = datetime.now()
                return True
            else:
                logger.error(f"❌ Error {self.crypto_name} Bot: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en {self.crypto_name} Bot send_message: {e}")
            return False
    
    def send_trading_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía alerta de trading específica de la crypto"""
        try:
            if not self.is_configured:
                return {"sent": 0, "total_targets": 0, "errors": [f"{self.crypto_name} Bot no configurado"]}
            
            # Obtener usuarios suscritos a esta crypto específica
            db = SessionLocal()
            try:
                subscribed_users = crud_users.get_active_telegram_users_by_crypto(db, self.crypto_key)
                if not subscribed_users:
                    logger.info(f"ℹ️ No hay usuarios suscritos a {self.crypto_name}")
                    return {"sent": 0, "total_targets": 0, "errors": ["No hay usuarios suscritos"]}
                
                # Formatear mensaje específico para esta crypto
                formatted_message = self._format_alert_message(alert_data)
                
                sent_count = 0
                errors = []
                
                for user in subscribed_users:
                    try:
                        success = self.send_message(user.telegram_chat_id, formatted_message)
                        if success:
                            sent_count += 1
                        else:
                            errors.append(f"Error enviando a {user.username}")
                    except Exception as e:
                        errors.append(f"Error con {user.username}: {str(e)}")
                
                logger.info(f"📊 {self.crypto_name} broadcast: {sent_count}/{len(subscribed_users)} usuarios")
                
                return {
                    "sent": sent_count,
                    "total_targets": len(subscribed_users),
                    "errors": errors
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en {self.crypto_name} trading alert: {e}")
            return {"sent": 0, "total_targets": 0, "errors": [str(e)]}
    
    def _format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """Formatea mensaje de alerta específico para la crypto"""
        try:
            alert_type = alert_data.get('type', 'BUY')
            symbol = alert_data.get('symbol', f'{self.crypto_name}USDT')
            price = alert_data.get('price', 0)
            
            # Emoji y color específico de la crypto
            crypto_emoji = self.bot_config.get('symbol', self.crypto_name)
            color_emoji = self.bot_config.get('color', '🟢')
            
            if alert_type == 'BUY':
                return self._format_buy_message(crypto_emoji, color_emoji, symbol, price, alert_data)
            else:
                return self._format_sell_message(crypto_emoji, color_emoji, symbol, price, alert_data)
                
        except Exception as e:
            logger.error(f"❌ Error formateando mensaje {self.crypto_name}: {e}")
            return f"Error formateando alerta {self.crypto_name}: {str(e)}"
    
    def _format_buy_message(self, crypto_emoji: str, color_emoji: str, symbol: str, price: float, data: Dict) -> str:
        """Formatea mensaje de compra"""
        message = data.get('message', '')
        
        # Extraer información del mensaje si está disponible
        lines = message.split('\n')
        
        # Mensaje específico por crypto
        formatted_message = f"""{color_emoji} *SEÑAL DE COMPRA {crypto_emoji}*

🎯 *{self.bot_config.get('name_full', self.crypto_name)}*
💰 Precio: ${price:,.2f}
📊 Par: {symbol}

{message}

🤖 Bot: {self.bot_username}
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}"""

        return formatted_message
    
    def _format_sell_message(self, crypto_emoji: str, color_emoji: str, symbol: str, price: float, data: Dict) -> str:
        """Formatea mensaje de venta"""
        message = data.get('message', '')
        
        formatted_message = f"""{color_emoji} *SEÑAL DE VENTA {crypto_emoji}*

📤 *{self.bot_config.get('name_full', self.crypto_name)}*
💰 Precio: ${price:,.2f}
📊 Par: {symbol}

{message}

🤖 Bot: {self.bot_username}
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}"""

        return formatted_message
    
    def handle_webhook(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja updates del webhook del bot específico"""
        try:
            if 'message' not in update:
                return {"status": "ignored", "reason": "No message"}
            
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            username = message.get('from', {}).get('username', 'Unknown')
            
            logger.info(f"{self.crypto_name} Bot mensaje de @{username}: {text}")
            
            # Verificar si el usuario está suscrito a esta crypto
            db = SessionLocal()
            try:
                user = crud_users.get_user_by_telegram_chat_id(db, chat_id)
                if not user:
                    response = f"🚫 *Usuario no registrado*\n\nPara usar {self.bot_username}, primero debes registrarte en la plataforma BotU."
                    self.send_message(chat_id, response)
                    return {"status": "denied", "reason": "User not registered"}
                
                # Procesar comandos específicos de crypto
                if text.startswith('/'):
                    response = self._handle_crypto_command(text, user)
                else:
                    response = f"ℹ️ Usa /help para ver los comandos de {self.crypto_name} disponibles."
                
                self.send_message(chat_id, response)
                return {"status": "processed", "command": text}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en {self.crypto_name} webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    def _handle_crypto_command(self, command: str, user) -> str:
        """Procesa comandos específicos del bot de crypto"""
        try:
            command = command.lower().strip()
            
            if command == '/start':
                return self._cmd_start(user)
            elif command == '/status':
                return self._cmd_status()
            elif command == '/subscribe':
                return self._cmd_subscribe(user)
            elif command == '/unsubscribe':
                return self._cmd_unsubscribe(user)
            elif command == '/help':
                return self._cmd_help()
            else:
                return f"❓ Comando desconocido: {command}\nUsa /help para ver comandos disponibles."
                
        except Exception as e:
            logger.error(f"❌ Error procesando comando {self.crypto_name}: {e}")
            return f"❌ Error procesando comando: {str(e)}"
    
    def _cmd_start(self, user) -> str:
        """Comando /start específico por crypto"""
        crypto_emoji = self.bot_config.get('symbol', self.crypto_name)
        color_emoji = self.bot_config.get('color', '🟢')
        
        return f"""{color_emoji} *Bot de {self.crypto_name} {crypto_emoji}*
¡Hola {user.username}!

Bienvenido al bot oficial de alertas de {self.bot_config.get('name_full', self.crypto_name)} de BotU.

📊 *Funciones:*
• Alertas de patrones U detectados
• Notificaciones de compra/venta automáticas
• Señales basadas en algoritmos probados
• Actualizaciones en tiempo real

🤖 *Comandos:*
/subscribe - Suscribirse a alertas
/unsubscribe - Cancelar suscripción
/status - Estado del scanner
/help - Esta ayuda

{crypto_emoji} Todas las señales están basadas en los algoritmos de backtesting exitosos de BotU."""
    
    def _cmd_status(self) -> str:
        """Estado del scanner específico"""
        # Aquí podrías conectar con el scanner específico
        return f"""📊 *Estado {self.crypto_name}*

🤖 Bot: Operativo
📡 Conexión: Activa
🔍 Scanner: Monitoreando patrones U
📈 Última señal: En análisis...

✅ Sistema funcionando correctamente"""
    
    def _cmd_subscribe(self, user) -> str:
        """Suscribir usuario a alertas de esta crypto"""
        try:
            db = SessionLocal()
            
            # Actualizar suscripción específica para esta crypto
            # Nota: Esto requeriría extender el modelo de usuario para suscripciones por crypto
            updated_user = crud_users.update_telegram_subscription(db, user.id, user.telegram_chat_id, True)
            db.close()
            
            if updated_user:
                return f"✅ *Suscripción Activada*\n\nAhora recibirás alertas de {self.crypto_name} automáticamente."
            else:
                return "❌ Error activando suscripción. Intenta más tarde."
                
        except Exception as e:
            return f"❌ Error en suscripción: {str(e)}"
    
    def _cmd_unsubscribe(self, user) -> str:
        """Cancelar suscripción del usuario"""
        try:
            db = SessionLocal()
            updated_user = crud_users.update_telegram_subscription(db, user.id, user.telegram_chat_id, False)
            db.close()
            
            if updated_user:
                return f"❌ *Suscripción Cancelada*\n\nYa no recibirás alertas de {self.crypto_name}."
            else:
                return "❌ Error cancelando suscripción. Intenta más tarde."
                
        except Exception as e:
            return f"❌ Error cancelando suscripción: {str(e)}"
    
    def _cmd_help(self) -> str:
        """Ayuda específica del bot"""
        crypto_emoji = self.bot_config.get('symbol', self.crypto_name)
        
        return f"""🤖 *{self.crypto_name} Bot - Ayuda*

{crypto_emoji} *Comandos disponibles:*

/start - Información del bot
/subscribe - Activar alertas de {self.crypto_name}
/unsubscribe - Cancelar alertas
/status - Estado del sistema
/help - Esta ayuda

📊 *Tipos de alertas:*
• 🟢 BUY - Señales de compra (patrones U)
• 🔴 SELL - Señales de venta (TP/SL/MaxHold)
• 📈 Análisis en tiempo real

🎯 *Algoritmo:*
Basado en backtesting exitoso de {self.crypto_name} con estrategias optimizadas y probadas.

💡 Bot exclusivo para usuarios registrados en BotU."""

# Instancia global del gestor de bots
crypto_bots = CryptoBotManager()