# backend/app/telegram/health_bot.py

import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_users
from app.services.health_monitor_service import health_monitor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthTelegramBot:
    """
    Bot de Telegram específico para monitoreo de salud del sistema
    Solo para administradores del sistema
    """
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_HEALTH_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token:
            logger.warning("⚠️ TELEGRAM_HEALTH_BOT_TOKEN no configurado")
        else:
            logger.info(f"🏥 Health Bot inicializado: @BotuHealthBot")
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Envía un mensaje por el bot de salud"""
        try:
            if not self.token:
                logger.warning("⚠️ Token de Health Bot no configurado")
                return False
                
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📤 Mensaje de salud enviado a chat {chat_id}")
                return True
            else:
                logger.error(f"❌ Error enviando mensaje de salud: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en send_message Health Bot: {e}")
            return False
    
    def broadcast_to_admins(self, message: str) -> Dict[str, Any]:
        """Envía mensaje a todos los administradores activos"""
        try:
            db = SessionLocal()
            admin_users = crud_users.get_admin_telegram_users(db)
            db.close()
            
            if not admin_users:
                logger.warning("⚠️ No hay administradores con Telegram configurado")
                return {"sent": 0, "total_targets": 0, "errors": ["No hay administradores"]}
            
            sent_count = 0
            errors = []
            
            for admin in admin_users:
                try:
                    success = self.send_message(admin.telegram_chat_id, message)
                    if success:
                        sent_count += 1
                    else:
                        errors.append(f"Error enviando a {admin.username}")
                except Exception as e:
                    errors.append(f"Error con {admin.username}: {str(e)}")
            
            logger.info(f"📊 Health broadcast: {sent_count}/{len(admin_users)} admins")
            
            return {
                "sent": sent_count,
                "total_targets": len(admin_users),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"❌ Error en broadcast_to_admins: {e}")
            return {"sent": 0, "total_targets": 0, "errors": [str(e)]}
    
    def handle_webhook(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja updates del webhook del bot de salud"""
        try:
            if 'message' not in update:
                return {"status": "ignored", "reason": "No message"}
            
            message = update['message']
            chat_id = str(message['chat']['id'])
            text = message.get('text', '').strip()
            username = message.get('from', {}).get('username', 'Unknown')
            
            logger.info(f"🏥 Health Bot mensaje de @{username}: {text}")
            
            # Verificar si el usuario es admin
            db = SessionLocal()
            try:
                user = crud_users.get_user_by_telegram_chat_id(db, chat_id)
                if not user or not user.is_admin:
                    response = "🚫 *Acceso Denegado*\n\nEste bot es solo para administradores del sistema BotU."
                    self.send_message(chat_id, response)
                    return {"status": "denied", "reason": "Not admin"}
                
                # Procesar comandos de admin
                if text.startswith('/'):
                    response = self._handle_admin_command(text, user)
                else:
                    response = "ℹ️ Usa /help para ver los comandos disponibles."
                
                self.send_message(chat_id, response)
                return {"status": "processed", "command": text}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error en handle_webhook Health Bot: {e}")
            return {"status": "error", "error": str(e)}
    
    def _handle_admin_command(self, command: str, user) -> str:
        """Procesa comandos de administrador"""
        try:
            command = command.lower().strip()
            
            if command == '/start':
                return self._cmd_start(user)
            elif command == '/status':
                return self._cmd_status()
            elif command == '/report':
                return self._cmd_report()
            elif command == '/help':
                return self._cmd_help()
            else:
                return f"❓ Comando desconocido: {command}\nUsa /help para ver comandos disponibles."
                
        except Exception as e:
            logger.error(f"❌ Error procesando comando: {e}")
            return f"❌ Error procesando comando: {str(e)}"
    
    def _cmd_start(self, user) -> str:
        """Comando /start"""
        return f"""🏥 *BotU Health Monitor*
¡Hola {user.username}!

Bienvenido al sistema de monitoreo de salud de BotU.

📊 *Funciones disponibles:*
• Reportes automáticos 2 veces al día (09:00 y 21:00 UTC)
• Alertas críticas inmediatas
• Monitoreo de servidor, base de datos y scanners
• Estadísticas en tiempo real

🤖 *Comandos disponibles:*
/status - Estado actual del sistema
/report - Reporte completo de salud
/help - Esta ayuda

El monitoreo está activo 24/7. Recibirás alertas automáticamente cuando sea necesario."""
    
    def _cmd_status(self) -> str:
        """Comando /status"""
        try:
            status = health_monitor.get_status()
            
            if status['is_running']:
                emoji = "🟢"
                state = "OPERATIVO"
            else:
                emoji = "🔴"
                state = "DETENIDO"
            
            last_report = "Nunca"
            if status['last_report_sent']:
                last_report = status['last_report_sent']
            
            return f"""📊 *Estado del Health Monitor*

{emoji} *Estado:* {state}
📅 *Último reporte:* {last_report}
🚨 *Alertas recientes:* {status['recent_alerts']}
⏰ *Próximos reportes:* {', '.join(status['next_report_times'])} UTC

🔄 *Verificando cada:* 30 minutos
📈 *Monitoreo activo desde el inicio del servidor*"""
        except Exception as e:
            return f"❌ Error obteniendo estado: {str(e)}"
    
    def _cmd_report(self) -> str:
        """Comando /report - Genera reporte completo"""
        try:
            # Generar reporte en tiempo real (simplificado para Telegram)
            import asyncio
            
            # Crear nuevo loop si no existe
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Ejecutar verificaciones de salud
            server_health = loop.run_until_complete(health_monitor._check_server_health())
            db_health = loop.run_until_complete(health_monitor._check_database_health())
            scanners_health = loop.run_until_complete(health_monitor._check_scanners_health())
            api_health = loop.run_until_complete(health_monitor._check_binance_api_health())
            
            # Emojis según estado
            server_emoji = "🟢" if server_health['healthy'] else "🔴"
            db_emoji = "🟢" if db_health['healthy'] else "🔴"
            scanners_emoji = "🟢" if scanners_health['healthy'] else "🔴"
            api_emoji = "🟢" if api_health['healthy'] else "🔴"
            
            # Estado general
            all_healthy = all([
                server_health['healthy'],
                db_health['healthy'], 
                scanners_health['healthy'],
                api_health['healthy']
            ])
            
            overall_emoji = "🟢" if all_healthy else "🔴"
            overall_status = "SALUDABLE" if all_healthy else "REQUIERE ATENCIÓN"
            
            return f"""🏥 *REPORTE DE SALUD COMPLETO*
📅 {datetime.now().strftime('%d/%m/%Y %H:%M UTC')}

{overall_emoji} *Estado General:* {overall_status}

🖥️ *SERVIDOR* {server_emoji}
   • CPU: {server_health['cpu_percent']:.1f}%
   • RAM: {server_health['memory_percent']:.1f}%
   • Disco: {server_health['disk_percent']:.1f}%

💾 *BASE DE DATOS* {db_emoji}
   • Conexión: {db_health['connection_status']}
   • Tiempo respuesta: {db_health['response_time_seconds']:.2f}s
   • Total alertas: {db_health['total_alerts']}

🤖 *SCANNERS* {scanners_emoji}
   • Bitcoin: {'🟢' if scanners_health['scanners']['bitcoin']['running'] else '🔴'}
   • Ethereum: {'🟢' if scanners_health['scanners']['ethereum']['running'] else '🔴'}
   • BNB: {'🟢' if scanners_health['scanners']['bnb']['running'] else '🔴'}

🌐 *BINANCE API* {api_emoji}
   • Estado: {api_health['status_code']}
   • Latencia: {api_health['response_time_seconds']:.2f}s

📊 *Sistema funcionando correctamente*"""
            
        except Exception as e:
            return f"❌ Error generando reporte: {str(e)}"
    
    def _cmd_help(self) -> str:
        """Comando /help"""
        return """🏥 *BotU Health Monitor - Ayuda*

🤖 *Comandos disponibles:*

/start - Iniciar monitoreo de salud
/status - Ver estado actual del sistema  
/report - Generar reporte completo
/help - Esta ayuda

📊 *Funciones automáticas:*
• Reportes programados a las 09:00 y 21:00 UTC
• Alertas críticas inmediatas
• Monitoreo continuo cada 30 minutos

🔧 *Qué monitoreamos:*
• Servidor (CPU, RAM, Disco)
• Base de datos (Conexión, rendimiento)
• Scanners (Bitcoin, Ethereum, BNB)
• API Binance (Disponibilidad, latencia)

⚠️ *Tipos de alertas:*
• 🟢 INFO - Información general
• 🟡 WARNING - Advertencias
• 🔴 ERROR - Errores que requieren atención
• 🚨 CRITICAL - Problemas críticos inmediatos

💡 *Este bot es solo para administradores del sistema BotU.*"""

# Instancia global del bot de salud
health_bot = HealthTelegramBot()