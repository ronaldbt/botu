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
from app.db import crud_users, crud_alertas
from app.schemas.alerta_schema import AlertaCreate
from app.telegram.telegram_bot import telegram_bot
from app.services.auto_trading_executor import auto_trading_executor

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
            "profit_target": 0.08,     # 8% take profit (igual que backtest 2023)
            "stop_loss": 0.03,         # 3% stop loss (igual que backtest 2023)
            "min_pattern_depth": 0.025, # 2.5% profundidad mínima (igual que backtest 2023)
            "max_hold_periods": 80,    # 80 períodos = 13 días (igual que backtest 2023)
            "window_size": 120,        # 120 velas ventana análisis (igual que backtest 2023)
            "scan_interval": 60 * 60,   # 1 hora (3600 segundos)
            "symbol": "BTCUSDT",
            "data_limit": 1000         # 1000 velas como backtest 2023
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
            
            current_price = df['close'].iloc[-1]
            
            # 1.5. 🤖 MONITOREAR POSICIONES AUTOMÁTICAS (Nueva funcionalidad)
            # Verificar condiciones de salida para trading automático usando las mismas estrategias
            try:
                await auto_trading_executor.check_exit_conditions('btc', current_price)
            except Exception as auto_trade_error:
                logger.error(f"❌ Error monitoreando posiciones automáticas BTC: {auto_trade_error}")
            
            # 2. Detectar patrones U usando lógica exacta del backtest 2023
            signals = self._detect_u_patterns_2023(df)
            
            # 3. Procesar señales detectadas
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
                self._add_log("INFO", f"Escaneo completado - No se detectaron patrones de compra", {
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
            # Obtener últimas 1000 velas de 4h (igual que backtest 2023)
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
            
            logger.info(f"📊 Datos obtenidos: {len(df)} velas, último precio: ${df['close'].iloc[-1]:,.2f}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de Binance: {e}")
            return None
    
    def _detect_u_patterns_2023(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta patrones U usando la lógica EXACTA del backtest 2023
        """
        signals = []
        
        # Usar ventana de análisis igual al backtest 2023 
        window_size = self.config['window_size']  # 120 velas
        
        if len(df) < window_size:
            return signals
            
        # Usar los últimos datos para análisis (simulando ventana final del backtest)
        analysis_df = df.iloc[-window_size:].copy()
        
        # Detectar mínimos significativos con parámetros del backtest 2023
        significant_lows = self._detect_lows_2023(analysis_df, window=6, min_depth_pct=self.config['min_pattern_depth'])
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos (igual que backtest 2023)
        for low in significant_lows[-4:]:  # Últimos 4 mínimos
            min_idx = low['index']
            
            # ATR y factor dinámico (igual que backtest 2023)
            atr = self._calculate_atr_simple(analysis_df)
            current_price = analysis_df.iloc[-1]['close']
            
            # Factor para bull market (igual que backtest 2023)
            dynamic_factor = self._calculate_rupture_factor_bull(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones EXACTAS del backtest 2023
            if len(analysis_df) - min_idx > 4 and len(analysis_df) - min_idx < 45:
                recent_slope = self._calculate_slope(analysis_df.iloc[-6:]['close'].values)
                pre_slope = self._calculate_slope(analysis_df.iloc[max(0, min_idx-6):min_idx]['close'].values)
                
                # Condiciones EXACTAS del backtest 2023
                conditions = [
                    pre_slope < -0.12,  # Más restrictivo para BTC
                    current_price > nivel_ruptura * 0.97,  # Más conservador (97% vs 95%)
                    recent_slope > -0.03,  # Momentum más positivo requerido
                    low['depth'] >= self.config['min_pattern_depth'],  # Al menos 2.5% de profundidad
                    # Filtro adicional: evitar trades en tendencias bajistas prolongadas
                    self._check_momentum_filter(analysis_df, min_idx)
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
                        'symbol': 'BTCUSDT'  # Add missing symbol
                    })
                    
                    logger.info(f"🎯 PATRÓN U DETECTADO - ALGORITMO BACKTEST 2023:")
                    logger.info(f"   💰 Precio actual: ${current_price:,.2f}")
                    logger.info(f"   🚀 Nivel ruptura: ${nivel_ruptura:,.2f} (+{((nivel_ruptura/current_price-1)*100):.2f}%)")
                    logger.info(f"   📊 Fuerza señal: {abs(pre_slope):.3f}")
                    logger.info(f"   📉 Profundidad: {low['depth']*100:.1f}%")
                    logger.info(f"   📏 Ancho patrón: {len(analysis_df) - min_idx} períodos")
                    
                    break  # Solo una señal por ventana
                    
        return signals
    
    def _detect_lows_2023(self, df: pd.DataFrame, window=6, min_depth_pct=0.025) -> List[Dict]:
        """Detecta mínimos EXACTOS del backtest 2023"""
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            
            window_slice = df.iloc[i-window:i+window+1]
            if current_low == window_slice['low'].min():
                local_high = window_slice['high'].max()
                depth = (local_high - current_low) / local_high
                
                # Filtro adicional: verificar que no sea un mínimo muy reciente
                if depth >= min_depth_pct and i < len(df) - 5:
                    # Verificar volumen para confirmar el mínimo
                    volume_avg = df.iloc[i-window:i+window+1]['volume'].mean()
                    current_volume = df.iloc[i]['volume']
                    
                    # Solo incluir si hay volumen suficiente o es un mínimo significativo
                    if current_volume > volume_avg * 0.8 or depth >= 0.04:
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
    
    def _calculate_rupture_factor_bull(self, atr: float, price: float, base_factor=1.015) -> float:
        """Factor de ruptura EXACTO del backtest 2023"""
        atr_pct = atr / price
        
        # Parámetros exactos del backtest 2023
        if atr_pct < 0.015:
            factor = base_factor
        elif atr_pct < 0.03:
            factor = base_factor + (atr_pct * 0.3)  
        else:
            factor = min(base_factor + (atr_pct * 0.5), 1.05)  # Máximo 5%
        
        return max(factor, 1.015)  # Mínimo 1.5%
    
    def _check_momentum_filter(self, df, min_idx):
        """Filtro de momentum EXACTO del backtest 2023"""
        if min_idx < 20:
            return True  
        
        # Verificar tendencia de los últimos 20 períodos
        recent_20 = df.iloc[-20:]['close'].values
        trend_slope = self._calculate_slope(recent_20)
        
        # Solo permitir trades si pendiente > -0.1 (igual que backtest 2023)
        return trend_slope > -0.1
    
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
            
            # Obtener usuarios activos de Telegram y guardar en DB
            db = SessionLocal()
            try:
                # 1. Guardar alerta en base de datos PRIMERO
                alerta_create = AlertaCreate(
                    ticker=signal['symbol'],
                    crypto_symbol='BTC',
                    tipo_alerta='BUY',
                    mensaje=alert_message,
                    nivel_ruptura=rupture_level,
                    precio_entrada=current_price,
                    bot_mode='automatic'
                )
                
                alerta_db = crud_alertas.create_alerta(db=db, alerta=alerta_create, usuario_id=None)
                logger.info(f"💾 BTC Alerta guardada en DB con ID: {alerta_db.id}")
                
                # 2. Luego enviar por Telegram
                active_users = crud_users.get_active_telegram_users(db)
                if not active_users:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram para enviar alertas")
                else:
                    # Enviar broadcast a todos los usuarios activos
                    result = telegram_bot.broadcast_alert(alert_data)
                    logger.info(f"📢 BTC Alerta enviada: {result['sent']}/{result['total_targets']} usuarios")
                
                # 3. Actualizar contador de alertas
                self.alerts_count += 1
                self.last_alert_sent = datetime.now()
                
                # 4. 🤖 EJECUTAR TRADING AUTOMÁTICO (Nueva funcionalidad)
                # Usar las mismas estrategias probadas (8% TP, 3% SL)
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
                    await auto_trading_executor.execute_buy_signal('btc', signal_data, alerta_db.id)
                    
                    self._add_log("SUCCESS", "🤖 Trading automático ejecutado para usuarios habilitados", {
                        "crypto": "BTC",
                        "entry_price": f"${current_price:.2f}",
                        "alerta_id": alerta_db.id
                    })
                    
                except Exception as trading_error:
                    logger.error(f"❌ Error en trading automático BTC: {trading_error}")
                    self._add_log("ERROR", f"Error en trading automático: {str(trading_error)}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando señal: {e}")
    
    async def _monitor_open_positions(self, current_price: float):
        """Monitorea posiciones abiertas BTC y crea alertas SELL cuando se alcanzan TP/SL/MaxHold"""
        try:
            db = SessionLocal()
            
            # Obtener posiciones abiertas (alertas BUY sin SELL correspondiente)
            open_positions = crud_alertas.get_open_positions(db, crypto_symbol='BTC')
            
            if not open_positions:
                return
                
            logger.info(f"📊 Monitoreando {len(open_positions)} posiciones BTC abiertas")
            
            for position in open_positions:
                entry_price = position.precio_entrada
                entry_time = position.fecha_creacion
                
                # Calcular precios objetivo usando la lógica del backtest Bitcoin 2023
                target_price = entry_price * (1 + self.config['profit_target'])  # 8% TP
                stop_price = entry_price * (1 - self.config['stop_loss'])        # 3% SL
                
                # Verificar tiempo máximo de holding (80 períodos de 4h = 13 días)
                max_hold_hours = self.config['max_hold_periods'] * 4  # 80 * 4h = 320h = 13.3 días
                hours_held = (datetime.now() - entry_time).total_seconds() / 3600
                
                # Condiciones de salida (misma lógica que backtest Bitcoin 2023)
                exit_reason = None
                exit_price = current_price
                
                if current_price >= target_price:
                    exit_reason = "TAKE_PROFIT"
                    exit_price = target_price
                elif current_price <= stop_price:
                    exit_reason = "STOP_LOSS" 
                    exit_price = stop_price
                elif hours_held >= max_hold_hours:
                    exit_reason = "MAX_HOLD"
                    exit_price = current_price
                
                if exit_reason:
                    # Crear alerta de venta usando la función existente
                    sell_alert = crud_alertas.create_sell_alert(
                        db=db,
                        buy_alert_id=position.id,
                        precio_salida=exit_price,
                        bot_mode='automatic'
                    )
                    
                    logger.info(f"🚨 BTC SELL creada - ID: {sell_alert.id} | Razón: {exit_reason} | "
                              f"Precio: ${exit_price:.2f} | Profit: ${sell_alert.profit_usd:.2f}")
                    
                    # Enviar por Telegram
                    await self._send_sell_alert_telegram(sell_alert, exit_reason)
            
            db.close()
                
        except Exception as e:
            logger.error(f"❌ Error monitoreando posiciones BTC: {e}")
    
    async def _send_sell_alert_telegram(self, sell_alert, exit_reason: str):
        """Envía alerta de venta BTC por Telegram"""
        try:
            # Crear mensaje de venta
            profit_emoji = "🟢" if sell_alert.profit_usd > 0 else "🔴" if sell_alert.profit_usd < 0 else "⚪"
            reason_emoji = {"TAKE_PROFIT": "🎯", "STOP_LOSS": "🛑", "MAX_HOLD": "⏰"}.get(exit_reason, "📤")
            
            alert_message = (
                f"{reason_emoji} VENTA BITCOIN - {exit_reason}\n\n"
                f"📊 Resultado:\n"
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
            
            # Obtener usuarios activos de Telegram para Bitcoin
            db = SessionLocal()
            try:
                active_users = crud_users.get_active_telegram_users_by_crypto(db, 'btc')
                if active_users:
                    result = telegram_bot.broadcast_alert(alert_data)
                    logger.info(f"📢 BTC SELL Telegram enviada: {result['sent']}/{result['total_targets']} usuarios")
                else:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram BTC para alertas SELL")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error enviando alerta SELL BTC por Telegram: {e}")
    
    async def scan_continuous(self):
        """Escaneo continuo en segundo plano - Bitcoin nunca se detiene"""
        self.add_log("info", "🚀 Iniciando escaneo continuo BITCOIN 24/7")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                self.add_log("info", f"📊 Escaneando Bitcoin... {current_time.strftime('%H:%M:%S')}")
                
                # Obtener datos de Binance con retry robusto
                df = await self._get_binance_data()
                if df is None:
                    self.add_log("error", "❌ Error obteniendo datos de Binance - reintentando en 30s")
                    await asyncio.sleep(30)  # Esperar 30s antes del siguiente intento
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # 1. MONITOREAR POSICIONES ABIERTAS PRIMERO
                await self._monitor_open_positions(current_price)
                
                # 2. DETECTAR NUEVOS PATRONES U usando estrategia Bitcoin 2023
                signals = self._detect_u_patterns_2023(df)
                
                if signals:
                    self.add_log("success", f"🎯 {len(signals)} patrón(es) U detectado(s) en Bitcoin")
                    
                    # Procesar solo la primera señal para evitar spam
                    signal = signals[0]
                    
                    # Verificar cooldown (solo una alerta por hora)
                    if self._should_send_alert():
                        await self._process_signal(signal, df)
                        self.last_scan_time = current_time
                    else:
                        self.add_log("info", f"⏳ Cooldown activo Bitcoin - Última alerta: {self.last_alert_sent}")
                else:
                    self.add_log("info", "👀 Sin patrones U detectados en Bitcoin")
                
                self.last_scan_time = current_time
                
                # Esperar el intervalo configurado antes del próximo escaneo
                await asyncio.sleep(self.config['scan_interval'])
                
            except asyncio.CancelledError:
                self.add_log("info", "🛑 Escaneo Bitcoin cancelado")
                break
            except Exception as e:
                self.add_log("error", f"❌ Error crítico en escaneo Bitcoin: {e}")
                # En caso de error crítico, esperar más tiempo antes de reintentar
                await asyncio.sleep(120)  # 2 minutos
        
        self.add_log("info", "🏁 Escaneo continuo Bitcoin terminado")
    
    def get_current_analysis(self) -> Dict[str, Any]:
        """Obtiene análisis actual de Bitcoin usando scanner optimizado 2023"""
        try:
            # Obtener datos actuales
            df = self._get_historical_data()
            if df is None or len(df) < 50:
                return {
                    "current_price": 0,
                    "nivel_ruptura": None,
                    "estado_sugerido": "ERROR",
                    "signal_strength": 0,
                    "slope_left": None,
                    "min_local_depth": None,
                    "pattern_description": "Error obteniendo datos"
                }
            
            current_price = df.iloc[-1]['close']
            
            # Usar el mismo algoritmo de detección que el scanner
            signals = self._detect_u_pattern_2023(df)
            
            if signals:
                signal = signals[0]  # Tomar la primera señal
                return {
                    "current_price": current_price,
                    "nivel_ruptura": signal['rupture_level'],
                    "estado_sugerido": "PATTERN_DETECTED",
                    "signal_strength": signal['signal_strength'],
                    "slope_left": signal.get('slope_left'),
                    "min_local_depth": signal['depth'],
                    "pattern_description": f"Patrón U detectado - Fuerza: {signal['signal_strength']:.1f}/10"
                }
            else:
                return {
                    "current_price": current_price,
                    "nivel_ruptura": None,
                    "estado_sugerido": "NO_PATTERN",
                    "signal_strength": 0,
                    "slope_left": None,
                    "min_local_depth": None,
                    "pattern_description": "Monitoreando patrones U optimizados 2023"
                }
                
        except Exception as e:
            logger.error(f"❌ Error en análisis actual Bitcoin: {e}")
            return {
                "current_price": 0,
                "nivel_ruptura": None,
                "estado_sugerido": "ERROR",
                "signal_strength": 0,
                "slope_left": None,
                "min_local_depth": None,
                "pattern_description": f"Error: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del scanner"""
        return {
            "is_running": self.is_running,
            "config": self.config,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "alerts_count": self.alerts_count,
            "next_scan_in_seconds": self.config['scan_interval'] if self.is_running else None,
            "logs": self.scanner_logs[-1000:],  # Últimos 1000 logs para el frontend
            "cooldown_remaining": None if not self.last_alert_sent else max(0, self.cooldown_period - (datetime.now() - self.last_alert_sent).total_seconds())
        }

# Instancia global del scanner
bitcoin_scanner = BitcoinScannerService()