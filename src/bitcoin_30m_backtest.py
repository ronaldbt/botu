# src/bitcoin_1h_backtest.py
# Backtesting de Bitcoin para todo el año 2024 usando intervalos de 30 minutos

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
        
    def get_historical_data_2024(self):
        """
        Obtiene datos históricos de Bitcoin para todo el año 2024 usando intervalos de 30 minutos
        """
        print("📊 Obteniendo datos históricos de Bitcoin para todo el año 2024 (30min)...")
        
        # Fechas para todo 2024
        start_time = int(datetime(2024, 1, 1).timestamp() * 1000)
        end_time = int(datetime(2024, 12, 31, 23, 59, 59).timestamp() * 1000)
        
        all_klines = []
        current_start = start_time
        
        # Binance límite: 1000 velas por request
        # Para 30min en 1 año: ~17520 velas, necesitamos múltiples requests
        interval = "30m"
        limit = 1000
        
        while current_start < end_time:
            try:
                url = "https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': 'BTCUSDT',
                    'interval': interval,
                    'startTime': current_start,
                    'endTime': end_time,
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
        
        print(f"🎯 DATOS BITCOIN 2024 COMPLETO (30min):")
        print(f"   📅 Período: {df.index[0]} a {df.index[-1]}")
        print(f"   📊 Total velas: {len(df)}")
        print(f"   💰 Precio inicial: ${df['open'].iloc[0]:,.2f}")
        print(f"   💰 Precio final: ${df['close'].iloc[-1]:,.2f}")
        print(f"   📈 Cambio período: {((df['close'].iloc[-1] / df['open'].iloc[0]) - 1) * 100:.2f}%")
        print(f"   🔝 Máximo: ${df['high'].max():,.2f}")
        print(f"   📉 Mínimo: ${df['low'].min():,.2f}")
        print()
        
        return df
    
    def backtest_2024_complete(self):
        """
        Backtesting completo de todo el año 2024 con intervalos de 30 minutos
        """
        print("🚀 BACKTESTING BITCOIN - AÑO COMPLETO 2024 (30min)")
        print("="*80)
        print("⚡ Estrategia de alta frecuencia con intervalos de 30 minutos")
        print("🎯 Objetivo: Capturar micro-movimientos durante todo 2024")
        print("🏆 2024 fue un año excepcional: Bitcoin subió de ~$42K a ~$96K (+129%)")
        print("="*80)
        
        df = self.get_historical_data_2024()
        if df.empty:
            print("❌ No se pudieron obtener datos históricos")
            return
            
        # Configuración del sistema optimizada para 30min
        profit_target = 0.04      # 4% objetivo (más conservador para timeframe corto)
        stop_loss = 0.015         # 1.5% stop loss (más ajustado para 30min)
        max_hold_periods = 48     # Máximo 48 períodos (24h)
        
        # Ventanas de análisis optimizadas para 30min
        window_size = 48          # 24 horas de datos
        step_size = 4             # Avance cada 2 horas
        
        total_windows = (len(df) - window_size) // step_size
        print(f"🔄 Analizando {total_windows} ventanas de trading...")
        print("⚡ Configuración 30min optimizada: 4% profit target | 1.5% stop loss | Max 24h holding")
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
            
            # Detectar señales usando algoritmo optimizado para 30min
            signals = self._detect_u_patterns_30min(analysis_df)
            
            for signal in signals:
                # Simular trade en datos futuros
                trade_result = self._simulate_trade_30min(
                    df, signal, end_idx, profit_target, stop_loss, max_hold_periods
                )
                
                if trade_result:
                    self.trades.append(trade_result)
                    old_capital = self.current_capital
                    self.current_capital *= (1 + trade_result['return_pct'])
                    self.equity_curve.append(self.current_capital)
                    
                    # Trackear por mes
                    month_key = trade_result['entry_time'].strftime('%Y-%m')
                    if month_key not in monthly_performance:
                        monthly_performance[month_key] = []
                        monthly_trades[month_key] = 0
                    
                    monthly_performance[month_key].append(trade_result['return_pct'] * 100)
                    monthly_trades[month_key] += 1
                    
                    print(f"🚀 Trade #{len(self.trades)} - {trade_result['entry_time'].strftime('%Y-%m-%d %H:%M')}")
                    print(f"   💰 ${old_capital:,.0f} → ${self.current_capital:,.0f} ({trade_result['return_pct']*100:+.2f}%)")
        
        self._generate_2024_report(monthly_performance, monthly_trades, df)
        
    def _detect_u_patterns_30min(self, df):
        """
        Detecta patrones U optimizado para intervalos de 30 minutos
        """
        signals = []
        
        # Detectar mínimos significativos con parámetros ajustados para 30min
        significant_lows = self._detect_lows_30min(df, window=3, min_depth_pct=0.015)  # 1.5% mínimo para 30min
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos
        for low in significant_lows[-2:]:  # Últimos 2 mínimos (más frecuente)
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
    
    def _detect_lows_30min(self, df, window=3, min_depth_pct=0.015):
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
    
    def _calculate_rupture_factor_30min(self, atr, price, base_factor=1.008):
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
    
    def _check_momentum_filter_30min(self, df, min_idx):
        """Filtro de momentum para timeframe de 30min"""
        if min_idx < 10:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia de los últimos 10 períodos (5 horas)
        recent_10 = df.iloc[-10:]['close'].values
        trend_slope = self._calculate_slope(recent_10)
        
        # Permitir trades si la tendencia no es muy bajista
        return trend_slope > -0.05
    
    def _calculate_atr_simple(self, df, period=7):
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
    
    def _calculate_slope(self, values):
        """Calcula pendiente"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    def _simulate_trade_30min(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """Simula trade para timeframe de 30min"""
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
        hold_minutes = int((exit_time - entry_time).total_seconds() / 60)
        
        return {
            'trade_number': len(self.trades) + 1,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': return_pct,
            'hold_minutes': hold_minutes,
            'exit_reason': exit_reason,
            'max_profit': max_profit,
            'max_drawdown': max_drawdown,
            'signal_strength': signal['signal_strength'],
            'depth': signal['depth']
        }
    
    def _generate_2024_report(self, monthly_performance, monthly_trades, df):
        """
        Genera reporte completo del año 2024 con timeframe de 30min
        """
        print()
        print("📊 REPORTE COMPLETO - BITCOIN AÑO 2024 (30min TIMEFRAME)")
        print("="*80)
        
        if not self.trades:
            print("⚠️ No se generaron trades durante 2024")
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
        
        print(f"🏆 RESUMEN EJECUTIVO BITCOIN 2024 (30min):")
        print(f"   💵 Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   💰 Capital final: ${self.current_capital:,.2f}")
        print(f"   📈 Sistema U (30min): {total_return:+.2f}%")
        print(f"   📈 Buy & Hold BTC: {buy_hold_return:+.2f}%")
        print(f"   🎯 Outperformance: {total_return - buy_hold_return:+.2f} puntos porcentuales")
        print()
        
        print(f"📊 ESTADÍSTICAS DE TRADING (30min):")
        print(f"   🔢 Total trades: {total_trades}")
        print(f"   ✅ Ganadores: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"   ❌ Perdedores: {len(losing_trades)} ({100-win_rate:.1f}%)")
        print(f"   📈 Retorno promedio: {np.mean([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   🚀 Mejor trade: {max([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   💥 Peor trade: {min([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   ⏱️ Holding promedio: {np.mean([t['hold_minutes'] for t in self.trades]):.0f} minutos")
        print()
        
        # Performance mensual
        print("📅 PERFORMANCE MENSUAL:")
        print("-" * 50)
        for month in sorted(monthly_performance.keys()):
            if month in monthly_performance:
                monthly_returns = monthly_performance[month]
                avg_return = np.mean(monthly_returns)
                trade_count = monthly_trades[month]
                total_monthly = sum(monthly_returns)
                
                status = "🟢" if total_monthly > 0 else "🔴" if total_monthly < 0 else "🟡"
                
                print(f"   {status} {month}: {trade_count} trades | Avg: {avg_return:+.2f}% | Total: {total_monthly:+.2f}%")
        print()
        
        # Trades detallados (primeros 20)
        print("💰 PRIMEROS 20 TRADES DETALLADOS (30min):")
        print("-" * 80)
        
        for i, trade in enumerate(self.trades[:20]):
            status = "✅" if trade['return_pct'] > 0 else "❌"
            print(f"{status} #{trade['trade_number']} | {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} | ")
            print(f"   ${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} | ")
            print(f"   {trade['return_pct']*100:+.2f}% | {trade['hold_minutes']}min | {trade['exit_reason']}")
        
        if len(self.trades) > 20:
            print(f"   ... y {len(self.trades) - 20} trades más")
        print()
        
        # Evaluación final
        print("🎯 EVALUACIÓN FINAL (30min STRATEGY):")
        if total_return > buy_hold_return * 1.5:
            print("🟢 EXCEPCIONAL: Estrategia 30min superó significativamente a Buy & Hold!")
        elif total_return > buy_hold_return:
            print("🟢 EXCELENTE: Estrategia 30min superó a Buy & Hold")
        elif total_return > 10:
            print("🟡 BUENO: Estrategia 30min tuvo performance sólida")
        elif total_return > 0:
            print("🟡 ACEPTABLE: Estrategia 30min fue rentable")
        else:
            print("🔴 MEJORABLE: Estrategia 30min perdió dinero (revisar parámetros)")
        
        # Frecuencia de trading
        total_days = (df.index[-1] - df.index[0]).days
        trades_per_day = total_trades / total_days
        print(f"📊 Frecuencia de trading: {trades_per_day:.2f} trades por día")
        print()

def main():
    """Función principal"""
    backtest = Bitcoin1hBacktest(initial_capital=1000)
    backtest.backtest_2024_complete()

if __name__ == "__main__":
    main()