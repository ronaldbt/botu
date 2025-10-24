# backend/app/services/bitcoin30m_mainnet.py
# Scanner Bitcoin 30m específico para Mainnet con lógica del backtest

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import requests
import time
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TradingApiKey, TradingOrder
from app.services.auto_trading_mainnet30m_executor import AutoTradingMainnet30mExecutor

logger = logging.getLogger(__name__)

class Bitcoin30mMainnetScanner:
    """
    Scanner Bitcoin 30m específico para Mainnet
    Utiliza la lógica probada del backtest para detectar patrones U
    """
    
    def __init__(self):
        self.is_running = False
        self.last_scan_time = None
        self.alerts_count = 0
        self.scanner_logs = []
        self.last_alert_sent = None
        self.cooldown_period = 300  # 5 minutos entre alertas
        self._last_known_btc_price: float = 0.0  # Cache de último precio conocido
        self.last_scan_price: Optional[float] = None  # Precio obtenido en el último escaneo
        self.readiness_cache: Dict[str, Any] = {
            'auto_ready': False,
            'enabled_keys': 0,
            'allocated_ok': False,
            'balance_ok': False,
            'reasons': []
        }
        # Control de ciclo y parada inmediata
        import asyncio as _asyncio
        self._stop_event: _asyncio.Event = _asyncio.Event()
        self._task: Optional[_asyncio.Task] = None
        
        # Estados del bot para separar lógica de compra y venta
        self.current_state = "SEARCHING_BUY"  # SEARCHING_BUY, MONITORING_SELL, IDLE
        self.state_changed_at = None
        self.last_position_check = None
        
        # Configuración específica para Mainnet (más conservadora)
        self.config = {
            'scan_interval': 1800,  # 30 minutos
            'profit_target': 0.04,  # 4% objetivo
            'stop_loss': 0.015,     # 1.5% stop loss
            'max_hold_periods': 80, # Máximo 40 horas (80 períodos de 30m)
            'environment': 'mainnet'
        }
        
        # Parámetros de detección optimizados del backtest
        self.detection_params = {
            'window_size': 48,      # 24 horas de datos
            'step_size': 4,         # Avance cada 2 horas
            'min_depth_pct': 0.015, # 1.5% mínimo para 30min
            'window_low': 3,        # Ventana para detectar mínimos
            'base_rupture_factor': 1.008,  # Factor base de ruptura
            'max_rupture_factor': 1.025    # Máximo 2.5%
        }
        
        self.executor = AutoTradingMainnet30mExecutor()
    
    async def _check_current_state(self) -> str:
        """
        Determina el estado actual del bot basado en posiciones abiertas
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                from app.db.database import get_db
                from app.db.models import TradingOrder, TradingApiKey
                
                db = next(get_db())
            
            # Verificar si hay posiciones abiertas
            api_keys = db.query(TradingApiKey).filter(
                TradingApiKey.btc_30m_mainnet_enabled == True,
                TradingApiKey.is_active == True
            ).all()
            
            has_open_positions = False
            for api_key in api_keys:
                # Buscar órdenes de compra ejecutadas (solo las que no están completadas)
                buy_orders = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == 'BTCUSDT',
                    TradingOrder.side == 'BUY',
                    TradingOrder.status == 'FILLED'  # Solo órdenes ejecutadas que no están completadas
                ).all()
                
                # Verificar si alguna de estas órdenes NO tiene venta asociada
                for buy_order in buy_orders:
                    # Verificar si ya tiene orden de venta posterior
                    sell_order = db.query(TradingOrder).filter(
                        TradingOrder.api_key_id == api_key.id,
                        TradingOrder.symbol == 'BTCUSDT',
                        TradingOrder.side == 'SELL',
                        TradingOrder.status == 'FILLED',
                        TradingOrder.created_at > buy_order.created_at
                    ).order_by(TradingOrder.created_at.asc()).first()
                    
                    # Si no hay venta, es una posición abierta
                    if not sell_order:
                        has_open_positions = True
                        break
                
                if has_open_positions:
                    break
            
            # Determinar estado
            if has_open_positions:
                new_state = "MONITORING_SELL"
            else:
                new_state = "SEARCHING_BUY"
            
            # Log cambio de estado
            if new_state != self.current_state:
                old_state = self.current_state
                self.current_state = new_state
                self.state_changed_at = datetime.now()
                
                state_emoji = "🔍" if new_state == "SEARCHING_BUY" else "📊"
                state_desc = "Buscando oportunidades de compra" if new_state == "SEARCHING_BUY" else "Monitoreando posiciones para venta"
                
                self.add_log(
                    f"{state_emoji} CAMBIO DE ESTADO: {state_desc}",
                    "INFO",
                    {
                        'new_state': new_state,
                        'previous_state': old_state,
                        'timestamp': self.state_changed_at.isoformat()
                    }
                )
            
                return self.current_state
                
            except Exception as e:
                logger.error(f"Error verificando estado (intento {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # Backoff exponencial: 2, 4, 8 segundos
                    wait_time = 2 ** attempt
                    logger.warning(f"🔄 Reintentando en {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Último intento falló, mantener estado anterior
                    logger.warning(f"🔄 Falló después de {max_retries} intentos. Manteniendo estado anterior: {self.current_state}")
                    return self.current_state
    
    async def _recover_state(self):
        """
        Intenta recuperar el estado correcto tras un error
        """
        try:
            self.add_log("🔄 Intentando recuperar estado...", "INFO")
            
            # Reintentar verificación de estado con timeout
            recovered_state = await asyncio.wait_for(
                self._check_current_state(), 
                timeout=10.0
            )
            
            if recovered_state != "IDLE":
                self.current_state = recovered_state
                self.add_log(f"✅ Estado recuperado: {recovered_state}", "INFO")
            else:
                self.add_log("⚠️ No se pudo recuperar estado, manteniendo IDLE", "WARNING")
                
        except asyncio.TimeoutError:
            self.add_log("⏱️ Timeout en recuperación de estado", "WARNING")
        except Exception as e:
            self.add_log(f"❌ Error en recuperación: {e}", "ERROR")
        
    async def start_scanner(self):
        """Inicia el scanner de Bitcoin 30m para Mainnet (loop cancelable)."""
        if self.is_running:
            logger.warning("Scanner Bitcoin 30m Mainnet ya está ejecutándose")
            return
        self.is_running = True
        self._stop_event.clear()
        self.add_log("🚀 Scanner Bitcoin 30m Mainnet iniciado")
        
        async def _run_loop():
            try:
                while self.is_running and not self._stop_event.is_set():
                    await self._scan_cycle()
                    # Espera cancelable
                    try:
                        await asyncio.wait_for(self._stop_event.wait(), timeout=self.config['scan_interval'])
                    except asyncio.TimeoutError:
                        pass
            except Exception as e:
                logger.error(f"Error en scanner Bitcoin 30m Mainnet: {e}")
                self.add_log(f"❌ Error en scanner: {e}")
            finally:
                self.is_running = False
                self.add_log("🛑 Scanner Bitcoin 30m Mainnet detenido")
        # Lanzar en background
        self._task = asyncio.create_task(_run_loop())
    
    async def stop_scanner(self):
        """Detiene el scanner de forma inmediata."""
        if not self.is_running and (self._task is None or self._task.done()):
            self.add_log("🛑 Scanner Bitcoin 30m Mainnet ya estaba detenido")
            return
        self.add_log("🛑 Deteniendo scanner Bitcoin 30m Mainnet...")
        self.is_running = False
        self._stop_event.set()
        try:
            if self._task:
                await asyncio.wait_for(self._task, timeout=5)
        except Exception:
            # En caso de no finalizar a tiempo, cancelar
            try:
                if self._task:
                    self._task.cancel()
            except Exception:
                pass
        finally:
            self._task = None
    
    async def _scan_cycle(self):
        """Ciclo principal de escaneo con lógica de estados"""
        try:
            self.last_scan_time = datetime.now()
            
            # Evaluar readiness antes de escanear
            self._evaluate_readiness()
            if not self.readiness_cache.get('auto_ready'):
                reasons = ", ".join(self.readiness_cache.get('reasons', []))
                self.add_log(
                    f"⚠️ Auto-trading NO LISTO: {reasons}. No se ejecutarán compras.",
                    "WARNING",
                    current_price=self.last_scan_price or 0.0
                )

            # Obtener datos históricos de 30 minutos
            df = await self._get_historical_data_30min()
            if df is None or df.empty:
                self.add_log("⚠️ No se pudieron obtener datos históricos")
                return
            
            # Precio de Binance tomado de la última vela escaneada
            current_price = float(df.iloc[-1]['close'])
            self.last_scan_price = current_price
            
            # Determinar estado actual del bot
            current_state = await self._check_current_state()
            
            # Log de inicio de escaneo con estado y precio
            state_emoji = "🔍" if current_state == "SEARCHING_BUY" else "📊"
            self.add_log(
                f"{state_emoji} Escaneo 30m - Estado: {current_state} | Velas: {len(df)} | Precio BTC: ${current_price:,.2f}",
                "INFO",
                {"candles": len(df), "state": current_state},
                current_price=current_price
            )
            
            # Ejecutar lógica según el estado
            if current_state == "SEARCHING_BUY":
                await self._handle_searching_buy_state(df, current_price)
            elif current_state == "MONITORING_SELL":
                await self._handle_monitoring_sell_state(current_price)
            elif current_state == "IDLE":
                # Intentar recuperar el estado correcto
                await self._recover_state()
            else:
                self.add_log("⚠️ Estado desconocido, saltando ciclo", "WARNING")
                
        except Exception as e:
            logger.error(f"Error en ciclo de escaneo Mainnet: {e}")
            self.add_log(f"❌ Error en escaneo: {e}")
    
    async def _handle_searching_buy_state(self, df: pd.DataFrame, current_price: float):
        """
        Maneja el estado de búsqueda de compras
        Solo se enfoca en detectar patrones U y ejecutar compras
        """
        try:
            # Detectar patrones U usando lógica del backtest
            signals = self._detect_u_patterns_30min(df)
            
            if signals:
                self.add_log(f"🎯 Detectados {len(signals)} patrones U potenciales")
                
                for signal in signals:
                    await self._process_signal(signal)
            else:
                self.add_log(
                    f"🔍 Búsqueda de compra - No se detectaron patrones U | Precio BTC: ${current_price:,.2f}",
                    "INFO",
                    current_price=current_price
                )
                
        except Exception as e:
            logger.error(f"Error en estado de búsqueda de compra: {e}")
            self.add_log(f"❌ Error buscando compras: {e}")
    
    async def _handle_monitoring_sell_state(self, current_price: float):
        """
        Maneja el estado de monitoreo de ventas
        Solo se enfoca en verificar condiciones de venta (TP, SL, Max Hold)
        """
        try:
            self.add_log(
                f"📊 Monitoreo de ventas - Verificando condiciones de salida | Precio BTC: ${current_price:,.2f}",
                "INFO",
                current_price=current_price
            )
            
            # Solo verificar condiciones de venta
            await self.executor.check_and_execute_sell_orders()
            
        except Exception as e:
            logger.error(f"Error en estado de monitoreo de ventas: {e}")
            self.add_log(f"❌ Error monitoreando ventas: {e}")
    
    async def _get_historical_data_30min(self) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos de 30 minutos para análisis"""
        try:
            # Obtener más historia para análisis en vivo (p. ej., ~6 días = 300 velas)
            # Binance permite hasta 1000; usamos 300 para un buen equilibrio
            limit = 300
            
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': 'BTCUSDT',
                'interval': '30m',
                'limit': limit
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
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos Mainnet: {e}")
            return None
    
    def _detect_u_patterns_30min(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta patrones U usando la lógica optimizada del backtest
        """
        signals = []
        
        # Detectar mínimos significativos
        significant_lows = self._detect_lows_30min(
            df, 
            window=self.detection_params['window_low'], 
            min_depth_pct=self.detection_params['min_depth_pct']
        )
        # Log de diagnóstico: conteo de mínimos detectados
        try:
            self.add_log(
                f"🔎 Diagnóstico: mínimos significativos detectados: {len(significant_lows)}",
                "INFO",
                {
                    "window_low": self.detection_params['window_low'],
                    "min_depth_pct": self.detection_params['min_depth_pct']
                },
                current_price=float(df.iloc[-1]['close'])
            )
        except Exception:
            pass
        
        if not significant_lows:
            return signals
        
        # Analizar los últimos 2 mínimos (más frecuente)
        for low in significant_lows[-2:]:
            min_idx = low['index']
            
            # ATR y factor dinámico
            atr = self._calculate_atr_simple(df)
            current_price = df.iloc[-1]['close']
            
            # Factor más conservador para 30min
            dynamic_factor = self._calculate_rupture_factor_30min(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones optimizadas para 30min
            if len(df) - min_idx > 2 and len(df) - min_idx < 24:  # Entre 1h y 12h
                recent_slope = self._calculate_slope(df.iloc[-3:]['close'].values)
                pre_slope = self._calculate_slope(df.iloc[max(0, min_idx-3):min_idx]['close'].values)
                
                # Condiciones ajustadas para timeframe corto
                conditions = [
                    pre_slope < -0.08,  # Pendiente bajista
                    current_price > nivel_ruptura * 0.98,  # Cerca del nivel de ruptura
                    recent_slope > -0.02,  # Momentum positivo
                    low['depth'] >= 0.015,  # Al menos 1.5% de profundidad
                    self._check_momentum_filter_30min(df, min_idx)
                ]
                condition_names = [
                    "pre_slope < -0.08",
                    "current_price > nivel_ruptura * 0.98",
                    "recent_slope > -0.02",
                    "depth >= 0.015",
                    "momentum_filter"
                ]
                
                # Log de diagnóstico por mínimo evaluado
                try:
                    failed = [name for ok, name in zip(conditions, condition_names) if not ok]
                    self.add_log(
                        f"🧪 Evaluación de mínimo idx={min_idx}",
                        "INFO",
                        {
                            "min_timestamp": str(df.index[min_idx]),
                            "pre_slope": float(pre_slope),
                            "recent_slope": float(recent_slope),
                            "low_depth": float(low['depth']),
                            "atr": float(atr),
                            "dynamic_factor": float(dynamic_factor),
                            "nivel_ruptura": float(nivel_ruptura),
                            "current_price": float(current_price),
                            "pattern_width": int(len(df) - min_idx),
                            "conditions_passed": all(conditions),
                            "failed_conditions": failed
                        },
                        current_price=float(current_price)
                    )
                except Exception:
                    pass

                if all(conditions):
                    signal = {
                        'timestamp': df.index[-1],
                        'entry_price': nivel_ruptura,
                        'signal_strength': abs(pre_slope),
                        'min_price': low['low'],
                        'pattern_width': len(df) - min_idx,
                        'atr': atr,
                        'dynamic_factor': dynamic_factor,
                        'depth': low['depth'],
                        'current_price': current_price,
                        'environment': 'mainnet'
                    }
                    # Log de aceptación de señal
                    try:
                        self.add_log(
                            f"✅ Señal U aceptada - entry: ${signal['entry_price']:.2f} (precio ${current_price:.2f})",
                            "ALERT",
                            {
                                "signal_strength": float(signal['signal_strength']),
                                "depth_pct": float(signal['depth'] * 100),
                                "pattern_width": int(signal['pattern_width'])
                            },
                            current_price=float(current_price)
                        )
                    except Exception:
                        pass
                    signals.append(signal)
                    break  # Solo una señal por ventana
        
        return signals
    
    def _detect_lows_30min(self, df: pd.DataFrame, window: int = 3, min_depth_pct: float = 0.015) -> List[Dict]:
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
    
    def _calculate_rupture_factor_30min(self, atr: float, price: float) -> float:
        """Factor de ruptura optimizado para 30min (más conservador)"""
        atr_pct = atr / price
        
        # Más conservador para timeframe corto
        if atr_pct < 0.01:
            factor = self.detection_params['base_rupture_factor']
        elif atr_pct < 0.02:
            factor = self.detection_params['base_rupture_factor'] + (atr_pct * 0.2)
        else:
            factor = min(
                self.detection_params['base_rupture_factor'] + (atr_pct * 0.3), 
                self.detection_params['max_rupture_factor']
            )
        
        return max(factor, self.detection_params['base_rupture_factor'])
    
    def _check_momentum_filter_30min(self, df: pd.DataFrame, min_idx: int) -> bool:
        """Filtro de momentum para timeframe de 30min"""
        if min_idx < 10:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia de los últimos 10 períodos (5 horas)
        recent_10 = df.iloc[-10:]['close'].values
        trend_slope = self._calculate_slope(recent_10)
        
        # Permitir trades si la tendencia no es muy bajista
        return trend_slope > -0.05
    
    def _calculate_atr_simple(self, df: pd.DataFrame, period: int = 7) -> float:
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
    
    def _calculate_slope(self, values: np.ndarray) -> float:
        """Calcula pendiente"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    async def _process_signal(self, signal: Dict):
        """Procesa una señal de compra detectada"""
        try:
            # Guardas tempranas por señal nula
            if signal is None:
                self.add_log("🛑 Señal nula recibida - no se procesa (probable posición abierta)", "WARNING")
                return
            # Verificar cooldown
            if self.last_alert_sent:
                time_since_last = (datetime.now() - self.last_alert_sent).total_seconds()
                if time_since_last < self.cooldown_period:
                    remaining = self.cooldown_period - time_since_last
                    self.add_log(f"⏳ Cooldown activo - {remaining:.0f}s restantes", "WARNING")
                    return
            
            self.alerts_count += 1
            self.last_alert_sent = datetime.now()
            
            # Log detallado de la señal
            self.add_log(
                f"🚨 ALERTA: Patrón U detectado - Precio actual: ${signal['current_price']:.2f} | Precio entrada sugerido: ${signal['entry_price']:.2f}",
                "ALERT",
                {
                    'signal_type': 'U_PATTERN',
                    'current_price': signal['current_price'],
                    'entry_price': signal['entry_price'],
                    'depth_percentage': signal['depth'] * 100,
                    'signal_strength': signal['signal_strength']
                }
            )
            
            self.add_log(
                f"📊 Análisis técnico: Profundidad {signal['depth']*100:.2f}% | Fuerza de señal: {signal['signal_strength']:.3f} | Potencial ganancia: +{self.config['profit_target']*100:.1f}%",
                "INFO"
            )
            
            # Ejecutar trading automático
            trade_result = await self.executor.execute_buy_order(signal)
            
            # Log del resultado del trade
            if trade_result and trade_result.get('success'):
                self.add_log(
                    f"💰 COMPRA EJECUTADA: {trade_result.get('quantity', 0):.6f} BTC a ${trade_result.get('price', 0):.2f} | Total: ${trade_result.get('total_usdt', 0):.2f}",
                    "TRADE",
                    {
                        'trade_type': 'BUY',
                        'quantity': trade_result.get('quantity', 0),
                        'price': trade_result.get('price', 0),
                        'total_usdt': trade_result.get('total_usdt', 0),
                        'binance_order_id': trade_result.get('binance_order_id')
                    }
                )
            else:
                # Si el ejecutor devolvió None o un dict sin success, puede ser por posición abierta
                msg = None
                if trade_result is None:
                    msg = "Compra omitida por ejecutor (sin respuesta)"
                elif isinstance(trade_result, dict) and not trade_result.get('success') and 'position_open' in trade_result.get('msg','').lower():
                    msg = "Compra omitida: ya existe una posición abierta"
                else:
                    # Mensaje genérico de error
                    err = trade_result.get('error') if isinstance(trade_result, dict) else 'Error desconocido'
                    msg = f"❌ Error ejecutando compra automática: {err}"
                self.add_log(msg, "WARNING")
            
            # NO verificar ventas inmediatamente después de una compra
            # Las ventas se verifican en el siguiente ciclo de escaneo para evitar ventas instantáneas
            # El cooldown de 5 minutos en el ejecutor previene ventas inmediatas
            
        except Exception as e:
            logger.error(f"Error procesando señal Mainnet: {e}")
            self.add_log(f"❌ Error procesando señal: {e}", "ERROR")
    
    def add_log(self, message: str, level: str = "INFO", details: Dict = None, current_price: Optional[float] = None):
        """Agrega un log detallado al scanner"""
        timestamp = datetime.now().isoformat()
        # No se consulta precio aquí; se pasa cuando corresponde (p. ej. durante escaneo)
        
        # Determinar el nivel del log basado en el mensaje
        if not level or level == "INFO":
            if "❌" in message or "Error" in message:
                level = "ERROR"
            elif "⚠️" in message or "Warning" in message:
                level = "WARNING"
            elif "🎯" in message or "💰" in message or "COMPRA" in message or "VENTA" in message:
                level = "TRADE"
            elif "🚨" in message or "ALERTA" in message:
                level = "ALERT"
            elif "✅" in message or "SUCCESS" in message:
                level = "SUCCESS"
            else:
                level = "INFO"
        
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level,
            'environment': 'mainnet',
            'btc_price': current_price if current_price is not None else None,
            'details': details or {}
        }
        
        # Agregar información adicional según el tipo de log
        if level == "TRADE" and details:
            log_entry['details'].update({
                'trade_type': details.get('trade_type', 'unknown'),
                'quantity': details.get('quantity', 0),
                'price': details.get('price', 0),
                'pnl': details.get('pnl', 0),
                'pnl_percentage': details.get('pnl_percentage', 0)
            })
        
        self.scanner_logs.append(log_entry)
        
        # Mantener solo los últimos 1000 logs
        if len(self.scanner_logs) > 1000:
            self.scanner_logs = self.scanner_logs[-1000:]
        
        logger.info(f"[Bitcoin30m-Mainnet-{level}] {message}")
    
    def _get_current_btc_price(self) -> float:
        """Obtiene el precio actual de BTC"""
        try:
            import requests
            response = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=5)
            response.raise_for_status()
            data = response.json()
            price = float(data['price'])
            self._last_known_btc_price = price
            return price
        except Exception as e:
            logger.warning(f"No se pudo obtener precio BTC (Binance): {e}")
            return self._last_known_btc_price if self._last_known_btc_price > 0 else 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del scanner 30m Mainnet"""
        is_actually_running = self.is_running
        
        # Verificar si está corriendo por logs recientes
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
                if minutes_since_last_log < 35:
                    is_actually_running = True
                    logger.info(f"🔄 Scanner 30m Mainnet detectado como activo por logs recientes (último: {minutes_since_last_log:.1f} min)")
        
        # Usar timestamp del último log si no hay last_scan_time
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
            "logs": self.scanner_logs[-100:],  # Últimos 100 logs
            "cooldown_remaining": None if not self.last_alert_sent else max(0, self.cooldown_period - (datetime.now() - self.last_alert_sent).total_seconds()),
            "timeframe": "30m",
            "environment": "mainnet",
            # Último precio conocido del último escaneo
            "btc_price": self.last_scan_price,
            "auto_trading_readiness": self.readiness_cache,
            # Estados del bot
            "current_state": self.current_state,
            "state_changed_at": self.state_changed_at.isoformat() if self.state_changed_at else None
        }

    def _evaluate_readiness(self):
        """Evalúa si hay condiciones para operar automáticamente y almacena razones."""
        try:
            from app.db.database import get_db
            from app.db.models import TradingApiKey
            db = next(get_db())
            keys = db.query(TradingApiKey).filter(
                TradingApiKey.is_testnet == False,
                TradingApiKey.is_active == True
            ).all()
            enabled = [k for k in keys if getattr(k, 'btc_30m_mainnet_enabled', False)]
            allocated_ok = any((k.btc_30m_mainnet_allocated_usdt or 0) > 0 for k in enabled)
            # Para balance_ok, asumimos true (el ejecutor valida saldo real). Aquí solo señalamos asignación
            reasons = []
            if len(enabled) == 0:
                reasons.append('sin claves mainnet habilitadas')
            if not allocated_ok:
                reasons.append('asignación USDT=0')
            auto_ready = len(enabled) > 0 and allocated_ok
            self.readiness_cache = {
                'auto_ready': auto_ready,
                'enabled_keys': len(enabled),
                'allocated_ok': allocated_ok,
                'balance_ok': allocated_ok,  # proxy
                'reasons': reasons
            }
        except Exception:
            self.readiness_cache = {
                'auto_ready': False,
                'enabled_keys': 0,
                'allocated_ok': False,
                'balance_ok': False,
                'reasons': ['error evaluando readiness']
            }

# Instancia global del scanner Mainnet
bitcoin_30m_mainnet_scanner = Bitcoin30mMainnetScanner()
