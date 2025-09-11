# backend/app/services/health_monitor_service.py

import asyncio
import logging
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
import sys
import os

# Add src path for trading modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from app.db.database import SessionLocal
from app.db import crud_alertas, crud_users
from app.services.eth_scanner_service import eth_scanner
from app.services.bitcoin_scanner_service import bitcoin_scanner
from app.services.bnb_scanner_service import bnb_scanner

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthMonitorService:
    """
    Servicio de monitoreo de salud del servidor y scanners
    Envía reportes automáticos 2 veces al día a los administradores
    """
    
    def __init__(self):
        self.is_running = False
        self.monitor_task = None
        self.config = {
            "report_times": ["09:00", "21:00"],  # 9 AM y 9 PM
            "timezone": "UTC",
            "check_interval": 30 * 60,  # Verificar cada 30 minutos
            "admin_telegram_token": os.getenv('TELEGRAM_HEALTH_BOT_TOKEN'),
            "admin_chat_ids": []  # Se llenará dinámicamente
        }
        self.last_report_sent = None
        self.system_alerts = []
        self.max_alerts = 100
        
    def _add_system_alert(self, level: str, component: str, message: str, details: dict = None):
        """Agrega una alerta del sistema"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,  # INFO, WARNING, ERROR, CRITICAL
            "component": component,  # SERVER, BITCOIN_SCANNER, ETH_SCANNER, BNB_SCANNER, DATABASE
            "message": message,
            "details": details or {}
        }
        
        self.system_alerts.append(alert)
        
        # Mantener solo las últimas alertas
        if len(self.system_alerts) > self.max_alerts:
            self.system_alerts = self.system_alerts[-self.max_alerts:]
        
        # Log crítico inmediatamente
        if level == "CRITICAL":
            logger.critical(f"🚨 CRÍTICO [{component}]: {message}")
            # Enviar alerta inmediata a admins
            asyncio.create_task(self._send_critical_alert(alert))
        elif level == "ERROR":
            logger.error(f"❌ ERROR [{component}]: {message}")
        elif level == "WARNING":
            logger.warning(f"⚠️ WARNING [{component}]: {message}")
        else:
            logger.info(f"ℹ️ INFO [{component}]: {message}")
    
    async def start_monitoring(self) -> bool:
        """Inicia el monitoreo de salud 24/7"""
        if self.is_running:
            return False
            
        try:
            self.is_running = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self._add_system_alert("INFO", "HEALTH_MONITOR", "Sistema de monitoreo de salud iniciado")
            logger.info("🏥 Health Monitor iniciado - Reportes automáticos activados")
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando Health Monitor: {e}")
            self.is_running = False
            return False
    
    async def stop_monitoring(self) -> bool:
        """Detiene el monitoreo de salud"""
        if not self.is_running:
            return True
            
        try:
            self.is_running = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            self._add_system_alert("INFO", "HEALTH_MONITOR", "Sistema de monitoreo detenido")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo Health Monitor: {e}")
            return False
    
    async def _monitor_loop(self):
        """Loop principal de monitoreo"""
        logger.info("🔄 Iniciando loop de monitoreo de salud")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 1. Verificar salud del sistema cada 30 minutos
                await self._check_system_health()
                
                # 2. Verificar si es hora de enviar reporte programado
                if self._should_send_scheduled_report(current_time):
                    await self._send_scheduled_report()
                    self.last_report_sent = current_time
                
                # Esperar hasta la próxima verificación
                await asyncio.sleep(self.config['check_interval'])
                
            except asyncio.CancelledError:
                logger.info("🛑 Health Monitor cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error crítico en Health Monitor: {e}")
                self._add_system_alert("ERROR", "HEALTH_MONITOR", f"Error en loop principal: {str(e)}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    async def _check_system_health(self):
        """Verifica la salud completa del sistema"""
        try:
            health_report = {
                "timestamp": datetime.now(),
                "server": await self._check_server_health(),
                "database": await self._check_database_health(),
                "scanners": await self._check_scanners_health(),
                "binance_api": await self._check_binance_api_health()
            }
            
            # Detectar problemas críticos
            critical_issues = []
            for component, status in health_report.items():
                if isinstance(status, dict) and not status.get('healthy', True):
                    critical_issues.append(f"{component}: {status.get('error', 'Unknown error')}")
            
            if critical_issues:
                self._add_system_alert("ERROR", "SYSTEM", f"Problemas detectados: {', '.join(critical_issues)}")
            
        except Exception as e:
            self._add_system_alert("ERROR", "HEALTH_MONITOR", f"Error verificando salud del sistema: {str(e)}")
    
    async def _check_server_health(self) -> Dict[str, Any]:
        """Verifica salud del servidor"""
        try:
            # CPU, RAM, Disk
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Verificar límites críticos
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"CPU alta: {cpu_percent:.1f}%")
            if memory.percent > 80:
                warnings.append(f"RAM alta: {memory.percent:.1f}%")
            if disk.percent > 80:
                warnings.append(f"Disco lleno: {disk.percent:.1f}%")
            
            if warnings:
                self._add_system_alert("WARNING", "SERVER", f"Recursos altos: {', '.join(warnings)}")
            
            return {
                "healthy": len(warnings) == 0,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime_seconds": int(datetime.now().timestamp() - psutil.boot_time()),
                "warnings": warnings
            }
        except Exception as e:
            self._add_system_alert("ERROR", "SERVER", f"Error verificando servidor: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Verifica salud de la base de datos"""
        try:
            db = SessionLocal()
            start_time = datetime.now()
            
            # Test básico de conexión
            from sqlalchemy import text
            result = db.execute(text("SELECT 1")).fetchone()
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Verificar tablas críticas
            alertas_count = crud_alertas.get_alertas_count(db)
            
            db.close()
            
            healthy = result is not None and response_time < 5.0
            if not healthy:
                self._add_system_alert("ERROR", "DATABASE", f"Base de datos lenta o inaccesible (tiempo: {response_time:.2f}s)")
            
            return {
                "healthy": healthy,
                "response_time_seconds": response_time,
                "total_alerts": alertas_count,
                "connection_status": "OK" if result else "FAILED"
            }
        except Exception as e:
            self._add_system_alert("ERROR", "DATABASE", f"Error verificando base de datos: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    async def _check_scanners_health(self) -> Dict[str, Any]:
        """Verifica salud de los 3 scanners"""
        try:
            scanners_status = {
                "bitcoin": {
                    "running": bitcoin_scanner.is_running,
                    "last_scan": bitcoin_scanner.last_scan_time,
                    "alerts_count": bitcoin_scanner.alerts_count
                },
                "ethereum": {
                    "running": eth_scanner.is_running,
                    "last_scan": eth_scanner.last_scan_time,
                    "alerts_count": eth_scanner.alerts_count
                },
                "bnb": {
                    "running": bnb_scanner.is_running,
                    "last_scan": bnb_scanner.last_scan_time,
                    "alerts_count": bnb_scanner.alerts_count
                }
            }
            
            # Verificar problemas
            issues = []
            for name, status in scanners_status.items():
                if not status['running']:
                    issues.append(f"{name} scanner detenido")
                elif status['last_scan']:
                    time_since_scan = (datetime.now() - status['last_scan']).total_seconds()
                    if time_since_scan > 7200:  # Más de 2 horas sin escanear
                        issues.append(f"{name} sin escanear por {time_since_scan/3600:.1f}h")
            
            if issues:
                self._add_system_alert("WARNING", "SCANNERS", f"Problemas detectados: {', '.join(issues)}")
            
            return {
                "healthy": len(issues) == 0,
                "scanners": scanners_status,
                "issues": issues
            }
        except Exception as e:
            self._add_system_alert("ERROR", "SCANNERS", f"Error verificando scanners: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    async def _check_binance_api_health(self) -> Dict[str, Any]:
        """Verifica salud de la API de Binance"""
        try:
            start_time = datetime.now()
            response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
            response_time = (datetime.now() - start_time).total_seconds()
            
            healthy = response.status_code == 200 and response_time < 5.0
            if not healthy:
                self._add_system_alert("WARNING", "BINANCE_API", f"API lenta o inaccesible (código: {response.status_code}, tiempo: {response_time:.2f}s)")
            
            return {
                "healthy": healthy,
                "status_code": response.status_code,
                "response_time_seconds": response_time
            }
        except Exception as e:
            self._add_system_alert("ERROR", "BINANCE_API", f"Error verificando API Binance: {str(e)}")
            return {"healthy": False, "error": str(e)}
    
    def _should_send_scheduled_report(self, current_time: datetime) -> bool:
        """Verifica si es hora de enviar reporte programado"""
        current_time_str = current_time.strftime("%H:%M")
        
        # Verificar si es una de las horas programadas (con margen de 30 min)
        for report_time in self.config['report_times']:
            target_hour, target_minute = map(int, report_time.split(':'))
            time_diff = abs((current_time.hour * 60 + current_time.minute) - (target_hour * 60 + target_minute))
            
            # Si estamos dentro de 30 minutos de la hora objetivo y no hemos enviado en las últimas 6 horas
            if time_diff <= 30:
                if not self.last_report_sent or (current_time - self.last_report_sent).total_seconds() > 6 * 3600:
                    return True
        
        return False
    
    async def _send_scheduled_report(self):
        """Envía reporte programado de salud a admins"""
        try:
            # Generar reporte completo
            health_data = {
                "server": await self._check_server_health(),
                "database": await self._check_database_health(),
                "scanners": await self._check_scanners_health(),
                "binance_api": await self._check_binance_api_health()
            }
            
            # Contar alertas recientes (últimas 12 horas)
            recent_alerts = len([a for a in self.system_alerts 
                               if (datetime.now() - datetime.fromisoformat(a['timestamp'])).total_seconds() < 12 * 3600])
            
            # Generar mensaje de reporte
            report_message = self._generate_health_report_message(health_data, recent_alerts)
            
            # Enviar a admins por Telegram
            await self._send_admin_telegram_message(report_message)
            
            logger.info("📊 Reporte de salud programado enviado a administradores")
            
        except Exception as e:
            logger.error(f"❌ Error enviando reporte programado: {e}")
    
    def _generate_health_report_message(self, health_data: Dict, recent_alerts: int) -> str:
        """Genera mensaje de reporte de salud"""
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M UTC")
        
        # Emojis según estado
        server_emoji = "🟢" if health_data['server']['healthy'] else "🔴"
        db_emoji = "🟢" if health_data['database']['healthy'] else "🔴"
        scanners_emoji = "🟢" if health_data['scanners']['healthy'] else "🔴"
        api_emoji = "🟢" if health_data['binance_api']['healthy'] else "🔴"
        
        message = f"""🏥 **REPORTE DE SALUD DEL SERVIDOR**
📅 {timestamp}

🖥️ **SERVIDOR** {server_emoji}
   • CPU: {health_data['server']['cpu_percent']:.1f}%
   • RAM: {health_data['server']['memory_percent']:.1f}%
   • Disco: {health_data['server']['disk_percent']:.1f}%
   • Uptime: {health_data['server']['uptime_seconds']//3600:.0f}h

💾 **BASE DE DATOS** {db_emoji}
   • Conexión: {health_data['database']['connection_status']}
   • Tiempo respuesta: {health_data['database']['response_time_seconds']:.2f}s
   • Total alertas: {health_data['database']['total_alerts']}

🤖 **SCANNERS** {scanners_emoji}
   • Bitcoin: {'🟢' if health_data['scanners']['scanners']['bitcoin']['running'] else '🔴'} ({health_data['scanners']['scanners']['bitcoin']['alerts_count']} alertas)
   • Ethereum: {'🟢' if health_data['scanners']['scanners']['ethereum']['running'] else '🔴'} ({health_data['scanners']['scanners']['ethereum']['alerts_count']} alertas)
   • BNB: {'🟢' if health_data['scanners']['scanners']['bnb']['running'] else '🔴'} ({health_data['scanners']['scanners']['bnb']['alerts_count']} alertas)

🌐 **BINANCE API** {api_emoji}
   • Estado: {health_data['binance_api']['status_code']}
   • Latencia: {health_data['binance_api']['response_time_seconds']:.2f}s

📊 **ALERTAS SISTEMA (12h)**: {recent_alerts}

✅ **Sistema operativo y funcionando correctamente**"""

        return message
    
    async def _send_critical_alert(self, alert: Dict):
        """Envía alerta crítica inmediata a admins"""
        try:
            message = f"""🚨 **ALERTA CRÍTICA**
🕐 {alert['timestamp']}
🔧 Componente: {alert['component']}
❌ Problema: {alert['message']}

⚠️ Requiere atención inmediata del administrador"""

            await self._send_admin_telegram_message(message)
        except Exception as e:
            logger.error(f"❌ Error enviando alerta crítica: {e}")
    
    async def _send_admin_telegram_message(self, message: str):
        """Envía mensaje a administradores por Health Bot de Telegram"""
        try:
            # Import lazy para evitar circular import
            from app.telegram.health_bot import health_bot
            
            result = health_bot.broadcast_to_admins(message)
            logger.info(f"📤 Health Bot: {result['sent']}/{result['total_targets']} admins notificados")
            
            if result['errors']:
                logger.warning(f"⚠️ Errores en Health Bot: {', '.join(result['errors'])}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje por Health Bot: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado del monitor de salud"""
        return {
            "is_running": self.is_running,
            "last_report_sent": self.last_report_sent.isoformat() if self.last_report_sent else None,
            "recent_alerts": len([a for a in self.system_alerts 
                                if (datetime.now() - datetime.fromisoformat(a['timestamp'])).total_seconds() < 24 * 3600]),
            "next_report_times": self.config['report_times'],
            "config": self.config
        }

# Instancia global del monitor de salud
health_monitor = HealthMonitorService()