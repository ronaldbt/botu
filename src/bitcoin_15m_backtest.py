# src/bitcoin_15m_backtest.py
# Backtesting de Bitcoin para los últimos 3 meses usando intervalos de 15 minutos
# Basado en el exitoso sistema de 30 minutos con ajustes para mayor frecuencia

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from utils import log

class Bitcoin15mBacktest:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.equity_curve = [initial_capital]
        
    def get_historical_data_6months(self):
        """
        Obtiene datos históricos de Bitcoin para los últimos 6 meses usando intervalos de 15 minutos
        """
        print("📊 Obteniendo datos históricos de Bitcoin para los últimos 6 meses (15min)...")
        
        # Fechas para últimos 6 meses
        end_time = datetime.now()
        start_time = end_time - timedelta(days=180)
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        all_klines = []
        current_start = start_timestamp
        
        # Binance límite: 1000 velas por request
        # Para 15min en 90 días: ~8640 velas, necesitamos múltiples requests
        interval = "15m"
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
        
        print(f"🎯 DATOS BITCOIN 6 MESES (15min):")
        print(f"   📅 Período: {df.index[0]} a {df.index[-1]}")
        print(f"   📊 Total velas: {len(df)}")
        print(f"   💰 Precio inicial: ${df['open'].iloc[0]:,.2f}")
        print(f"   💰 Precio final: ${df['close'].iloc[-1]:,.2f}")
        print(f"   📈 Cambio período: {((df['close'].iloc[-1] / df['open'].iloc[0]) - 1) * 100:.2f}%")
        print(f"   🔝 Máximo: ${df['high'].max():,.2f}")
        print(f"   📉 Mínimo: ${df['low'].min():,.2f}")
        print()
        
        return df
    
    def backtest_6months_15min_optimized(self):
        """
        Backtesting OPTIMIZADO de los últimos 6 meses con intervalos de 15 minutos
        Parámetros ajustados basados en análisis previo
        """
        print("🚀 BACKTESTING BITCOIN OPTIMIZADO - ÚLTIMOS 6 MESES (15min)")
        print("="*80)
        print("⚡ Estrategia OPTIMIZADA basada en análisis de resultados previos")
        print("🎯 Objetivo: Mejorar win rate y frequency vs buy & hold")
        print("🔧 Parámetros ajustados para mejor performance")
        print("="*80)
        
        df = self.get_historical_data_6months()
        if df.empty:
            print("❌ No se pudieron obtener datos históricos")
            return
            
        # CONFIGURACIÓN IGUAL A 30MIN EXITOSO
        profit_target = 0.040     # 4.0% objetivo (igual que 30min exitoso)
        stop_loss = 0.015         # 1.5% stop loss (igual que 30min exitoso)
        max_hold_periods = 96     # Máximo 96 períodos (24h en 15min = 96 períodos)
        
        # Ventanas de análisis basadas en el sistema de 30min
        window_size = 32          # 8 horas de datos (equivalente a 4h en 30min)
        step_size = 4             # Avance cada 1 hora (equivalente a 2h en 30min)
        
        total_windows = (len(df) - window_size) // step_size
        print(f"🔄 Analizando {total_windows} ventanas de trading...")
        print("⚡ Configuración OPTIMIZADA: 2.0% profit target | 1.0% stop loss | Max 6h holding")
        print()
        
        # Trackear performance semanal
        weekly_performance = {}
        weekly_trades = {}
        
        for window_idx in range(total_windows):
            start_idx = window_idx * step_size
            end_idx = start_idx + window_size
            
            if end_idx >= len(df) - 50:  # Dejar datos para simular trades
                break
            
            # Datos para análisis
            analysis_df = df.iloc[start_idx:end_idx].copy()
            
            # Detectar señales usando algoritmo adaptado para 15min
            signals = self._detect_u_patterns_15min(analysis_df)
            
            for signal in signals:
                # Simular trade en datos futuros
                trade_result = self._simulate_trade_15min(
                    df, signal, end_idx, profit_target, stop_loss, max_hold_periods
                )
                
                if trade_result:
                    self.trades.append(trade_result)
                    old_capital = self.current_capital
                    self.current_capital *= (1 + trade_result['return_pct'])
                    self.equity_curve.append(self.current_capital)
                    
                    # Trackear por semana
                    week_key = f"W{trade_result['entry_time'].isocalendar()[1]}-{trade_result['entry_time'].year}"
                    if week_key not in weekly_performance:
                        weekly_performance[week_key] = []
                        weekly_trades[week_key] = 0
                    
                    weekly_performance[week_key].append(trade_result['return_pct'] * 100)
                    weekly_trades[week_key] += 1
                    
                    if len(self.trades) <= 40:  # Mostrar primeros 40 trades
                        print(f"🚀 Trade #{len(self.trades)} - {trade_result['entry_time'].strftime('%Y-%m-%d %H:%M')}")
                        print(f"   💰 ${old_capital:,.0f} → ${self.current_capital:,.0f} ({trade_result['return_pct']*100:+.2f}%)")
        
        self._generate_6months_report(weekly_performance, weekly_trades, df)
        
    def _detect_u_patterns_15min(self, df):
        """
        Detecta patrones U adaptado para intervalos de 15 minutos
        Basado en el algoritmo exitoso de 30 minutos
        """
        signals = []
        
        # Detectar mínimos significativos con parámetros OPTIMIZADOS para 15min
        significant_lows = self._detect_lows_15min(df, window=3, min_depth_pct=0.010)  # 1.0% mínimo (menos restrictivo)
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos (similar a 30min pero ajustado)
        for low in significant_lows[-2:]:  # Últimos 2 mínimos
            min_idx = low['index']
            
            # ATR y factor dinámico
            atr = self._calculate_atr_simple(df)
            current_price = df.iloc[-1]['close']
            
            # Factor adaptado para 15min (entre 30min y 5min)
            dynamic_factor = self._calculate_rupture_factor_15min(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones adaptadas para 15min
            if len(df) - min_idx > 2 and len(df) - min_idx < 16:  # Entre 30min y 4h
                recent_slope = self._calculate_slope(df.iloc[-3:]['close'].values)
                pre_slope = self._calculate_slope(df.iloc[max(0, min_idx-3):min_idx]['close'].values)
                
                # Condiciones OPTIMIZADAS para timeframe medio
                conditions = [
                    pre_slope < -0.05,  # Pendiente bajista (menos restrictivo)
                    current_price > nivel_ruptura * 0.990,  # Más cerca del nivel de ruptura
                    recent_slope > -0.010,  # Momentum menos restrictivo
                    low['depth'] >= 0.010,  # 1.0% de profundidad (menos restrictivo)
                    self._check_momentum_filter_15min(df, min_idx)
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
    
    def _detect_lows_15min(self, df, window=3, min_depth_pct=0.010):
        """Detecta mínimos OPTIMIZADOS para intervalos de 15min"""
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
                    
                    if current_volume > volume_avg * 0.60 or depth >= 0.015:  # Menos restrictivo
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
    
    def _calculate_rupture_factor_15min(self, atr, price, base_factor=1.006):
        """Factor de ruptura adaptado para 15min"""
        atr_pct = atr / price
        
        # Adaptado entre 30min y 5min
        if atr_pct < 0.008:
            factor = base_factor
        elif atr_pct < 0.015:
            factor = base_factor + (atr_pct * 0.15)
        else:
            factor = min(base_factor + (atr_pct * 0.25), 1.020)  # Máximo 2% para 15min
        
        return max(factor, 1.006)  # Mínimo 0.6%
    
    def _check_momentum_filter_15min(self, df, min_idx):
        """Filtro de momentum para timeframe de 15min"""
        if min_idx < 8:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia de los últimos 8 períodos (2 horas)
        recent_8 = df.iloc[-8:]['close'].values
        trend_slope = self._calculate_slope(recent_8)
        
        # Permitir trades si la tendencia no es muy bajista
        return trend_slope > -0.04
    
    def _calculate_atr_simple(self, df, period=6):
        """Calcula ATR simplificado para 15min"""
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
    
    def _simulate_trade_15min(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """Simula trade para timeframe de 15min"""
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
    
    def _generate_6months_report(self, weekly_performance, weekly_trades, df):
        """
        Genera reporte completo de los últimos 6 meses con timeframe de 15min
        """
        print()
        print("📊 REPORTE OPTIMIZADO - BITCOIN ÚLTIMOS 6 MESES (15min TIMEFRAME)")
        print("="*80)
        
        if not self.trades:
            print("⚠️ No se generaron trades durante los últimos 6 meses")
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
        
        print(f"🏆 RESUMEN EJECUTIVO BITCOIN 6 MESES OPTIMIZADO (15min):")
        print(f"   💵 Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   💰 Capital final: ${self.current_capital:,.2f}")
        print(f"   📈 Sistema U Optimizado (15min): {total_return:+.2f}%")
        print(f"   📈 Buy & Hold BTC (6 meses): {buy_hold_return:+.2f}%")
        print(f"   🎯 Diferencia vs Buy & Hold: {total_return - buy_hold_return:+.2f} puntos")
        
        # Análisis de rentabilidad anualizada
        total_days = (df.index[-1] - df.index[0]).days
        annualized_return = ((self.current_capital / self.initial_capital) ** (365 / total_days) - 1) * 100
        annualized_btc = ((btc_end_price / btc_start_price) ** (365 / total_days) - 1) * 100
        
        print(f"   📊 Rentabilidad anualizada Sistema: {annualized_return:+.2f}%")
        print(f"   📊 Rentabilidad anualizada BTC: {annualized_btc:+.2f}%")
        print()
        
        print(f"📊 ESTADÍSTICAS DE TRADING (15min MEDIA-FRECUENCIA):")
        print(f"   🔢 Total trades: {total_trades}")
        print(f"   ✅ Ganadores: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"   ❌ Perdedores: {len(losing_trades)} ({100-win_rate:.1f}%)")
        print(f"   📈 Retorno promedio: {np.mean([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   🚀 Mejor trade: {max([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   💥 Peor trade: {min([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   ⏱️ Holding promedio: {np.mean([t['hold_minutes'] for t in self.trades]):.0f} minutos")
        print()
        
        # Performance semanal
        print("📅 PERFORMANCE SEMANAL (15min):")
        print("-" * 60)
        for week in sorted(weekly_performance.keys()):
            if week in weekly_performance:
                weekly_returns = weekly_performance[week]
                avg_return = np.mean(weekly_returns)
                trade_count = weekly_trades[week]
                total_weekly = sum(weekly_returns)
                
                status = "🟢" if total_weekly > 0 else "🔴" if total_weekly < 0 else "🟡"
                
                print(f"   {status} {week}: {trade_count} trades | Avg: {avg_return:+.2f}% | Total: {total_weekly:+.2f}%")
        print()
        
        # Análisis de frecuencia
        total_days = (df.index[-1] - df.index[0]).days
        trades_per_day = total_trades / total_days
        trades_per_week = total_trades / (total_days / 7)
        
        print(f"⚡ ANÁLISIS DE FRECUENCIA (15min STRATEGY):")
        print(f"   📊 Trades por día: {trades_per_day:.1f}")
        print(f"   📊 Trades por semana: {trades_per_week:.1f}")
        print(f"   📊 Días con trading: {total_days}")
        print()
        
        # Trades detallados (primeros 30)
        print("💰 PRIMEROS 30 TRADES DETALLADOS (15min):")
        print("-" * 90)
        
        for i, trade in enumerate(self.trades[:30]):
            status = "✅" if trade['return_pct'] > 0 else "❌"
            print(f"{status} #{trade['trade_number']} | {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} | ")
            print(f"   ${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} | ")
            print(f"   {trade['return_pct']*100:+.2f}% | {trade['hold_minutes']}min | {trade['exit_reason']}")
        
        if len(self.trades) > 30:
            print(f"   ... y {len(self.trades) - 30} trades más")
        print()
        
        # Evaluación final
        print("🎯 EVALUACIÓN FINAL (15min STRATEGY):")
        if total_return > buy_hold_return * 1.5:
            print("🟢 EXCEPCIONAL: Estrategia 15min superó significativamente a Buy & Hold!")
        elif total_return > buy_hold_return:
            print("🟢 EXCELENTE: Estrategia 15min superó a Buy & Hold")
        elif total_return > 8:
            print("🟡 BUENO: Estrategia 15min tuvo performance sólida")
        elif total_return > 0:
            print("🟡 ACEPTABLE: Estrategia 15min fue rentable")
        else:
            print("🔴 MEJORABLE: Estrategia 15min perdió dinero (revisar parámetros)")
        
        # Comparación con otros timeframes
        print(f"📈 Factor de rendimiento vs Buy & Hold: {total_return / buy_hold_return if buy_hold_return != 0 else 'N/A':.2f}x")
        print(f"📊 Eficiencia de trading: {trades_per_day:.1f} trades/día vs 30min≈0.1 trades/día")
        print()

def main():
    """Función principal"""
    print("🚀 Iniciando backtest OPTIMIZADO Bitcoin 15min para últimos 6 meses...")
    backtest = Bitcoin15mBacktest(initial_capital=1000)
    backtest.backtest_6months_15min_optimized()

if __name__ == "__main__":
    main()