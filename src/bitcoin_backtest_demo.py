# src/bitcoin_backtest_demo.py
# Backtesting específico para Bitcoin con datos reales de Binance

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance_client import fetch_klines
from scanner_crypto import scan_crypto_for_u, detect_significant_lows, calculate_atr, calculate_dynamic_rupture_factor
from utils import log

class BitcoinBacktestDemo:
    def __init__(self, initial_capital=1000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.positions = []
        self.equity_curve = [initial_capital]
        
    def backtest_bitcoin_realistic(self, timeframe='4h', lookback_limit=1000):
        """
        Backtesting realista de Bitcoin usando datos disponibles de Binance
        Simula el comportamiento del sistema con datos reales
        """
        print(f"🚀 Backtesting Bitcoin con ${self.initial_capital} inicial")
        print(f"📊 Usando timeframe {timeframe} con {lookback_limit} velas")
        print("="*70)
        
        # Obtener datos históricos máximos disponibles
        klines = fetch_klines('BTCUSDT', timeframe, lookback_limit)
        if not klines:
            print("❌ No se pudieron obtener datos de Bitcoin")
            return
            
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Datos obtenidos: {len(df)} velas desde {df.index[0]} hasta {df.index[-1]}")
        print(f"📈 Rango de precios: ${df['low'].min():,.2f} - ${df['high'].max():,.2f}")
        print()
        
        # Configuración del sistema
        profit_target = 0.12  # 12% objetivo
        stop_loss = 0.05      # 5% stop loss
        max_hold_periods = 100  # Máximo 100 períodos (400h = ~16 días)
        
        # Dividir datos en ventanas para simular trading en tiempo real
        window_size = 200  # Ventana de análisis
        step_size = 20     # Avance de ventana
        
        total_windows = (len(df) - window_size) // step_size
        print(f"🔄 Analizando {total_windows} ventanas de trading...")
        print()
        
        for window_idx in range(total_windows):
            start_idx = window_idx * step_size
            end_idx = start_idx + window_size
            
            if end_idx >= len(df) - 50:  # Dejar datos para simular trades
                break
            
            # Datos para análisis
            analysis_df = df.iloc[start_idx:end_idx].copy()
            
            # Detectar señales usando nuestro algoritmo
            signals = self._detect_u_patterns(analysis_df)
            
            for signal in signals:
                # Simular trade en datos futuros (out-of-sample)
                trade_result = self._simulate_trade(
                    df, signal, end_idx, profit_target, stop_loss, max_hold_periods
                )
                
                if trade_result:
                    self.trades.append(trade_result)
                    self.current_capital *= (1 + trade_result['return_pct'])
                    self.equity_curve.append(self.current_capital)
        
        self._generate_comprehensive_report()
        
    def _detect_u_patterns(self, df):
        """
        Detecta patrones U en los datos usando lógica similar al scanner real
        """
        signals = []
        
        # Detectar mínimos significativos manualmente (evitar función que requiere timestamp column)
        significant_lows = self._detect_lows_manual(df, window=10, min_depth_pct=0.03)
        
        if not significant_lows:
            return signals
            
        # Analizar el último mínimo
        last_low = significant_lows[-1]
        min_idx = last_low['index']
        
        # Calcular ATR para factor dinámico
        atr = self._calculate_atr_simple(df)
        current_price = df.iloc[-1]['close']
        
        # Factor de ruptura dinámico
        dynamic_factor = self._calculate_rupture_factor(atr, current_price)
        nivel_ruptura = last_low['high'] * dynamic_factor
        
        # Verificar si hay momentum alcista
        if len(df) - min_idx > 10:
            recent_slope = self._calculate_slope(df.iloc[-10:]['close'].values)
            pre_slope = self._calculate_slope(df.iloc[max(0, min_idx-10):min_idx]['close'].values) 
            
            # Condiciones para señal U
            conditions = [
                pre_slope < -0.3,  # Pendiente bajista antes del mínimo
                current_price > nivel_ruptura * 0.98,  # Cerca del nivel de ruptura
                recent_slope > 0,  # Momentum alcista reciente
                len(df) - min_idx >= 5,  # Tiempo suficiente desde mínimo
                len(df) - min_idx <= 50   # No demasiado tiempo
            ]
            
            if all(conditions):
                signals.append({
                    'timestamp': df.index[-1],
                    'entry_price': nivel_ruptura,
                    'signal_strength': abs(pre_slope),
                    'min_price': last_low['low'],
                    'pattern_width': len(df) - min_idx,
                    'atr': atr,
                    'dynamic_factor': dynamic_factor
                })
                
        return signals
    
    def _detect_lows_manual(self, df, window=10, min_depth_pct=0.03):
        """
        Detecta mínimos locales significativos manualmente
        """
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
            
            # Verificar que es mínimo en la ventana
            window_slice = df.iloc[i-window:i+window+1]
            if current_low == window_slice['low'].min():
                
                # Verificar profundidad: debe ser X% más bajo que máximo local
                local_high = window_slice['high'].max()
                depth = (local_high - current_low) / local_high
                
                if depth >= min_depth_pct:
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
    
    def _calculate_rupture_factor(self, atr, price, base_factor=1.03):
        """Calcula factor de ruptura dinámico"""
        atr_pct = atr / price
        
        if atr_pct < 0.02:  # Baja volatilidad
            factor = base_factor
        elif atr_pct < 0.05:  # Volatilidad media
            factor = base_factor + (atr_pct * 0.5)
        else:  # Alta volatilidad
            factor = min(base_factor + (atr_pct * 0.8), 1.08)  # Máximo 8%
        
        return max(factor, 1.03)  # Mínimo 3%
    
    def _calculate_slope(self, values):
        """Calcula la pendiente de una serie de valores"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    def _simulate_trade(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """
        Simula un trade completo desde la señal hasta la salida
        """
        entry_price = signal['entry_price']
        entry_time = signal['timestamp']
        
        # Datos futuros para simular el trade
        future_data = df.iloc[start_idx:start_idx + max_hold + 50]
        if len(future_data) < 10:
            return None
            
        target_price = entry_price * (1 + profit_target)
        stop_price = entry_price * (1 - stop_loss)
        
        max_profit = 0
        max_drawdown = 0
        
        for i, (timestamp, row) in enumerate(future_data.iterrows()):
            if i > max_hold:
                # Salida por tiempo máximo
                exit_price = row['close']
                exit_reason = "MAX_HOLD"
                exit_time = timestamp
                break
                
            high = row['high']
            low = row['low']
            close = row['close']
            
            # Tracking de performance
            current_profit = (high - entry_price) / entry_price
            current_loss = (entry_price - low) / entry_price
            max_profit = max(max_profit, current_profit)
            max_drawdown = max(max_drawdown, current_loss)
            
            # Take profit
            if high >= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
                exit_time = timestamp
                break
                
            # Stop loss
            if low <= stop_price:
                exit_price = stop_price
                exit_reason = "STOP_LOSS"
                exit_time = timestamp
                break
                
        else:
            # Final de datos
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
            'pattern_width': signal['pattern_width'],
            'target_price': target_price,
            'stop_price': stop_price
        }
    
    def _generate_comprehensive_report(self):
        """
        Genera reporte completo del backtesting
        """
        print("💰 REPORTE DETALLADO DE BACKTESTING")
        print("="*70)
        
        if not self.trades:
            print("⚠️ No se generaron trades durante el período analizado")
            print("🔍 Posibles causas:")
            print("   • Condiciones muy estrictas para detectar patrones U")
            print("   • Período sin formaciones de U válidas")
            print("   • Bitcoin en tendencia lateral sin rupturas claras")
            return
            
        # Estadísticas generales
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['return_pct'] > 0]
        losing_trades = [t for t in self.trades if t['return_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        total_return = (self.current_capital / self.initial_capital - 1) * 100
        
        avg_return = np.mean([t['return_pct'] for t in self.trades]) * 100
        avg_winner = np.mean([t['return_pct'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loser = np.mean([t['return_pct'] for t in losing_trades]) * 100 if losing_trades else 0
        
        best_trade = max([t['return_pct'] for t in self.trades]) * 100
        worst_trade = min([t['return_pct'] for t in self.trades]) * 100
        
        avg_hold = np.mean([t['hold_hours'] for t in self.trades])
        
        print(f"📊 RESUMEN EJECUTIVO:")
        print(f"   💵 Capital inicial: ${self.initial_capital:,.2f}")
        print(f"   💰 Capital final: ${self.current_capital:,.2f}")
        print(f"   📈 Ganancia/Pérdida total: ${self.current_capital - self.initial_capital:+,.2f} ({total_return:+.2f}%)")
        print()
        
        print(f"🎯 ESTADÍSTICAS DE TRADING:")
        print(f"   🔢 Total de trades: {total_trades}")
        print(f"   ✅ Trades ganadores: {len(winning_trades)} ({len(winning_trades)/total_trades*100:.1f}%)")
        print(f"   ❌ Trades perdedores: {len(losing_trades)} ({len(losing_trades)/total_trades*100:.1f}%)")
        print(f"   🎊 Tasa de éxito: {win_rate:.1f}%")
        print()
        
        print(f"📊 RENDIMIENTO:")
        print(f"   📈 Retorno promedio por trade: {avg_return:+.2f}%")
        print(f"   🟢 Promedio ganadores: +{avg_winner:.2f}%")
        print(f"   🔴 Promedio perdedores: {avg_loser:.2f}%")
        print(f"   🚀 Mejor trade: +{best_trade:.2f}%")
        print(f"   💥 Peor trade: {worst_trade:.2f}%")
        print(f"   ⏱️ Tiempo promedio en posición: {avg_hold:.1f} horas")
        print()
        
        # Detalle de cada trade
        print("📋 HISTORIAL DETALLADO DE TRADES:")
        print("="*70)
        
        for trade in self.trades:
            capital_antes = self.initial_capital
            for prev_trade in self.trades[:trade['trade_number']-1]:
                capital_antes *= (1 + prev_trade['return_pct'])
                
            btc_amount = capital_antes / trade['entry_price']
            capital_despues = capital_antes * (1 + trade['return_pct'])
            profit_loss = capital_despues - capital_antes
            
            status = "✅ GANANCIA" if trade['return_pct'] > 0 else "❌ PÉRDIDA"
            
            print(f"Trade #{trade['trade_number']} - {trade['entry_time'].strftime('%Y-%m-%d %H:%M')} - {status}")
            print(f"   💵 Capital: ${capital_antes:,.2f} → ${capital_despues:,.2f}")
            print(f"   🟡 COMPRA: {btc_amount:.6f} BTC a ${trade['entry_price']:,.2f}")
            print(f"   🔄 VENTA: {btc_amount:.6f} BTC a ${trade['exit_price']:,.2f}")
            print(f"   📊 Return: {trade['return_pct']*100:+.2f}% | Hold: {trade['hold_hours']}h | Exit: {trade['exit_reason']}")
            print(f"   💰 P&L: ${profit_loss:+,.2f}")
            print(f"   📈 Max profit: +{trade['max_profit']*100:.2f}% | Max DD: -{trade['max_drawdown']*100:.2f}%")
            print(f"   🎯 Target: ${trade['target_price']:,.2f} | Stop: ${trade['stop_price']:,.2f}")
            print("-" * 70)
        
        # Evaluación final
        print("🎯 EVALUACIÓN FINAL:")
        if win_rate >= 60 and total_return > 0:
            print("🟢 EXCELENTE: Alta tasa de éxito y rentabilidad positiva")
        elif win_rate >= 40 and total_return > 0:
            print("🟡 BUENO: Rentabilidad positiva con tasa de éxito aceptable")
        elif total_return > 0:
            print("🟡 ACEPTABLE: Rentabilidad positiva pero baja tasa de éxito")
        else:
            print("🔴 MEJORABLE: Sistema necesita optimización")

def main():
    """Función principal para ejecutar el backtesting"""
    backtest = BitcoinBacktestDemo(initial_capital=1000)
    backtest.backtest_bitcoin_realistic(timeframe='4h', lookback_limit=1000)

if __name__ == "__main__":
    main()