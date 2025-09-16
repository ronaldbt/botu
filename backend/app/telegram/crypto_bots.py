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
        # Crear los bots
        bitcoin_bot = CryptoBot('bitcoin', os.getenv('TELEGRAM_BITCOIN_BOT_TOKEN'))
        ethereum_bot = CryptoBot('ethereum', os.getenv('TELEGRAM_ETHEREUM_BOT_TOKEN'))
        bnb_bot = CryptoBot('bnb', os.getenv('TELEGRAM_BNB_BOT_TOKEN'))
        
        self.bots = {
            'bitcoin': bitcoin_bot,
            'ethereum': ethereum_bot,
            'bnb': bnb_bot,
            # Aliases para compatibilidad
            'btc': bitcoin_bot,
            'eth': ethereum_bot
        }
        
        logger.info("🤖 Crypto Bots Manager inicializado")
        # Solo mostrar bots principales en logs, no aliases
        for crypto in ['bitcoin', 'ethereum', 'bnb']:
            bot = self.bots[crypto]
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
    

# Instancia global del gestor de bots
crypto_bots = CryptoBotManager()
