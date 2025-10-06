# src/bitcoin_2023_backtest.py
# Backtesting completo de Bitcoin para el año 2023 usando datos históricos reales

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
from utils import log

class Bitcoin2023Backtest:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.equity_curve = [initial_capital]
        
    def get_historical_data_2023(self):
        """
        Obtiene datos históricos de Bitcoin para todo 2023 usando Binance API
        """
        print("📊 Obteniendo datos históricos de Bitcoin para 2023...")
        
        # Fechas para 2023 completo
        start_time = int(datetime(2023, 1, 1).timestamp() * 1000)
        end_time = int(datetime(2023, 12, 31, 23, 59, 59).timestamp() * 1000)
        
        all_klines = []
        current_start = start_time
        
        # Binance límite: 1000 velas por request
        # Para 4h en un año: ~2190 velas, necesitamos múltiples requests
        interval = "4h"
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
        
        print(f"🎯 DATOS BITCOIN 2023 COMPLETOS:")
        print(f"   📅 Período: {df.index[0]} a {df.index[-1]}")
        print(f"   📊 Total velas: {len(df)}")
        print(f"   💰 Precio inicial: ${df['open'].iloc[0]:,.2f}")
        print(f"   💰 Precio final: ${df['close'].iloc[-1]:,.2f}")
        print(f"   📈 Cambio anual: {((df['close'].iloc[-1] / df['open'].iloc[0]) - 1) * 100:.2f}%")
        print(f"   🔝 Máximo: ${df['high'].max():,.2f}")
        print(f"   📉 Mínimo: ${df['low'].min():,.2f}")
        print()
        
        return df
    
    def backtest_2023_complete(self):
        """
        Backtesting completo del año 2023
        """
        print("🚀 BACKTESTING BITCOIN - AÑO 2023 COMPLETO")
        print("="*80)
        print("🎢 NOTA: 2023 fue el año de la RECUPERACIÓN - Bull market regresa!")
        print("📈 Bitcoin subió de ~$16K a ~$42K (+162%)")
        print("🏆 Este será el año donde el sistema debería brillar más")
        print("="*80)
        
        df = self.get_historical_data_2023()
        if df.empty:
            print("❌ No se pudieron obtener datos históricos de 2023")
            return
            
        # Configuración del sistema optimizada para BTC
        profit_target = 0.08  # 8% objetivo (ajustado para BTC menos volátil)
        stop_loss = 0.03      # 3% stop loss (más ajustado)
        max_hold_periods = 80   # Máximo 80 períodos (320h = ~13 días)
        
        # Ventanas de análisis optimizadas para BTC
        window_size = 120  # Ventana más pequeña para BTC
        step_size = 8      # Avance más frecuente para capturar más oportunidades
        
        total_windows = (len(df) - window_size) // step_size
        print(f"🔄 Analizando {total_windows} ventanas de trading en 2023...")
        print("⚡ Configuración BTC optimizada: 8% profit target | 3% stop loss | Max 13 días holding")
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
            
            # Detectar señales usando algoritmo optimizado para bull market
            signals = self._detect_u_patterns_2023(analysis_df)
            
            for signal in signals:
                # Simular trade en datos futuros
                trade_result = self._simulate_trade_2023(
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
                    
                    print(f"🚀 Trade #{len(self.trades)} - {trade_result['entry_time'].strftime('%Y-%m-%d')}")
                    print(f"   💰 ${old_capital:,.0f} → ${self.current_capital:,.0f} ({trade_result['return_pct']*100:+.2f}%)")
        
        self._generate_2023_report(monthly_performance, monthly_trades, df)
        
    def _detect_u_patterns_2023(self, df):
        """
        Detecta patrones U optimizado para bull market de 2023
        """
        signals = []
        
        # Detectar mínimos significativos con parámetros más agresivos para bull market
        significant_lows = self._detect_lows_2023(df, window=6, min_depth_pct=0.025)  # 2.5% mínimo (BTC menos volátil)
        
        if not significant_lows:
            return signals
            
        # Analizar múltiples mínimos para bull market
        for low in significant_lows[-4:]:  # Últimos 4 mínimos (más oportunidades)
            min_idx = low['index']
            
            # ATR y factor dinámico
            atr = self._calculate_atr_simple(df)
            current_price = df.iloc[-1]['close']
            
            # Factor más agresivo para bull market
            dynamic_factor = self._calculate_rupture_factor_bull(atr, current_price)
            nivel_ruptura = low['high'] * dynamic_factor
            
            # Condiciones optimizadas para BTC en bull market
            if len(df) - min_idx > 4 and len(df) - min_idx < 45:
                recent_slope = self._calculate_slope(df.iloc[-6:]['close'].values)
                pre_slope = self._calculate_slope(df.iloc[max(0, min_idx-6):min_idx]['close'].values)
                
                # Condiciones más estrictas para BTC (menos volátil)
                conditions = [
                    pre_slope < -0.12,  # Más restrictivo para BTC
                    current_price > nivel_ruptura * 0.97,  # Más conservador (97% vs 95%)
                    recent_slope > -0.03,  # Momentum más positivo requerido
                    low['depth'] >= 0.025,  # Al menos 2.5% de profundidad
                    # Filtro adicional: evitar trades en tendencias bajistas prolongadas
                    self._check_momentum_filter(df, min_idx)
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
    
    def _detect_lows_2023(self, df, window=6, min_depth_pct=0.025):
        """Detecta mínimos optimizados para BTC en bull market de 2023"""
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
    
    def _calculate_rupture_factor_bull(self, atr, price, base_factor=1.015):
        """Factor de ruptura optimizado para BTC (más conservador)"""
        atr_pct = atr / price
        
        # Más conservador para BTC (menos volátil)
        if atr_pct < 0.015:
            factor = base_factor
        elif atr_pct < 0.03:
            factor = base_factor + (atr_pct * 0.3)  # Menos agresivo
        else:
            factor = min(base_factor + (atr_pct * 0.5), 1.05)  # Máximo 5% para BTC
        
        return max(factor, 1.015)  # Mínimo 1.5%
    
    def _check_momentum_filter(self, df, min_idx):
        """Filtro de momentum para evitar trades en tendencias bajistas prolongadas"""
        if min_idx < 20:
            return True  # No hay suficientes datos para evaluar
        
        # Verificar tendencia de los últimos 20 períodos
        recent_20 = df.iloc[-20:]['close'].values
        trend_slope = self._calculate_slope(recent_20)
        
        # Solo permitir trades si la tendencia general no es muy bajista
        return trend_slope > -0.1  # Permitir trades si pendiente > -0.1
    
    def _calculate_atr_simple(self, df, period=14):
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
    
    def _calculate_slope(self, values):
        """Calcula pendiente"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    def _simulate_trade_2023(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """Simula trade en 2023 (bull market)"""
        entry_price = signal['entry_price']
        entry_time = signal['timestamp']
        
        future_data = df.iloc[start_idx:start_idx + max_hold + 50]
        if len(future_data) < 5:
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
    
    def _generate_2023_report(self, monthly_performance, monthly_trades, df):
        """
        Genera reporte completo del año 2023
        """
        print()
        print("📊 REPORTE COMPLETO - BITCOIN 2023 (BULL MARKET RECOVERY)")
        print("="*80)
        
        if not self.trades:
            print("⚠️ No se generaron trades durante 2023")
            print("🤔 Esto sería extraño en un bull market...")
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
        
        print(f"🏆 RESUMEN EJECUTIVO BITCOIN 2023:")
        print(f"   💵 Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   💰 Capital final: ${self.current_capital:,.2f}")
        print(f"   📈 Sistema U: {total_return:+.2f}%")
        print(f"   📈 Buy & Hold BTC: {buy_hold_return:+.2f}%")
        print(f"   🎯 Outperformance: {total_return - buy_hold_return:+.2f} puntos porcentuales")
        print()
        
        print(f"📊 ESTADÍSTICAS DE TRADING:")
        print(f"   🔢 Total trades: {total_trades}")
        print(f"   ✅ Ganadores: {len(winning_trades)} ({win_rate:.1f}%)")
        print(f"   ❌ Perdedores: {len(losing_trades)} ({100-win_rate:.1f}%)")
        print(f"   📈 Retorno promedio: {np.mean([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   🚀 Mejor trade: {max([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print(f"   💥 Peor trade: {min([t['return_pct'] for t in self.trades]) * 100:.2f}%")
        print()
        
        # Performance mensual
        print("📅 PERFORMANCE MENSUAL 2023:")
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
        
        # Trades detallados (solo primeros 15 para bull market)
        print("💰 PRIMEROS 15 TRADES DETALLADOS:")
        print("-" * 80)
        
        for i, trade in enumerate(self.trades[:15]):
            status = "✅" if trade['return_pct'] > 0 else "❌"
            print(f"{status} #{trade['trade_number']} | {trade['entry_time'].strftime('%Y-%m-%d')} | ")
            print(f"   ${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} | ")
            print(f"   {trade['return_pct']*100:+.2f}% | {trade['hold_hours']}h | {trade['exit_reason']}")
        
        if len(self.trades) > 15:
            print(f"   ... y {len(self.trades) - 15} trades más")
        print()
        
        # Evaluación final
        print("🎯 EVALUACIÓN FINAL 2023:")
        if total_return > buy_hold_return and total_return > 100:
            print("🟢 EXCEPCIONAL: Sistema superó a Buy & Hold en bull market!")
        elif total_return > 50:
            print("🟢 EXCELENTE: Sistema aprovechó muy bien el bull market")
        elif total_return > 20:
            print("🟡 BUENO: Sistema tuvo performance sólida")
        elif total_return > 0:
            print("🟡 ACEPTABLE: Sistema fue rentable")
        else:
            print("🔴 MEJORABLE: Sistema perdió dinero en bull market (necesita revisión)")
        print()

def main():
    """Función principal"""
    backtest = Bitcoin2023Backtest(initial_capital=1000)
    backtest.backtest_2023_complete()

if __name__ == "__main__":
    main()