# backend/app/telegram/alert_sender.py

import logging
import asyncio
import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_alertas
from app.db.models import Alerta, TradingEvent, TelegramConnection

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

    async def process_pending_trading_events(self):
        """Procesa eventos de trading pendientes agrupando por símbolo/operación para eficiencia."""
        # Verificar feature flag
        if not os.getenv('TELEGRAM_ALERTS_ENABLED', 'false').lower() in ('true', '1', 'yes'):
            logger.debug("🚫 Alertas de Telegram deshabilitadas por feature flag")
            return
            
        db = SessionLocal()
        try:
            pending_events = (db.query(TradingEvent)
                              .filter(TradingEvent.status == 'PENDING')
                              .order_by(TradingEvent.created_at.asc())
                              .limit(100)
                              .all())
            if not pending_events:
                return
            logger.info(f"📥 Procesando {len(pending_events)} trading_events pendientes")

            # Obtener todos los usuarios conectados una sola vez
            connected_users = self._get_connected_users(db)
            if not connected_users:
                logger.info("ℹ️ No hay usuarios conectados a Telegram")
                # Marcar todos como procesados sin envío
                for ev in pending_events:
                    ev.status = 'SENT'
                    ev.processed_at = datetime.now()
                    ev.error_message = 'no_connected_users'
                db.commit()
                return

            # Agrupar eventos por símbolo y operación (últimos 2 minutos)
            grouped_events = self._group_events_by_symbol_and_side(pending_events)
            
            for group_key, events in grouped_events.items():
                try:
                    # Usar el primer evento como referencia para el mensaje
                    reference_event = events[0]
                    
                    # Componer mensaje agrupado
                    message_text = self._format_grouped_message(events, reference_event)
                    
                    # Enviar a todos los usuarios conectados
                    sent_count = 0
                    failed_count = 0
                    
                    for chat_id in connected_users:
                        sent_ok = self._send_message(chat_id, message_text)
                        if sent_ok:
                            sent_count += 1
                        else:
                            failed_count += 1
                        # Rate limit: 0.5 seg entre mensajes para no saturar
                        await asyncio.sleep(0.5)
                    
                    # Marcar todos los eventos del grupo como procesados
                    for ev in events:
                        ev.status = 'SENT'
                        ev.processed_at = datetime.now()
                        ev.error_message = f'sent_to_{sent_count}_users'
                    
                    db.commit()
                    logger.info(f"✅ Grupo {group_key}: {len(events)} eventos enviados a {sent_count} usuarios ({failed_count} fallos)")
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando grupo {group_key}: {e}")
                    # Marcar eventos del grupo como fallidos
                    for ev in events:
                        ev.status = 'FAILED'
                        ev.error_message = str(e)
                    db.commit()
                    
        except Exception as e:
            logger.error(f"❌ Error procesando trading_events: {e}")
        finally:
            db.close()

    def _get_connected_users(self, db: Session) -> List[str]:
        """Obtiene lista de chat_ids de usuarios conectados (cache por 5 minutos)"""
        try:
            # Cache simple en memoria
            if not hasattr(self, '_connected_users_cache') or not self._connected_users_cache:
                self._connected_users_cache = []
                self._cache_timestamp = datetime.now()
            
            # Verificar si el cache es válido (5 minutos)
            if datetime.now() - self._cache_timestamp > timedelta(minutes=5):
                self._connected_users_cache = []
            
            if not self._connected_users_cache:
                connections = db.query(TelegramConnection).filter(
                    TelegramConnection.connected == True,
                    TelegramConnection.chat_id.isnot(None)
                ).all()
                
                self._connected_users_cache = [conn.chat_id for conn in connections]
                self._cache_timestamp = datetime.now()
                logger.info(f"📱 Cache actualizado: {len(self._connected_users_cache)} usuarios conectados")
            
            return self._connected_users_cache
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios conectados: {e}")
            return []

    def _group_events_by_symbol_and_side(self, events: List[TradingEvent]) -> Dict[str, List[TradingEvent]]:
        """Agrupa eventos por símbolo y operación (últimos 2 minutos)"""
        groups = {}
        cutoff_time = datetime.now() - timedelta(minutes=2)
        
        for ev in events:
            # Solo agrupar eventos recientes (o todos si son de prueba)
            if ev.created_at < cutoff_time and not ev.symbol.startswith('TEST'):
                continue
                
            # Crear clave de agrupación: símbolo + operación
            group_key = f"{ev.symbol}_{ev.side}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(ev)
        
        return groups

    def _format_grouped_message(self, events: List[TradingEvent], reference_event: TradingEvent) -> str:
        """Formatea mensaje para un grupo de eventos similares"""
        if not events:
            return ""
        
        # Usar el primer evento como referencia
        ev = reference_event
        scanner_info = self._get_scanner_info(ev.symbol)
        
        if ev.side == 'BUY':
            emoji = "🟢"
            action = "COMPRA"
            # Calcular totales del grupo
            total_quantity = sum(e.quantity or 0 for e in events)
            avg_price = sum((e.price or 0) * (e.quantity or 0) for e in events) / total_quantity if total_quantity > 0 else 0
            total_value = sum(e.total_usdt or (e.quantity or 0) * (e.price or 0) for e in events)
            
            message = f"{emoji} {action} {ev.symbol}\n"
            message += f"📊 {scanner_info}\n"
            message += f"💰 Cantidad: {total_quantity:.6f} @ ${avg_price:.2f}\n"
            message += f"💵 Total: ${total_value:.2f}\n"
            message += f"👥 Operaciones: {len(events)}\n"
            message += f"🔧 Origen: {ev.source or 'sistema'}\n"
            message += f"🕒 {ev.created_at.strftime('%H:%M:%S')}"
            
        else:  # SELL
            emoji = "🔴"
            action = "VENTA"
            # Calcular totales del grupo
            total_quantity = sum(e.quantity or 0 for e in events)
            avg_price = sum((e.price or 0) * (e.quantity or 0) for e in events) / total_quantity if total_quantity > 0 else 0
            total_pnl = sum(e.pnl_usdt or 0 for e in events)
            avg_pnl_pct = sum(e.pnl_percentage or 0 for e in events) / len(events) if events else 0
            
            message = f"{emoji} {action} {ev.symbol}\n"
            message += f"📊 {scanner_info}\n"
            message += f"💰 Cantidad: {total_quantity:.6f} @ ${avg_price:.2f}\n"
            message += f"💵 PnL Total: ${total_pnl:+.2f} ({avg_pnl_pct:+.2f}%)\n"
            message += f"👥 Operaciones: {len(events)}\n"
            message += f"🔧 Origen: {ev.source or 'sistema'}\n"
            message += f"🕒 {ev.created_at.strftime('%H:%M:%S')}"
        
        return message

    def _send_message(self, chat_id: str, message: str) -> bool:
        """Envía un mensaje usando un único bot configurado por TELEGRAM_BOT_TOKEN."""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN no configurado")
                return False

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }

            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return True
            logger.error(f"Telegram sendMessage error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Error enviando mensaje Telegram: {e}")
            return False

    def _format_message_from_event(self, ev: TradingEvent) -> str:
        # Determinar scanner/timeframe por símbolo
        scanner_info = self._get_scanner_info(ev.symbol)
        
        if ev.side == 'BUY':
            emoji = "🟢"
            action = "COMPRA"
            details = f"{ev.quantity or 0:.6f} @ ${ev.price or 0:.2f}"
            total = f"Total: ${ev.total_usdt or (ev.quantity or 0) * (ev.price or 0):.2f}"
        else:
            pnl = ev.pnl_usdt or 0.0
            pnl_pct = ev.pnl_percentage or 0.0
            emoji = '🟢' if pnl > 0 else '🔴' if pnl < 0 else '⚪'
            action = "VENTA"
            details = f"{ev.quantity or 0:.6f} @ ${ev.price or 0:.2f}"
            total = f"PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)"
        
        # Formato unificado
        message = f"{emoji} {action} {ev.symbol}\n"
        message += f"📊 {scanner_info}\n"
        message += f"💰 {details}\n"
        message += f"💵 {total}\n"
        message += f"🔧 Origen: {ev.source or 'sistema'}\n"
        message += f"🕒 {ev.created_at.strftime('%H:%M:%S')}"
        
        return message
    
    def _get_scanner_info(self, symbol: str) -> str:
        """Determina el scanner y timeframe basado en el símbolo"""
        symbol_upper = symbol.upper()
        
        if symbol_upper == 'BTCUSDT':
            # Asumir BTC 30m por defecto, pero podría ser 4h
            return "Bitcoin 30m Scanner"
        elif symbol_upper == 'ETHUSDT':
            return "Ethereum 4h Scanner"
        elif symbol_upper == 'BNBUSDT':
            return "BNB 4h Scanner"
        elif symbol_upper == 'PAXGUSDT':
            return "PAXG 4h Scanner"
        else:
            return "Trading Scanner"
    
    async def send_alert_by_crypto(self, alert: Alerta) -> bool:
        """Compat: envía una alerta vinculada a un usuario por su conexión principal."""
        try:
            db = SessionLocal()
            try:
                # Determinar usuario destino
                target_user_id = alert.usuario_id
                if not target_user_id:
                    logger.warning(f"Alerta {alert.id} sin usuario asociado")
                    return False

                conn = db.query(TelegramConnection).filter(
                    TelegramConnection.user_id == target_user_id,
                    TelegramConnection.connected == True,
                    TelegramConnection.chat_id.isnot(None)
                ).order_by(TelegramConnection.connected_at.desc().nullslast()).first()

                if not conn or not conn.chat_id:
                    logger.warning(f"Usuario {target_user_id} sin chat conectado para alertas")
                    return False

                sent_ok = self._send_message(conn.chat_id, alert.mensaje)
                return bool(sent_ok)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ Error enviando alerta {alert.id}: {e}")
            return False
    
    def get_status(self) -> dict:
        """Obtiene el estado del alert sender"""
        return {
            'is_running': self.is_running,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }

# Instancia global
alert_sender = AlertSender()