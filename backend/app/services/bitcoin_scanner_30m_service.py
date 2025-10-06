# backend/app/services/bitcoin_scanner_30m_service.py

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
from app.db import crud_users, crud_alertas
from app.schemas.alerta_schema import AlertaCreate
from app.telegram.telegram_bot import telegram_bot
from app.services.auto_trading_executor import auto_trading_executor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BitcoinScanner30mService:
    """
    Servicio de scanner automático de Bitcoin usando intervalos de 30 minutos
    Basado en la estrategia exitosa del backtest 30min con parámetros optimizados
    """
    
    def __init__(self):
        self.is_running = False
        self.scan_task = None
        self.config = {
            "timeframe": "30m",             # Cambiado a 30 minutos
            "profit_target": 0.04,          # 4% take profit (igual que backtest 30min)
            "stop_loss": 0.015,             # 1.5% stop loss (igual que backtest 30min)
            "min_pattern_depth": 0.015,     # 1.5% profundidad mínima (igual que backtest 30min)
            "max_hold_periods": 48,         # 48 períodos = 24 horas (igual que backtest 30min)
            "window_size": 48,              # 48 velas = 24 horas de datos (igual que backtest 30min)
            "scan_interval": 30 * 60,       # 30 minutos (1800 segundos)
            "symbol": "BTCUSDT",
            "data_limit": 1000              # 1000 velas
        }
        self.last_scan_time = None
        self.alerts_count = 0
        self.last_alert_sent = None  # Timestamp de la última alerta enviada
        self.cooldown_period = 30 * 60   # 30 minutos de cooldown entre alertas (más frecuente para 30m)
        self.scanner_logs = []  # Lista de logs para mostrar en el frontend
        self.max_logs = 50  # Máximo número de logs a mantener
        
    def update_config(self, new_config: Dict[str, Any]):
        """Actualiza la configuración del scanner (solo admin)"""
        self.config.update(new_config)
        logger.info(f"✅ Configuración 30m actualizada: {self.config}")
    
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
            logger.error(f"🔴 [30m] {message}")
        elif level == "WARNING":
            logger.warning(f"🟡 [30m] {message}")
        elif level == "SUCCESS":
            logger.info(f"🟢 [30m] {message}")
        else:
            logger.info(f"🔵 [30m] {message}")
    
    async def start_scanning(self) -> bool:
        """Inicia el scanner automático 30m"""
        if self.is_running:
            logger.warning("⚠️ Scanner 30m ya está ejecutándose")
            return False
            
        try:
            self.is_running = True
            self.scan_task = asyncio.create_task(self._scan_loop())
            self._add_log("SUCCESS", "Bitcoin Scanner 30m iniciado - Modo automático 24/7", {
                "timeframe": self.config["timeframe"],
                "scan_interval": f"{self.config['scan_interval']/60:.0f} minutos"
            })
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando scanner 30m: {e}")
            self.is_running = False
            return False
    
    async def stop_scanning(self) -> bool:
        """Detiene el scanner automático 30m"""
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
            logger.info("⏹️ Bitcoin Scanner 30m detenido")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo scanner 30m: {e}")
            return False
    
    async def _scan_loop(self):
        """Loop principal del scanner 30m"""
        logger.info(f"🔄 Iniciando loop de escaneo 30m cada {self.config['scan_interval']/60:.1f} minutos")
        
        while self.is_running:
            try:
                # Realizar escaneo
                await self._perform_scan()
                
                # Esperar hasta el próximo escaneo
                await asyncio.sleep(self.config['scan_interval'])
                
            except asyncio.CancelledError:
                logger.info("🛑 Scanner 30m cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error en loop de escaneo 30m: {e}")
                # Esperar 2 minutos antes de reintentar en caso de error
                await asyncio.sleep(120)
    
    async def _perform_scan(self):
        """Realiza un escaneo completo de Bitcoin con timeframe 30m"""
        try:
            scan_start = datetime.now()
            self._add_log("INFO", f"Iniciando escaneo 30m de {self.config['symbol']}", {
                "timestamp": scan_start.strftime('%H:%M:%S')
            })
            
            # 1. Obtener datos de Binance
            df = await self._get_binance_data()
            if df is None or len(df) < 50:
                self._add_log("WARNING", "No se pudieron obtener datos suficientes de Binance")
                return
            
            current_price = df['close'].iloc[-1]
            
            # 1.5. 🤖 MONITOREAR POSICIONES AUTOMÁTICAS (Nueva funcionalidad)
            # Verificar condiciones de salida para trading automático usando las mismas estrategias
            try:
                await auto_trading_executor.check_exit_conditions('btc_30m', current_price)
            except Exception as auto_trade_error:
                logger.error(f"❌ Error monitoreando posiciones automáticas BTC 30m: {auto_trade_error}")
            
            # 2. Detectar patrones U usando lógica del backtest 30m
            signals = self._detect_u_patterns_30m(df)
            
            # 3. Procesar señales detectadas
            if signals:
                # Verificar cooldown para evitar spam
                now = datetime.now()
                if self.last_alert_sent and (now - self.last_alert_sent).total_seconds() < self.cooldown_period:
                    remaining_cooldown = self.cooldown_period - (now - self.last_alert_sent).total_seconds()
                    self._add_log("WARNING", f"Patrón U 30m detectado pero en cooldown", {
                        "remaining_minutes": f"{remaining_cooldown/60:.0f}",
                        "current_price": f"${current_price:,.2f}"
                    })
                else:
                    for signal in signals:
                        await self._process_signal(signal, df)
                        self.alerts_count += 1
                        self.last_alert_sent = now
                        self._add_log("SUCCESS", "🚨 ALERTA 30m ENVIADA - Patrón U confirmado", {
                            "price": f"${current_price:,.2f}",
                            "rupture_level": f"${signal['rupture_level']:,.2f}",
                            "next_alert_in": f"{self.cooldown_period/60:.0f} minutos"
                        })
                        break  # Solo una alerta por escaneo
            else:
                self._add_log("INFO", f"Escaneo 30m completado - No se detectaron patrones de compra", {
                    "current_price": f"${current_price:,.2f}",
                    "candles_analyzed": len(df)
                })
            
            self.last_scan_time = scan_start
            scan_duration = (datetime.now() - scan_start).total_seconds()
            logger.info(f"✅ Escaneo 30m completado en {scan_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en escaneo 30m: {e}")
    
    async def _get_binance_data(self) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de Binance para 30m"""
        try:
            # Obtener últimas 1000 velas de 30m
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': self.config['symbol'],
                'interval': self.config['timeframe'], 
                'limit': self.config['data_limit']  # 1000 velas
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
            
            logger.info(f"📊 Datos 30m obtenidos: {len(df)} velas, último precio: ${df['close'].iloc[-1]:,.2f}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos 30m de Binance: {e}")
            return None
    
    def _detect_u_patterns_30m(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta patrones U usando la lógica EXACTA del backtest 30m
        """
        signals = []
        
        # Usar ventana de análisis igual al backtest 30m 
        window_size = self.config['window_size']  # 48 velas = 24 horas
        
        if len(df) < window_size:
            return signals
            
        # Usar los últimos datos para análisis
        analysis_df = df.iloc[-window_size:].copy()
        
        # Detectar mínimos significativos con parámetros del backtest 30m
        significant_lows = self._detect_lows_30m(analysis_df, window=3, min_depth_pct=self.config['min_pattern_depth'])
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos (igual que backtest 30m)
        for low in significant_lows[-2:]:  # Últimos 2 mínimos (más frecuente)
            min_idx = low['index']
            
            # ATR y factor dinámico (igual que backtest 30m)
            atr = self._calculate_atr_simple(analysis_df)
            current_price = analysis_df.iloc[-1]['close']
            
            # Factor para 30m
            dynamic_factor = self._calculate_rupture_factor_30m(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones EXACTAS del backtest 30m
            if len(analysis_df) - min_idx > 2 and len(analysis_df) - min_idx < 24:  # Entre 1h y 12h
                recent_slope = self._calculate_slope(analysis_df.iloc[-3:]['close'].values)
                pre_slope = self._calculate_slope(analysis_df.iloc[max(0, min_idx-3):min_idx]['close'].values)
                
                # Condiciones EXACTAS del backtest 30m
                conditions = [
                    pre_slope < -0.08,  # Pendiente bajista
                    current_price > nivel_ruptura * 0.98,  # Cerca del nivel de ruptura
                    recent_slope > -0.02,  # Momentum positivo
                    low['depth'] >= self.config['min_pattern_depth'],  # Al menos 1.5% de profundidad
                    self._check_momentum_filter_30m(analysis_df, min_idx)
                ]
                
                if all(conditions):
                    signals.append({
                        'timestamp': analysis_df.index[-1],
                        'entry_price': nivel_ruptura,
                        'signal_strength': abs(pre_slope),
                        'min_price': low['low'],
                        'pattern_width': len(analysis_df) - min_idx,
                        'atr': atr,
                        'dynamic_factor': dynamic_factor,
                        'depth': low['depth'],
                        'rupture_level': nivel_ruptura,
                        'symbol': 'BTCUSDT'
                    })
                    
                    logger.info(f"🎯 PATRÓN U 30m DETECTADO - ALGORITMO BACKTEST 30m:")
                    logger.info(f"   💰 Precio actual: ${current_price:,.2f}")
                    logger.info(f"   🚀 Nivel ruptura: ${nivel_ruptura:,.2f} (+{((nivel_ruptura/current_price-1)*100):.2f}%)")
                    logger.info(f"   📊 Fuerza señal: {abs(pre_slope):.3f}")
                    logger.info(f"   📉 Profundidad: {low['depth']*100:.1f}%")
                    logger.info(f"   📏 Ancho patrón: {len(analysis_df) - min_idx} períodos")
                    
                    break  # Solo una señal por ventana
                    
        return signals
    
    def _detect_lows_30m(self, df: pd.DataFrame, window=3, min_depth_pct=0.015) -> List[Dict]:
        """Detecta mínimos optimizados para intervalos de 30min"""
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            
            window_slice = df.iloc[i-window:i+window+1]
            if current_low == window_slice['low'].min():
                local_high = window_slice['high'].max()
                depth = (local_high - current_low) / local_high
                
                if depth >= min_depth_pct and i < len(df) - 2:
                    # Verificar volumen para confirmar el mínimo
                    volume_avg = df.iloc[i-window:i+window+1]['volume'].mean()
                    current_volume = df.iloc[i]['volume']
                    
                    if current_volume > volume_avg * 0.7 or depth >= 0.025:
                        lows.append({
                            'index': i,
                            'timestamp': df.index[i],
                            'low': current_low,
                            'high': df.iloc[i]['high'],
                            'close': df.iloc[i]['close'],
                            'volume': df.iloc[i]['volume'],
                            'depth': depth
                        })
        
        return lows
    
    def _calculate_rupture_factor_30m(self, atr: float, price: float, base_factor=1.008) -> float:
        """Factor de ruptura optimizado para 30min (más conservador)"""
        atr_pct = atr / price
        
        # Más conservador para timeframe corto
        if atr_pct < 0.01:
            factor = base_factor
        elif atr_pct < 0.02:
            factor = base_factor + (atr_pct * 0.2)
        else:
            factor = min(base_factor + (atr_pct * 0.3), 1.025)  # Máximo 2.5% para 30min
        
        return max(factor, 1.008)  # Mínimo 0.8%
    
    def _check_momentum_filter_30m(self, df, min_idx):
        """Filtro de momentum para timeframe de 30min"""
        if min_idx < 10:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia de los últimos 10 períodos (5 horas)
        recent_10 = df.iloc[-10:]['close'].values
        trend_slope = self._calculate_slope(recent_10)
        
        # Permitir trades si la tendencia no es muy bajista
        return trend_slope > -0.05
    
    def _calculate_atr_simple(self, df: pd.DataFrame, period=7) -> float:
        """Calcula ATR simplificado para 30min"""
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
                f"🚀 PATRÓN U 30m DETECTADO EN BITCOIN\n\n"
                f"📊 Análisis (30 minutos):\n"
                f"   • Precio actual: ${current_price:,.2f}\n"
                f"   • Nivel ruptura: ${rupture_level:,.2f} (+{((rupture_level/current_price-1)*100):.1f}%)\n"
                f"   • Profundidad: {signal['depth']*100:.1f}%\n"
                f"   • Fuerza señal: {signal['signal_strength']:.1f}/10\n\n"
                f"🎯 Objetivos de trading (30m):\n"
                f"   • 🟢 Take Profit: ${profit_target:,.2f} (+{self.config['profit_target']*100:.0f}%)\n"
                f"   • 🔴 Stop Loss: ${stop_loss:,.2f} (-{self.config['stop_loss']*100:.1f}%)\n"
                f"   • ⏰ Max Hold: 24 horas\n\n"
                f"⏰ Detectado: {signal['timestamp'].strftime('%d/%m/%Y %H:%M')} UTC"
            )
            
            # Preparar datos para Telegram
            alert_data = {
                'type': 'BUY',
                'symbol': signal['symbol'],
                'price': current_price,
                'message': alert_message
            }
            
            # Obtener usuarios activos de Telegram y guardar en DB
            db = SessionLocal()
            try:
                # 1. Guardar alerta en base de datos PRIMERO
                alerta_create = AlertaCreate(
                    ticker=signal['symbol'],
                    crypto_symbol='BTC_30m',
                    tipo_alerta='BUY',
                    mensaje=alert_message,
                    nivel_ruptura=rupture_level,
                    precio_entrada=current_price,
                    bot_mode='automatic_30m'
                )
                
                alerta_db = crud_alertas.create_alerta(db=db, alerta=alerta_create, usuario_id=None)
                logger.info(f"💾 BTC 30m Alerta guardada en DB con ID: {alerta_db.id}")
                
                # 2. Luego enviar por Telegram
                active_users = crud_users.get_active_telegram_users(db)
                if not active_users:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram para enviar alertas 30m")
                else:
                    # Enviar broadcast a todos los usuarios activos
                    result = telegram_bot.broadcast_alert(alert_data)
                    logger.info(f"📢 BTC 30m Alerta enviada: {result['sent']}/{result['total_targets']} usuarios")
                
                # 3. Actualizar contador de alertas
                self.alerts_count += 1
                self.last_alert_sent = datetime.now()
                
                # 4. 🤖 EJECUTAR TRADING AUTOMÁTICO (Nueva funcionalidad)
                # Usar las mismas estrategias probadas (4% TP, 1.5% SL)
                try:
                    signal_data = {
                        'entry_price': current_price,
                        'rupture_level': rupture_level,
                        'profit_target': profit_target,
                        'stop_loss': stop_loss,
                        'signal_strength': signal.get('signal_strength', 0),
                        'depth': signal.get('depth', 0),
                        'timestamp': signal.get('timestamp', datetime.now())
                    }
                    
                    # Ejecutar trading automático para usuarios que lo tengan habilitado
                    await auto_trading_executor.execute_buy_signal('btc_30m', signal_data, alerta_db.id)
                    
                    self._add_log("SUCCESS", "🤖 Trading automático 30m ejecutado para usuarios habilitados", {
                        "crypto": "BTC_30m",
                        "entry_price": f"${current_price:.2f}",
                        "alerta_id": alerta_db.id
                    })
                    
                except Exception as trading_error:
                    logger.error(f"❌ Error en trading automático BTC 30m: {trading_error}")
                    self._add_log("ERROR", f"Error en trading automático 30m: {str(trading_error)}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando señal 30m: {e}")
    
    async def _monitor_open_positions(self, current_price: float):
        """Monitorea posiciones abiertas BTC 30m y crea alertas SELL cuando se alcanzan TP/SL/MaxHold"""
        try:
            db = SessionLocal()
            
            # Obtener posiciones abiertas (alertas BUY sin SELL correspondiente)
            open_positions = crud_alertas.get_open_positions(db, crypto_symbol='BTC_30m')
            
            if not open_positions:
                return
                
            logger.info(f"📊 Monitoreando {len(open_positions)} posiciones BTC 30m abiertas")
            
            for position in open_positions:
                entry_price = position.precio_entrada
                entry_time = position.fecha_creacion
                
                # Calcular precios objetivo usando la lógica del backtest 30m
                target_price = entry_price * (1 + self.config['profit_target'])  # 4% TP
                stop_price = entry_price * (1 - self.config['stop_loss'])        # 1.5% SL
                
                # Verificar tiempo máximo de holding (48 períodos de 30m = 24 horas)
                max_hold_minutes = self.config['max_hold_periods'] * 30  # 48 * 30m = 1440m = 24h
                minutes_held = (datetime.now() - entry_time).total_seconds() / 60
                
                # Condiciones de salida (misma lógica que backtest 30m)
                exit_reason = None
                exit_price = current_price
                
                if current_price >= target_price:
                    exit_reason = "TAKE_PROFIT"
                    exit_price = target_price
                elif current_price <= stop_price:
                    exit_reason = "STOP_LOSS" 
                    exit_price = stop_price
                elif minutes_held >= max_hold_minutes:
                    exit_reason = "MAX_HOLD"
                    exit_price = current_price
                
                if exit_reason:
                    # Crear alerta de venta usando la función existente
                    sell_alert = crud_alertas.create_sell_alert(
                        db=db,
                        buy_alert_id=position.id,
                        precio_salida=exit_price,
                        bot_mode='automatic_30m'
                    )
                    
                    logger.info(f"🚨 BTC 30m SELL creada - ID: {sell_alert.id} | Razón: {exit_reason} | "
                              f"Precio: ${exit_price:.2f} | Profit: ${sell_alert.profit_usd:.2f}")
                    
                    # Enviar por Telegram
                    await self._send_sell_alert_telegram(sell_alert, exit_reason)
            
            db.close()
                
        except Exception as e:
            logger.error(f"❌ Error monitoreando posiciones BTC 30m: {e}")
    
    async def _send_sell_alert_telegram(self, sell_alert, exit_reason: str):
        """Envía alerta de venta BTC 30m por Telegram"""
        try:
            # Crear mensaje de venta
            profit_emoji = "🟢" if sell_alert.profit_usd > 0 else "🔴" if sell_alert.profit_usd < 0 else "⚪"
            reason_emoji = {"TAKE_PROFIT": "🎯", "STOP_LOSS": "🛑", "MAX_HOLD": "⏰"}.get(exit_reason, "📤")
            
            alert_message = (
                f"{reason_emoji} VENTA BITCOIN 30m - {exit_reason}\n\n"
                f"📊 Resultado (30 minutos):\n"
                f"   • Precio venta: ${sell_alert.precio_salida:.2f}\n"
                f"   • Precio entrada: ${sell_alert.precio_entrada:.2f}\n"
                f"   • Ganancia: ${sell_alert.profit_usd:.2f} ({sell_alert.profit_percentage:.2f}%)\n"
                f"   • Cantidad: {sell_alert.cantidad:.8f} BTC\n\n"
                f"⏰ Ejecutado: {sell_alert.fecha_creacion.strftime('%d/%m/%Y %H:%M')} UTC"
            )
            
            # Preparar datos para Telegram
            alert_data = {
                'type': 'SELL',
                'symbol': sell_alert.ticker,
                'price': sell_alert.precio_salida,
                'message': alert_message
            }
            
            # Obtener usuarios activos de Telegram para Bitcoin 30m
            db = SessionLocal()
            try:
                active_users = crud_users.get_active_telegram_users_by_crypto(db, 'btc_30m')
                if active_users:
                    result = telegram_bot.broadcast_alert(alert_data)
                    logger.info(f"📢 BTC 30m SELL Telegram enviada: {result['sent']}/{result['total_targets']} usuarios")
                else:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram BTC 30m para alertas SELL")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error enviando alerta SELL BTC 30m por Telegram: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del scanner 30m"""
        # Verificar si realmente está corriendo basándose en los logs recientes
        is_actually_running = self.is_running
        
        # Si no está marcado como corriendo pero hay logs recientes, asumir que está corriendo
        if not self.is_running and self.scanner_logs:
            last_log_time = None
            for log in reversed(self.scanner_logs):
                if log.get('timestamp'):
                    try:
                        last_log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                        break
                    except:
                        continue
            
            if last_log_time:
                minutes_since_last_log = (datetime.now() - last_log_time.replace(tzinfo=None)).total_seconds() / 60
                # Si hay logs en los últimos 35 minutos, asumir que está corriendo
                if minutes_since_last_log < 35:
                    is_actually_running = True
                    logger.info(f"🔄 Scanner 30m detectado como activo por logs recientes (último: {minutes_since_last_log:.1f} min)")
        
        # Si hay logs pero no hay timestamp del último escaneo, usar el timestamp del último log
        last_scan_time = self.last_scan_time
        if not last_scan_time and self.scanner_logs:
            for log in reversed(self.scanner_logs):
                if log.get('timestamp'):
                    try:
                        last_scan_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                        break
                    except:
                        continue
        
        return {
            "is_running": is_actually_running,
            "config": self.config,
            "last_scan_time": last_scan_time.isoformat() if last_scan_time else None,
            "alerts_count": self.alerts_count,
            "next_scan_in_seconds": self.config['scan_interval'] if is_actually_running else None,
            "logs": self.scanner_logs[-1000:],  # Últimos 1000 logs para el frontend
            "cooldown_remaining": None if not self.last_alert_sent else max(0, self.cooldown_period - (datetime.now() - self.last_alert_sent).total_seconds()),
            "timeframe": "30m"
        }

# Instancia global del scanner 30m
bitcoin_scanner_30m = BitcoinScanner30mService()