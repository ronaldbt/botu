# backend/app/services/bitcoin_scanner_service.py

import asyncio
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from sqlalchemy.orm import Session
import sys
import os

# Add src path for trading modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from app.db.database import SessionLocal
from app.db import crud_users
from app.telegram.telegram_bot import telegram_bot

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinScannerService:
    """
    Servicio de scanner automático de Bitcoin usando la lógica exitosa del backtest 2022
    """
    
    def __init__(self):
        self.is_running = False
        self.scan_task = None
        self.config = {
            "timeframe": "4h",
            "profit_target": 0.08,     # 8% take profit
            "stop_loss": 0.05,         # 5% stop loss  
            "min_pattern_depth": 0.04, # 4% profundidad mínima
            "scan_interval": 5 * 60,  # 5 minutos para testing (cambiar a 4h + 5min en producción)
            "symbol": "BTCUSDT"
        }
        self.last_scan_time = None
        self.alerts_count = 0
        self.last_alert_sent = None  # Timestamp de la última alerta enviada
        self.cooldown_period = 60 * 60  # 1 hora de cooldown entre alertas
        self.scanner_logs = []  # Lista de logs para mostrar en el frontend
        self.max_logs = 50  # Máximo número de logs a mantener
        
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del scanner (solo admin)"""
        self.config.update(new_config)
        logger.info(f"✅ Configuración actualizada: {self.config}")
    
    def _add_log(self, level: str, message: str, details: dict = None):
        """Agrega un log personalizado para el frontend"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,  # INFO, SUCCESS, WARNING, ERROR
            "message": message,
            "details": details or {}
        }
        
        self.scanner_logs.append(log_entry)
        
        # Mantener solo los últimos logs
        if len(self.scanner_logs) > self.max_logs:
            self.scanner_logs = self.scanner_logs[-self.max_logs:]
        
        # También loggear normalmente
        if level == "ERROR":
            logger.error(f"🔴 {message}")
        elif level == "WARNING":
            logger.warning(f"🟡 {message}")
        elif level == "SUCCESS":
            logger.info(f"🟢 {message}")
        else:
            logger.info(f"🔵 {message}")
    
    async def start_scanning(self) -> bool:
        """Inicia el scanner automático"""
        if self.is_running:
            logger.warning("⚠️ Scanner ya está ejecutándose")
            return False
            
        try:
            self.is_running = True
            self.scan_task = asyncio.create_task(self._scan_loop())
            self._add_log("SUCCESS", "Bitcoin Scanner iniciado - Modo automático 24/7", {
                "timeframe": self.config["timeframe"],
                "scan_interval": f"{self.config['scan_interval']/60:.0f} minutos"
            })
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando scanner: {e}")
            self.is_running = False
            return False
    
    async def stop_scanning(self) -> bool:
        """Detiene el scanner automático"""
        if not self.is_running:
            return True
            
        try:
            self.is_running = False
            if self.scan_task:
                self.scan_task.cancel()
                try:
                    await self.scan_task
                except asyncio.CancelledError:
                    pass
            logger.info("⏹️ Bitcoin Scanner detenido")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo scanner: {e}")
            return False
    
    async def _scan_loop(self):
        """Loop principal del scanner"""
        logger.info(f"🔄 Iniciando loop de escaneo cada {self.config['scan_interval']/3600:.1f} horas")
        
        while self.is_running:
            try:
                # Realizar escaneo
                await self._perform_scan()
                
                # Esperar hasta el próximo escaneo
                await asyncio.sleep(self.config['scan_interval'])
                
            except asyncio.CancelledError:
                logger.info("🛑 Scanner cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop de escaneo: {e}")
                # Esperar 5 minutos antes de reintentar en caso de error
                await asyncio.sleep(300)
    
    async def _perform_scan(self):
        """Realiza un escaneo completo de Bitcoin"""
        try:
            scan_start = datetime.now()
            self._add_log("INFO", f"Iniciando escaneo de {self.config['symbol']}", {
                "timestamp": scan_start.strftime('%H:%M:%S')
            })
            
            # 1. Obtener datos de Binance
            df = await self._get_binance_data()
            if df is None or len(df) < 50:
                self._add_log("WARNING", "No se pudieron obtener datos suficientes de Binance")
                return
            
            # 2. Detectar patrones U usando lógica del backtest exitoso
            signals = self._detect_u_pattern_2022(df)
            
            # 3. Procesar señales detectadas
            current_price = df['close'].iloc[-1]
            if signals:
                # Verificar cooldown para evitar spam
                now = datetime.now()
                if self.last_alert_sent and (now - self.last_alert_sent).total_seconds() < self.cooldown_period:
                    remaining_cooldown = self.cooldown_period - (now - self.last_alert_sent).total_seconds()
                    self._add_log("WARNING", f"Patrón U detectado pero en cooldown", {
                        "remaining_minutes": f"{remaining_cooldown/60:.0f}",
                        "current_price": f"${current_price:,.2f}"
                    })
                else:
                    for signal in signals:
                        await self._process_signal(signal, df)
                        self.alerts_count += 1
                        self.last_alert_sent = now
                        self._add_log("SUCCESS", "🚨 ALERTA ENVIADA - Patrón U confirmado", {
                            "price": f"${current_price:,.2f}",
                            "rupture_level": f"${signal['rupture_level']:,.2f}",
                            "next_alert_in": f"{self.cooldown_period/60:.0f} minutos"
                        })
                        break  # Solo una alerta por escaneo
            else:
                self._add_log("INFO", f"Escaneo completado - No se detectaron patrones U", {
                    "current_price": f"${current_price:,.2f}",
                    "candles_analyzed": len(df)
                })
            
            self.last_scan_time = scan_start
            scan_duration = (datetime.now() - scan_start).total_seconds()
            logger.info(f"✅ Escaneo completado en {scan_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en escaneo: {e}")
    
    async def _get_binance_data(self) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de Binance"""
        try:
            # Obtener últimas 200 velas de 4h (suficiente para análisis)
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': self.config['symbol'],
                'interval': self.config['timeframe'], 
                'limit': 200
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            if not klines:
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convertir tipos
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"📊 Datos obtenidos: {len(df)} velas, último precio: ${df['close'].iloc[-1]:,.2f}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de Binance: {e}")
            return None
    
    def _detect_u_pattern_2022(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta patrones U usando la lógica exitosa del backtest 2022
        """
        signals = []
        window_size = min(48, len(df))  # Ventana de análisis (48 velas = 8 días en 4h)
        
        if window_size < 20:
            return signals
            
        # Usar ventana deslizante para detectar patrones
        for end_idx in range(window_size, len(df)):
            start_idx = end_idx - window_size
            window_df = df.iloc[start_idx:end_idx]
            
            # Detectar mínimos locales
            lows = self._detect_lows_2022(window_df)
            if not lows:
                continue
            
            # Analizar cada mínimo como posible base de U
            for low in lows[-3:]:  # Solo últimos 3 mínimos
                min_idx = low['index']
                
                # Verificar condiciones del patrón U
                pre_crash = window_df.iloc[:min_idx]
                post_recovery = window_df.iloc[min_idx:]
                
                if len(pre_crash) < 5 or len(post_recovery) < 5:
                    continue
                
                # Calcular pendientes
                pre_slope = self._calculate_slope(pre_crash['close'].values)
                post_slope = self._calculate_slope(post_recovery['close'].values)
                
                # ATR para nivel de ruptura dinámico
                atr = self._calculate_atr_simple(window_df)
                current_price = window_df.iloc[-1]['close']
                dynamic_factor = self._calculate_rupture_factor_bear(atr, current_price)
                nivel_ruptura = current_price * dynamic_factor
                
                # Filtros MÁS ESTRICTOS del patrón U para evitar falsos positivos
                recent_closes = post_recovery['close'].iloc[-3:].values
                recent_slope = self._calculate_slope(recent_closes) if len(recent_closes) >= 2 else 0
                
                # Verificar momentum mínimo y recuperación significativa
                recovery_pct = (current_price - low['low']) / low['low']
                volume_recent = post_recovery['volume'].iloc[-5:].mean() if len(post_recovery) >= 5 else 0
                volume_avg = window_df['volume'].mean()
                volume_ratio = volume_recent / volume_avg if volume_avg > 0 else 0
                
                conditions = [
                    pre_slope < -0.02,           # Caída previa MÁS significativa
                    post_slope > 0.01,           # Recuperación MÁS fuerte
                    recent_slope > 0.005,        # Momentum reciente POSITIVO
                    low['depth'] >= self.config['min_pattern_depth'] * 1.5,  # Profundidad 50% más estricta
                    recovery_pct >= 0.03,        # Al menos 3% de recuperación desde el mínimo
                    volume_ratio >= 1.2,         # Volumen reciente 20% mayor que promedio
                    len(post_recovery) >= 8,     # Al menos 8 períodos de recuperación
                ]
                
                if all(conditions):
                    signal_strength = min(abs(pre_slope) * 100, 10.0)  # Fuerza entre 0-10
                    
                    signals.append({
                        'timestamp': window_df.index[-1],
                        'symbol': self.config['symbol'],
                        'entry_price': current_price,
                        'rupture_level': nivel_ruptura,
                        'signal_strength': signal_strength,
                        'min_price': low['low'],
                        'pattern_width': len(post_recovery),
                        'depth': low['depth'],
                        'pre_slope': pre_slope,
                        'post_slope': post_slope,
                        'atr': atr
                    })
                    
                    logger.info(f"🎯 PATRÓN U DETECTADO - FILTROS ESTRICTOS PASADOS:")
                    logger.info(f"   💰 Precio actual: ${current_price:,.2f}")
                    logger.info(f"   🚀 Nivel ruptura: ${nivel_ruptura:,.2f} (+{((nivel_ruptura/current_price-1)*100):.2f}%)")
                    logger.info(f"   📊 Fuerza señal: {signal_strength:.1f}/10")
                    logger.info(f"   📉 Profundidad: {low['depth']*100:.1f}% (mín: {self.config['min_pattern_depth']*1.5*100:.1f}%)")
                    logger.info(f"   📈 Recuperación: {recovery_pct*100:.1f}% desde mínimo")
                    logger.info(f"   📊 Volumen ratio: {volume_ratio:.1f}x (>1.2x requerido)")
                    
                    break  # Solo una señal por ventana
        
        return signals
    
    def _detect_lows_2022(self, df: pd.DataFrame, window=8, min_depth_pct=None) -> List[Dict]:
        """Detecta mínimos locales usando lógica del backtest 2022"""
        if min_depth_pct is None:
            min_depth_pct = self.config['min_pattern_depth']
            
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            
            # Ventana alrededor del punto
            window_slice = df.iloc[i-window:i+window+1]
            if current_low == window_slice['low'].min():
                local_high = window_slice['high'].max()
                depth = (local_high - current_low) / local_high
                
                if depth >= min_depth_pct:
                    lows.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'low': current_low,
                        'high': df.iloc[i]['high'],
                        'close': df.iloc[i]['close'],
                        'depth': depth
                    })
        
        return lows
    
    def _calculate_rupture_factor_bear(self, atr: float, price: float, base_factor=1.025) -> float:
        """Factor de ruptura dinámico para bear market"""
        atr_pct = atr / price
        
        if atr_pct < 0.02:
            factor = base_factor
        elif atr_pct < 0.05:
            factor = base_factor + (atr_pct * 0.3)
        else:
            factor = min(base_factor + (atr_pct * 0.5), 1.06)  # Máximo 6%
        
        return max(factor, 1.025)  # Mínimo 2.5%
    
    def _calculate_atr_simple(self, df: pd.DataFrame, period=14) -> float:
        """Calcula ATR simplificado"""
        tr_values = []
        for i in range(1, len(df)):
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']
            prev_close = df.iloc[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        return np.mean(tr_values[-period:]) if tr_values else df.iloc[-1]['high'] - df.iloc[-1]['low']
    
    def _calculate_slope(self, values) -> float:
        """Calcula pendiente de una serie de valores"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    async def _process_signal(self, signal: Dict, df: pd.DataFrame):
        """Procesa una señal detectada y envía alertas"""
        try:
            # Crear mensaje de alerta
            current_price = signal['entry_price']
            rupture_level = signal['rupture_level']
            profit_target = current_price * (1 + self.config['profit_target'])
            stop_loss = current_price * (1 - self.config['stop_loss'])
            
            alert_message = (
                f"🚀 PATRÓN U DETECTADO EN BITCOIN\n\n"
                f"📊 Análisis:\n"
                f"   • Precio actual: ${current_price:,.2f}\n"
                f"   • Nivel ruptura: ${rupture_level:,.2f} (+{((rupture_level/current_price-1)*100):.1f}%)\n"
                f"   • Profundidad: {signal['depth']*100:.1f}%\n"
                f"   • Fuerza señal: {signal['signal_strength']:.1f}/10\n\n"
                f"🎯 Objetivos de trading:\n"
                f"   • 🟢 Take Profit: ${profit_target:,.2f} (+{self.config['profit_target']*100:.0f}%)\n"
                f"   • 🔴 Stop Loss: ${stop_loss:,.2f} (-{self.config['stop_loss']*100:.0f}%)\n\n"
                f"⏰ Detectado: {signal['timestamp'].strftime('%d/%m/%Y %H:%M')} UTC"
            )
            
            # Preparar datos para Telegram
            alert_data = {
                'type': 'BUY',
                'symbol': signal['symbol'],
                'price': current_price,
                'message': alert_message
            }
            
            # Obtener usuarios activos de Telegram
            db = SessionLocal()
            try:
                active_users = crud_users.get_active_telegram_users(db)
                if not active_users:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram para enviar alertas")
                    return
                
                # Enviar broadcast a todos los usuarios activos
                result = telegram_bot.broadcast_alert(alert_data)
                
                logger.info(f"📢 Alerta enviada: {result['sent']}/{result['total_targets']} usuarios")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando señal: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del scanner"""
        return {
            "is_running": self.is_running,
            "config": self.config,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "alerts_count": self.alerts_count,
            "next_scan_in_seconds": self.config['scan_interval'] if self.is_running else None,
            "logs": self.scanner_logs[-20:],  # Últimos 20 logs para el frontend
            "cooldown_remaining": None if not self.last_alert_sent else max(0, self.cooldown_period - (datetime.now() - self.last_alert_sent).total_seconds())
        }

# Instancia global del scanner
bitcoin_scanner = BitcoinScannerService()