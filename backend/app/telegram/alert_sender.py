# backend/app/telegram/alert_sender.py

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_alertas
from app.db.models import Alerta
from app.telegram.crypto_bots import crypto_bots

logger = logging.getLogger(__name__)

class AlertSender:
    """
    Servicio para enviar alertas pendientes por Telegram
    Se ejecuta automáticamente para enviar alertas creadas en BD
    """
    
    def __init__(self):
        self.is_running = False
        self.last_check = None
        
    async def start_monitoring(self):
        """Inicia el monitoreo de alertas pendientes"""
        if self.is_running:
            logger.warning("⚠️ Alert sender ya está ejecutándose")
            return
            
        self.is_running = True
        logger.info("🚀 Alert sender iniciado - Monitoreando alertas pendientes")
        
        while self.is_running:
            try:
                await self.process_pending_alerts()
                await asyncio.sleep(30)  # Revisar cada 30 segundos
            except Exception as e:
                logger.error(f"❌ Error en alert sender: {e}")
                await asyncio.sleep(60)  # Esperar más si hay error
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.is_running = False
        logger.info("🛑 Alert sender detenido")
    
    async def process_pending_alerts(self):
        """Procesa alertas pendientes de envío"""
        db = SessionLocal()
        try:
            # Obtener alertas no enviadas por Telegram (últimas 24 horas)
            cutoff_time = datetime.now() - timedelta(hours=24)
            pending_alerts = db.query(Alerta).filter(
                Alerta.telegram_sent == False,
                Alerta.fecha_creacion >= cutoff_time
            ).order_by(Alerta.fecha_creacion.desc()).all()
            
            if not pending_alerts:
                self.last_check = datetime.now()
                return
            
            logger.info(f"📤 Procesando {len(pending_alerts)} alertas pendientes")
            
            for alert in pending_alerts:
                success = await self.send_alert_by_crypto(alert)
                if success:
                    # Marcar como enviada
                    alert.telegram_sent = True
                    db.commit()
                    logger.info(f"✅ Alerta {alert.id} enviada y marcada como enviada")
                else:
                    logger.warning(f"⚠️ No se pudo enviar alerta {alert.id}")
            
            self.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Error procesando alertas pendientes: {e}")
        finally:
            db.close()
    
    async def send_alert_by_crypto(self, alert: Alerta) -> bool:
        """Envía una alerta específica por el bot de su crypto"""
        try:
            # Determinar la crypto por el símbolo
            crypto_type = self.get_crypto_from_symbol(alert.crypto_symbol)
            if not crypto_type:
                logger.warning(f"⚠️ No se pudo determinar crypto para {alert.crypto_symbol}")
                return False
            
            # Preparar datos para Telegram
            alert_data = {
                'type': alert.tipo_alerta,
                'symbol': alert.ticker,
                'price': alert.precio_entrada or alert.precio_salida or 0,
                'message': alert.mensaje,
                'rupture_level': alert.nivel_ruptura,
                'entry_price': alert.precio_entrada,
                'exit_price': alert.precio_salida,
                'profit_percentage': alert.profit_percentage,
                'profit_usd': alert.profit_usd
            }
            
            # Enviar por el bot específico
            result = crypto_bots.broadcast_alert(crypto_type, alert_data)
            
            sent_count = result.get('sent', 0)
            total_targets = result.get('total_targets', 0)
            
            if sent_count > 0:
                logger.info(f"📢 Alerta {alert.id} ({crypto_type.upper()}) enviada a {sent_count}/{total_targets} usuarios")
                return True
            else:
                logger.warning(f"⚠️ Alerta {alert.id} no se envió a ningún usuario")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando alerta {alert.id}: {e}")
            return False
    
    def get_crypto_from_symbol(self, crypto_symbol: str) -> str:
        """Determina el tipo de crypto por el símbolo"""
        crypto_mapping = {
            'BTC': 'btc',
            'BTC_30M': 'btc',
            'ETH': 'eth', 
            'BNB': 'bnb'
        }
        return crypto_mapping.get(crypto_symbol.upper())
    
    def get_status(self) -> dict:
        """Obtiene el estado del alert sender"""
        return {
            'is_running': self.is_running,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }

# Instancia global
alert_sender = AlertSender()