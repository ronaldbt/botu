# src/bitcoin_1h_backtest.py
# Backtesting de Bitcoin para todo el año 2024 usando intervalos de 1 hora
# Basado en el sistema de 15 minutos con ajustes para menor frecuencia y mayor estabilidad

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from utils import log

class Bitcoin1hBacktest:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.equity_curve = [initial_capital]
        
    def get_historical_data_12months(self):
        """
        Obtiene datos históricos de Bitcoin para todo el año 2024 usando intervalos de 1 hora
        """
        print("📊 Obteniendo datos históricos de Bitcoin para todo el año 2024 (1h)...")
        
        # Fechas para todo 2024
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2025, 1, 1)
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        all_klines = []
        current_start = start_timestamp
        
        # Binance límite: 1000 velas por request
        # Para 1h en 365 días: ~8760 velas, necesitamos múltiples requests
        interval = "1h"
        limit = 1000
        
        while current_start < end_timestamp:
            try:
                url = "https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': 'BTCUSDT',
                    'interval': interval,
                    'startTime': current_start,
                    'endTime': end_timestamp,
                    'limit': limit
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                klines = response.json()
                if not klines:
                    break
                    
                all_klines.extend(klines)
                
                # Actualizar start_time para siguiente request
                last_timestamp = klines[-1][0]
                current_start = last_timestamp + 1
                
                print(f"✅ Obtenidas {len(klines)} velas hasta {datetime.fromtimestamp(last_timestamp/1000).strftime('%Y-%m-%d')}")
                
                # Rate limit: esperar un poco entre requests
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error obteniendo datos: {e}")
                break
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        # Convertir tipos
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"🎯 DATOS BITCOIN 2024 COMPLETO (1h):")
        print(f"   📅 Período: {df.index[0]} a {df.index[-1]}")
        print(f"   📊 Total velas: {len(df)}")
        print(f"   💰 Precio inicial: ${df['open'].iloc[0]:,.2f}")
        print(f"   💰 Precio final: ${df['close'].iloc[-1]:,.2f}")
        print(f"   📈 Cambio período: {((df['close'].iloc[-1] / df['open'].iloc[0]) - 1) * 100:.2f}%")
        print(f"   🔝 Máximo: ${df['high'].max():,.2f}")
        print(f"   📉 Mínimo: ${df['low'].min():,.2f}")
        print()
        
        return df
    
    def backtest_12months_1h_optimized(self):
        """
        Backtesting OPTIMIZADO de todo el año 2024 con intervalos de 1 hora
        Parámetros ajustados para mayor estabilidad en timeframe largo
        """
        print("🚀 BACKTESTING BITCOIN - AÑO COMPLETO 2024 (1h)")
        print("="*80)
        print("⚡ Estrategia de baja frecuencia con intervalos de 1 hora")
        print("🎯 Objetivo: Maximizar estabilidad y capturar movimientos grandes")
        print("🏆 2024 fue un año excepcional: Bitcoin subió de ~$42K a ~$96K (+129%)")
        print("="*80)
        
        df = self.get_historical_data_12months()
        if df.empty:
            print("❌ No se pudieron obtener datos históricos")
            return
            
        # CONFIGURACIÓN IGUAL A 30MIN EXITOSO
        profit_target = 0.040     # 4.0% objetivo (igual que 30min exitoso)
        stop_loss = 0.015         # 1.5% stop loss (igual que 30min exitoso)
        max_hold_periods = 48     # Máximo 48 horas (24h en 30min = 48h en 1h)
        
        # Ventanas de análisis adaptadas para 1h (misma proporción que 30min)
        window_size = 48          # 48 horas de datos (equivalente a 24h en 30min)
        step_size = 2             # Avance cada 2 horas (equivalente a 1h en 30min)
        
        total_windows = (len(df) - window_size) // step_size
        print(f"🔄 Analizando {total_windows} ventanas de trading...")
        print("⚡ Configuración 1h (estrategia 30min): 4.0% profit target | 1.5% stop loss | Max 48h holding")
        print()
        
        # Trackear performance mensual
        monthly_performance = {}
        monthly_trades = {}
        
        for window_idx in range(total_windows):
            start_idx = window_idx * step_size
            end_idx = start_idx + window_size
            
            if end_idx >= len(df) - 50:  # Dejar datos para simular trades
                break
            
            # Datos para análisis
            analysis_df = df.iloc[start_idx:end_idx].copy()
            
            # Detectar señales usando algoritmo adaptado para 1h
            signals = self._detect_u_patterns_1h(analysis_df)
            
            for signal in signals:
                # Simular trade en datos futuros
                trade_result = self._simulate_trade_1h(
                    df, signal, end_idx, profit_target, stop_loss, max_hold_periods
                )
                
                if trade_result:
                    self.trades.append(trade_result)
                    old_capital = self.current_capital
                    self.current_capital *= (1 + trade_result['return_pct'])
                    self.equity_curve.append(self.current_capital)
                    
                    # Trackear por mes
                    month_key = f"{trade_result['entry_time'].year}-{trade_result['entry_time'].month:02d}"
                    if month_key not in monthly_performance:
                        monthly_performance[month_key] = []
                        monthly_trades[month_key] = 0
                    
                    monthly_performance[month_key].append(trade_result['return_pct'] * 100)
                    monthly_trades[month_key] += 1
                    
                    if len(self.trades) <= 50:  # Mostrar primeros 50 trades
                        print(f"🚀 Trade #{len(self.trades)} - {trade_result['entry_time'].strftime('%Y-%m-%d %H:%M')}")
                        print(f"   💰 ${old_capital:,.0f} → ${self.current_capital:,.0f} ({trade_result['return_pct']*100:+.2f}%)")
        
        self._generate_12months_report(monthly_performance, monthly_trades, df)
        
    def _detect_u_patterns_1h(self, df):
        """
        Detecta patrones U adaptado para intervalos de 1 hora
        Basado en el algoritmo de 15min pero con parámetros para mayor estabilidad
        """
        signals = []
        
        # Detectar mínimos significativos con parámetros de 30min exitoso
        significant_lows = self._detect_lows_1h(df, window=3, min_depth_pct=0.015)  # 1.5% mínimo (igual que 30min)
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos (igual que 30min exitoso)
        for low in significant_lows[-2:]:  # Últimos 2 mínimos (igual que 30min)
            min_idx = low['index']
            
            # ATR y factor dinámico
            atr = self._calculate_atr_simple(df)
            current_price = df.iloc[-1]['close']
            
            # Factor adaptado para 1h (más conservador)
            dynamic_factor = self._calculate_rupture_factor_1h(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones adaptadas para 1h (equivalente a 30min)
            if len(df) - min_idx > 1 and len(df) - min_idx < 24:  # Entre 1h y 24h (proporcional a 30min)
                recent_slope = self._calculate_slope(df.iloc[-3:]['close'].values)
                pre_slope = self._calculate_slope(df.iloc[max(0, min_idx-3):min_idx]['close'].values)
                
                # Condiciones IGUALES a 30min exitoso
                conditions = [
                    pre_slope < -0.08,  # Pendiente bajista (igual que 30min)
                    current_price > nivel_ruptura * 0.98,  # Cerca del nivel de ruptura (igual que 30min)
                    recent_slope > -0.01,  # Momentum (igual que 30min)
                    low['depth'] >= 0.015,  # 1.5% de profundidad (igual que 30min)
                    self._check_momentum_filter_1h(df, min_idx)
                ]
                
                if all(conditions):
                    signals.append({
                        'timestamp': df.index[-1],
                        'entry_price': nivel_ruptura,
                        'signal_strength': abs(pre_slope),
                        'min_price': low['low'],
                        'pattern_width': len(df) - min_idx,
                        'atr': atr,
                        'dynamic_factor': dynamic_factor,
                        'depth': low['depth']
                    })
                    break  # Solo una señal por ventana
                    
        return signals
    
    def _detect_lows_1h(self, df, window=3, min_depth_pct=0.015):
        """Detecta mínimos OPTIMIZADOS para intervalos de 1h"""
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            
            window_slice = df.iloc[i-window:i+window+1]
            if current_low == window_slice['low'].min():
                local_high = window_slice['high'].max()
                depth = (local_high - current_low) / local_high
                
                if depth >= min_depth_pct and i < len(df) - 2:
                    # Verificar volumen para confirmar el mínimo (igual que 30min)
                    volume_avg = df.iloc[i-window:i+window+1]['volume'].mean()
                    current_volume = df.iloc[i]['volume']
                    
                    if current_volume > volume_avg * 0.70 or depth >= 0.020:  # Igual que 30min
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
    
    def _calculate_rupture_factor_1h(self, atr, price, base_factor=1.008):
        """Factor de ruptura igual que 30min exitoso"""
        atr_pct = atr / price
        
        # Igual que 30min exitoso
        if atr_pct < 0.010:
            factor = base_factor
        elif atr_pct < 0.015:
            factor = base_factor + (atr_pct * 0.10)
        else:
            factor = min(base_factor + (atr_pct * 0.20), 1.020)  # Máximo 2% igual que 30min
        
        return max(factor, 1.008)  # Mínimo igual que 30min
    
    def _check_momentum_filter_1h(self, df, min_idx):
        """Filtro de momentum para timeframe de 1h"""
        if min_idx < 4:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia igual que 30min exitoso (adaptado a 1h)
        recent_4 = df.iloc[-4:]['close'].values
        trend_slope = self._calculate_slope(recent_4)
        
        # Permitir trades igual que 30min exitoso
        return trend_slope > -0.03
    
    def _calculate_atr_simple(self, df, period=6):
        """Calcula ATR simplificado para 1h"""
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
    
    def _calculate_slope(self, values):
        """Calcula pendiente"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    def _simulate_trade_1h(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """Simula trade para timeframe de 1h"""
        entry_price = signal['entry_price']
        entry_time = signal['timestamp']
        
        future_data = df.iloc[start_idx:start_idx + max_hold + 20]
        if len(future_data) < 3:
            return None
            
        target_price = entry_price * (1 + profit_target)
        stop_price = entry_price * (1 - stop_loss)
        
        max_profit = 0
        max_drawdown = 0
        
        for i, (timestamp, row) in enumerate(future_data.iterrows()):
            if i > max_hold:
                exit_price = row['close']
                exit_reason = "MAX_HOLD"
                exit_time = timestamp
                break
                
            high = row['high']
            low = row['low']
            close = row['close']
            
            current_profit = (high - entry_price) / entry_price
            current_loss = (entry_price - low) / entry_price
            max_profit = max(max_profit, current_profit)
            max_drawdown = max(max_drawdown, current_loss)
            
            if high >= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
                exit_time = timestamp
                break
                
            if low <= stop_price:
                exit_price = stop_price
                exit_reason = "STOP_LOSS"
                exit_time = timestamp
                break
                
        else:
            exit_price = future_data.iloc[-1]['close']
            exit_reason = "END_OF_DATA"
            exit_time = future_data.index[-1]
        
        return_pct = (exit_price - entry_price) / entry_price
        hold_hours = int((exit_time - entry_time).total_seconds() / 3600)
        
        return {
            'trade_number': len(self.trades) + 1,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': return_pct,
            'hold_hours': hold_hours,
            'exit_reason': exit_reason,
            'max_profit': max_profit,
            'max_drawdown': max_drawdown,
            'signal_strength': signal['signal_strength'],
            'depth': signal['depth']
        }
    
    def _generate_12months_report(self, monthly_performance, monthly_trades, df):
        """
        Genera reporte completo del año 2024 con timeframe de 1 hora
        """
        print()
        print("📊 REPORTE COMPLETO - BITCOIN AÑO 2024 (1h TIMEFRAME)")
        print("="*80)
        
        if not self.trades:
            print("⚠️ No se generaron trades durante el año 2024")
            return
            
        # Estadísticas generales
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['return_pct'] > 0]
        losing_trades = [t for t in self.trades if t['return_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        total_return = (self.current_capital / self.initial_capital - 1) * 100
        
        # Comparar con Buy & Hold
        btc_start_price = df['open'].iloc[0]
        btc_end_price = df['close'].iloc[-1]
        buy_hold_return = (btc_end_price / btc_start_price - 1) * 100
        
        print(f"🏆 RESUMEN EJECUTIVO BITCOIN 2024 (1h):")
        print(f"   💵 Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   💰 Capital final: ${self.current_capital:,.2f}")
        print(f"   📈 Sistema U (1h): {total_return:+.2f}%")
        print(f"   📈 Buy & Hold BTC (2024): {buy_hold_return:+.2f}%")
        print(f"   🎯 Diferencia vs Buy & Hold: {total_return - buy_hold_return:+.2f} puntos")
        print()
        
        print(f"📊 ESTADÍSTICAS DE TRADING (1h BAJA-FRECUENCIA):")
        print(f"   🔢 Total trades: {total_trades}")
        print(f"   ✅ Ganadores: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"   ❌ Perdedores: {len(losing_trades)} ({100-win_rate:.1f}%)")
        print(f"   📈 Retorno promedio: {np.mean([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   🚀 Mejor trade: {max([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   💥 Peor trade: {min([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   ⏱️ Holding promedio: {np.mean([t['hold_hours'] for t in self.trades]):.0f} horas")
        print()
        
        # Performance mensual
        print("📅 PERFORMANCE MENSUAL (1h):")
        print("-" * 60)
        months_map = {
            '2024-01': 'Enero', '2024-02': 'Febrero', '2024-03': 'Marzo',
            '2024-04': 'Abril', '2024-05': 'Mayo', '2024-06': 'Junio',
            '2024-07': 'Julio', '2024-08': 'Agosto', '2024-09': 'Septiembre',
            '2024-10': 'Octubre', '2024-11': 'Noviembre', '2024-12': 'Diciembre'
        }
        
        for month in sorted(monthly_performance.keys()):
            if month in monthly_performance:
                monthly_returns = monthly_performance[month]
                avg_return = np.mean(monthly_returns)
                trade_count = monthly_trades[month]
                total_monthly = sum(monthly_returns)
                
                status = "🟢" if total_monthly > 0 else "🔴" if total_monthly < 0 else "🟡"
                month_name = months_map.get(month, month)
                
                print(f"   {status} {month_name}: {trade_count} trades | Avg: {avg_return:+.2f}% | Total: {total_monthly:+.2f}%")
        print()
        
        # Análisis de frecuencia
        total_days = (df.index[-1] - df.index[0]).days
        trades_per_day = total_trades / total_days
        trades_per_week = total_trades / (total_days / 7)
        trades_per_month = total_trades / 12
        
        print(f"⚡ ANÁLISIS DE FRECUENCIA (1h STRATEGY):")
        print(f"   📊 Trades por día: {trades_per_day:.2f}")
        print(f"   📊 Trades por semana: {trades_per_week:.1f}")
        print(f"   📊 Trades por mes: {trades_per_month:.1f}")
        print(f"   📊 Días con trading: {total_days}")
        print()
        
        # Trades detallados (todos si son pocos)
        print("💰 TRADES DETALLADOS (1h):")
        print("-" * 90)
        
        for i, trade in enumerate(self.trades):
            status = "✅" if trade['return_pct'] > 0 else "❌"
            print(f"{status} #{trade['trade_number']} | {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} | ")
            print(f"   ${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} | ")
            print(f"   {trade['return_pct']*100:+.2f}% | {trade['hold_hours']}h | {trade['exit_reason']}")
        print()
        
        # Evaluación final
        print("🎯 EVALUACIÓN FINAL (1h STRATEGY):")
        if total_return > buy_hold_return * 1.5:
            print("🟢 EXCEPCIONAL: Estrategia 1h superó significativamente a Buy & Hold!")
        elif total_return > buy_hold_return:
            print("🟢 EXCELENTE: Estrategia 1h superó a Buy & Hold")
        elif total_return > 15:
            print("🟡 BUENO: Estrategia 1h tuvo performance sólida")
        elif total_return > 0:
            print("🟡 ACEPTABLE: Estrategia 1h fue rentable")
        else:
            print("🔴 MEJORABLE: Estrategia 1h perdió dinero (revisar parámetros)")
        
        # Comparación con otros timeframes
        print(f"📈 Factor de rendimiento vs Buy & Hold: {total_return / buy_hold_return if buy_hold_return != 0 else 'N/A':.2f}x")
        print(f"📊 Eficiencia de trading: {trades_per_day:.2f} trades/día vs 30min≈1.5 trades/día")
        print()

def main():
    """Función principal"""
    print("🚀 Iniciando backtest Bitcoin 1h para todo el año 2024...")
    backtest = Bitcoin1hBacktest(initial_capital=1000)
    backtest.backtest_12months_1h_optimized()

if __name__ == "__main__":
    main()