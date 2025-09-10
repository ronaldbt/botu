# backend/app/services/eth_scanner_service.py

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

class EthScannerService:
    """
    Servicio de scanner automático de Ethereum usando la lógica exitosa del backtest 2022
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
            "scan_interval": 5 * 60,   # 5 minutos para testing
            "symbol": "ETHUSDT",
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
        logger.info(f"✅ Configuración ETH actualizada: {self.config}")
    
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
            logger.error(f"🔴 ETH {message}")
        elif level == "WARNING":
            logger.warning(f"🟡 ETH {message}")
        elif level == "SUCCESS":
            logger.info(f"🟢 ETH {message}")
        else:
            logger.info(f"🔵 ETH {message}")
    
    async def start_scanning(self) -> bool:
        """Inicia el scanner automático"""
        if self.is_running:
            logger.warning("⚠️ ETH Scanner ya está ejecutándose")
            return False
            
        try:
            self.is_running = True
            self.scan_task = asyncio.create_task(self._scan_loop())
            self._add_log("SUCCESS", "Ethereum Scanner iniciado - Modo automático 24/7", {
                "timeframe": self.config["timeframe"],
                "scan_interval": f"{self.config['scan_interval']/60:.0f} minutos"
            })
            return True
        except Exception as e:
            logger.error(f"❌ Error iniciando ETH scanner: {e}")
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
            logger.info("⏹️ Ethereum Scanner detenido")
            return True
        except Exception as e:
            logger.error(f"❌ Error deteniendo ETH scanner: {e}")
            return False
    
    async def _scan_loop(self):
        """Loop principal del scanner"""
        logger.info(f"🔄 ETH Iniciando loop de escaneo cada {self.config['scan_interval']/3600:.1f} horas")
        
        while self.is_running:
            try:
                # Realizar escaneo
                await self._perform_scan()
                
                # Esperar hasta el próximo escaneo
                await asyncio.sleep(self.config['scan_interval'])
                
            except asyncio.CancelledError:
                logger.info("🛑 ETH Scanner cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Error crítico en loop de escaneo ETH: {e}")
                self._add_log("ERROR", f"Error crítico en scanner: {str(e)}")
                # Esperar tiempo progresivo para evitar bucles de errores
                await asyncio.sleep(min(300, 60 * (1 + len([log for log in self.scanner_logs if log.get('level') == 'ERROR']))))
    
    async def _perform_scan(self):
        """Realiza un escaneo completo de Ethereum"""
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
            
            # 2. Detectar patrones U usando lógica exacta del backtest 2023
            signals = self._detect_u_patterns_2023(df)
            
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
            logger.info(f"✅ ETH Escaneo completado en {scan_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error en escaneo ETH: {e}")
    
    async def _get_binance_data(self) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de Binance para ETH con reintentos"""
        max_retries = 3
        for retry in range(max_retries):
            try:
                # Obtener últimas 500 velas de 4h (optimizado servidor)
                url = "https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': self.config['symbol'],
                    'interval': self.config['timeframe'], 
                    'limit': self.config['data_limit']  # 500 velas
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                klines = response.json()
                if not klines:
                    raise ValueError("No se recibieron datos de Binance")
                
                # Convertir a DataFrame
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                
                # Convertir tipos con validación
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Validar que no hay NaN
                if df[['open', 'high', 'low', 'close']].isnull().any().any():
                    raise ValueError("Datos inválidos recibidos de Binance")
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                logger.info(f"📊 ETH Datos obtenidos: {len(df)} velas, último precio: ${df['close'].iloc[-1]:,.2f}")
                return df
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ ETH Timeout en intento {retry + 1}/{max_retries}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry)  # Backoff exponencial
                    continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"🌐 ETH Error de red en intento {retry + 1}/{max_retries}: {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry)
                    continue
            except Exception as e:
                logger.error(f"❌ Error crítico obteniendo datos ETH: {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry)
                    continue
                    
        logger.error(f"❌ ETH Falló después de {max_retries} intentos")
        return None
    
    def _detect_u_patterns_2023(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta patrones U usando la lógica EXACTA del backtest ETH 2023
        """
        signals = []
        
        # Validaciones de seguridad
        if df is None or len(df) < 50:
            logger.warning("ETH: DataFrame insuficiente para análisis")
            return signals
            
        # Usar ventana de análisis igual al backtest 2023 
        window_size = min(self.config['window_size'], len(df) - 20)  # 120 velas o menos
        
        if window_size < 50:
            logger.warning(f"ETH: Ventana muy pequeña: {window_size}")
            return signals
            
        # Usar los últimos datos para análisis (simulando ventana final del backtest)
        analysis_df = df.iloc[-window_size:].copy()
        
        # Detectar mínimos significativos optimizados para ETH
        significant_lows = self._detect_lows_2023(analysis_df, window=6, min_depth_pct=self.config['min_pattern_depth'])
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos (igual que backtest 2023)
        for low in significant_lows[-3:]:  # Últimos 3 mínimos
            min_idx = low['index']
            
            # ATR y factor dinámico (igual que backtest 2023)
            atr = self._calculate_atr_simple(analysis_df)
            current_price = analysis_df.iloc[-1]['close']
            
            # Factor optimizado para ETH
            dynamic_factor = self._calculate_rupture_factor_bull(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones optimizadas para ETH en bull market
            if len(analysis_df) - min_idx > 4 and len(analysis_df) - min_idx < 45:
                recent_slope = self._calculate_slope(analysis_df.iloc[-6:]['close'].values)
                pre_slope = self._calculate_slope(analysis_df.iloc[max(0, min_idx-6):min_idx]['close'].values)
                
                # Condiciones más estrictas para ETH (menos volátil) - EXACTAS del backtest 2023
                conditions = [
                    pre_slope < -0.12,  # Más restrictivo para ETH
                    current_price > nivel_ruptura * 0.97,  # Más conservador (97% vs 95%)
                    recent_slope > -0.03,  # Momentum más positivo requerido
                    low['depth'] >= 0.025,  # Al menos 2.5% de profundidad
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
                        'rupture_level': nivel_ruptura
                    })
                    
                    logger.info(f"🎯 ETH PATRÓN U DETECTADO - ALGORITMO BACKTEST 2023:")
                    logger.info(f"   💰 Precio actual: ${current_price:,.2f}")
                    logger.info(f"   🚀 Nivel ruptura: ${nivel_ruptura:,.2f} (+{((nivel_ruptura/current_price-1)*100):.2f}%)")
                    logger.info(f"   📊 Fuerza señal: {abs(pre_slope):.3f}")
                    logger.info(f"   📉 Profundidad: {low['depth']*100:.1f}%")
                    logger.info(f"   📏 Ancho patrón: {len(analysis_df) - min_idx} períodos")
                    
                    break  # Solo una señal por ventana
                    
        return signals
    
    def _detect_lows_2023(self, df: pd.DataFrame, window=6, min_depth_pct=0.025) -> List[Dict]:
        """Detecta mínimos EXACTOS del backtest ETH 2023"""
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
        """Factor de ruptura EXACTO del backtest ETH 2023"""
        atr_pct = atr / price
        
        # Parámetros exactos del backtest ETH 2023
        if atr_pct < 0.015:
            factor = base_factor
        elif atr_pct < 0.03:
            factor = base_factor + (atr_pct * 0.3)  
        else:
            factor = min(base_factor + (atr_pct * 0.5), 1.05)  # Máximo 5%
        
        return max(factor, 1.015)  # Mínimo 1.5%
    
    def _check_momentum_filter(self, df, min_idx):
        """Filtro de momentum EXACTO del backtest ETH 2023"""
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
                f"🚀 PATRÓN U DETECTADO EN ETHEREUM\n\n"
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
                'message': alert_message,
                'crypto_type': 'eth'  # Identificador para routing de telegram
            }
            
            # Obtener usuarios activos de Telegram
            db = SessionLocal()
            try:
                active_users = crud_users.get_active_telegram_users_by_crypto(db, 'eth')
                if not active_users:
                    logger.info("ℹ️ No hay usuarios conectados a Telegram ETH para enviar alertas")
                    return
                
                # Enviar broadcast a todos los usuarios activos para ETH
                result = telegram_bot.broadcast_alert_crypto(alert_data, 'eth')
                
                logger.info(f"📢 ETH Alerta enviada: {result['sent']}/{result['total_targets']} usuarios")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error procesando señal ETH: {e}")
    
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
eth_scanner = EthScannerService()