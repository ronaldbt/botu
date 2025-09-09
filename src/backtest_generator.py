# src/backtest_generator.py
# Generador automático de backtests para todas las criptomonedas y años

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import json
import os
from utils import log

class BacktestGenerator:
    def __init__(self):
        self.crypto_configs = {
            'BTC': {
                'symbol': 'BTCUSDT',
                'name': 'Bitcoin',
                'emoji': '₿',
                'base_profit_target': 0.12,
                'base_stop_loss': 0.05,
                'volatility_multiplier': 1.0,
                'min_depth': 0.04
            },
            'ETH': {
                'symbol': 'ETHUSDT',
                'name': 'Ethereum',
                'emoji': 'Ξ',
                'base_profit_target': 0.12,
                'base_stop_loss': 0.05,
                'volatility_multiplier': 1.1,
                'min_depth': 0.035
            },
            'BNB': {
                'symbol': 'BNBUSDT',
                'name': 'Binance Coin',
                'emoji': '🟡',
                'base_profit_target': 0.10,
                'base_stop_loss': 0.04,
                'volatility_multiplier': 0.8,
                'min_depth': 0.03
            }
        }
        
        self.year_configs = {
            2022: {
                'market_type': 'bear',
                'description': 'Crypto Winter - Mercado bajista brutal',
                'profit_adjustment': 0.0,  # Sin ajuste para bear market
                'window_size': 150,
                'step_size': 10
            },
            2023: {
                'market_type': 'recovery',
                'description': 'Bull Market Recovery - Regresa el optimismo',
                'profit_adjustment': 0.03,  # +3% más agresivo
                'window_size': 120,
                'step_size': 6
            },
            2024: {
                'market_type': 'bull',
                'description': 'Bull Market Consolidation - Nuevos máximos',
                'profit_adjustment': 0.05,  # +5% más agresivo
                'window_size': 100,
                'step_size': 5
            }
        }
        
    def generate_all_backtests(self):
        """Genera todos los backtests necesarios"""
        results = {}
        
        for year in [2022, 2023, 2024]:
            results[year] = {}
            for crypto in ['BTC', 'ETH', 'BNB']:
                print(f"\n{'='*60}")
                print(f"🚀 GENERANDO BACKTEST {crypto} {year}")
                print(f"{'='*60}")
                
                try:
                    backtest_result = self.run_backtest(crypto, year)
                    results[year][crypto] = backtest_result
                    
                    # Guardar resultado individual
                    self.save_backtest_result(crypto, year, backtest_result)
                    
                    print(f"✅ Backtest {crypto} {year} completado")
                    
                except Exception as e:
                    print(f"❌ Error en backtest {crypto} {year}: {e}")
                    results[year][crypto] = None
                
                # Pausa entre backtests para no saturar la API
                time.sleep(2)
        
        # Guardar todos los resultados
        self.save_all_results(results)
        return results
    
    def run_backtest(self, crypto, year):
        """Ejecuta un backtest específico"""
        crypto_config = self.crypto_configs[crypto]
        year_config = self.year_configs[year]
        
        # Obtener datos históricos
        df = self.get_historical_data(crypto_config['symbol'], year)
        if df.empty:
            raise Exception(f"No se pudieron obtener datos para {crypto} {year}")
        
        # Configurar parámetros
        profit_target = crypto_config['base_profit_target'] + year_config['profit_adjustment']
        stop_loss = crypto_config['base_stop_loss']
        max_hold_periods = 100 if year_config['market_type'] == 'bear' else 80
        
        # Ejecutar backtest
        trades = []
        initial_capital = 1000
        current_capital = initial_capital
        
        window_size = year_config['window_size']
        step_size = year_config['step_size']
        
        total_windows = (len(df) - window_size) // step_size
        
        for window_idx in range(total_windows):
            start_idx = window_idx * step_size
            end_idx = start_idx + window_size
            
            if end_idx >= len(df) - 50:
                break
            
            analysis_df = df.iloc[start_idx:end_idx].copy()
            signals = self.detect_u_patterns(analysis_df, crypto_config, year_config)
            
            for signal in signals:
                trade_result = self.simulate_trade(
                    df, signal, end_idx, profit_target, stop_loss, max_hold_periods
                )
                
                if trade_result:
                    trades.append(trade_result)
                    current_capital *= (1 + trade_result['return_pct'])
        
        # Calcular estadísticas
        if not trades:
            return self.create_empty_result(crypto, year, df, initial_capital)
        
        return self.calculate_backtest_stats(
            crypto, year, df, trades, initial_capital, current_capital
        )
    
    def get_historical_data(self, symbol, year):
        """Obtiene datos históricos para un año específico"""
        start_time = int(datetime(year, 1, 1).timestamp() * 1000)
        end_time = int(datetime(year, 12, 31, 23, 59, 59).timestamp() * 1000)
        
        all_klines = []
        current_start = start_time
        interval = "4h"
        limit = 1000
        
        while current_start < end_time:
            try:
                url = "https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': symbol,
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
                last_timestamp = klines[-1][0]
                current_start = last_timestamp + 1
                
                time.sleep(0.1)  # Rate limit
                
            except Exception as e:
                print(f"Error obteniendo datos: {e}")
                break
        
        if not all_klines:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def detect_u_patterns(self, df, crypto_config, year_config):
        """Detecta patrones U adaptados por crypto y año"""
        signals = []
        window = 8 if year_config['market_type'] == 'bear' else 6
        min_depth = crypto_config['min_depth']
        
        # Detectar mínimos significativos
        significant_lows = self.detect_lows(df, window, min_depth)
        if not significant_lows:
            return signals
        
        for low in significant_lows[-3:]:
            min_idx = low['index']
            atr = self.calculate_atr_simple(df)
            current_price = df.iloc[-1]['close']
            
            # Factor de ruptura adaptativo
            base_factor = 1.025 if year_config['market_type'] == 'bear' else 1.035
            dynamic_factor = self.calculate_rupture_factor(atr, current_price, base_factor)
            nivel_ruptura = low['high'] * dynamic_factor
            
            if len(df) - min_idx > 3 and len(df) - min_idx < 60:
                recent_slope = self.calculate_slope(df.iloc[-8:]['close'].values)
                pre_slope = self.calculate_slope(df.iloc[max(0, min_idx-8):min_idx]['close'].values)
                
                # Condiciones adaptativas por mercado
                slope_threshold = -0.2 if year_config['market_type'] == 'bear' else -0.15
                price_threshold = 0.96 if year_config['market_type'] == 'bear' else 0.94
                
                conditions = [
                    pre_slope < slope_threshold,
                    current_price > nivel_ruptura * price_threshold,
                    recent_slope > -0.1,
                    low['depth'] >= min_depth * 0.8,
                ]
                
                if all(conditions):
                    signals.append({
                        'timestamp': df.index[-1],
                        'entry_price': nivel_ruptura,
                        'signal_strength': abs(pre_slope),
                        'min_price': low['low'],
                        'pattern_width': len(df) - min_idx,
                        'depth': low['depth']
                    })
                    break
                    
        return signals
    
    def detect_lows(self, df, window, min_depth_pct):
        """Detecta mínimos locales"""
        lows = []
        
        for i in range(window, len(df) - window):
            current_low = df.iloc[i]['low']
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
                        'depth': depth
                    })
        
        return lows
    
    def calculate_rupture_factor(self, atr, price, base_factor):
        """Calcula factor de ruptura dinámico"""
        atr_pct = atr / price
        
        if atr_pct < 0.025:
            factor = base_factor
        elif atr_pct < 0.05:
            factor = base_factor + (atr_pct * 0.3)
        else:
            factor = min(base_factor + (atr_pct * 0.5), 1.08)
        
        return max(factor, base_factor)
    
    def calculate_atr_simple(self, df, period=14):
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
    
    def calculate_slope(self, values):
        """Calcula pendiente"""
        if len(values) < 2:
            return 0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
    def simulate_trade(self, df, signal, start_idx, profit_target, stop_loss, max_hold):
        """Simula ejecución de trade"""
        entry_price = signal['entry_price']
        entry_time = signal['timestamp']
        
        future_data = df.iloc[start_idx:start_idx + max_hold + 50]
        if len(future_data) < 5:
            return None
            
        target_price = entry_price * (1 + profit_target)
        stop_price = entry_price * (1 - stop_loss)
        
        for i, (timestamp, row) in enumerate(future_data.iterrows()):
            if i > max_hold:
                exit_price = row['close']
                exit_reason = "MAX_HOLD"
                exit_time = timestamp
                break
                
            if row['high'] >= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
                exit_time = timestamp
                break
                
            if row['low'] <= stop_price:
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
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_pct': return_pct,
            'hold_hours': hold_hours,
            'exit_reason': exit_reason,
            'signal_strength': signal['signal_strength']
        }
    
    def calculate_backtest_stats(self, crypto, year, df, trades, initial_capital, final_capital):
        """Calcula estadísticas del backtest"""
        crypto_config = self.crypto_configs[crypto]
        year_config = self.year_configs[year]
        
        # Estadísticas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['return_pct'] > 0]
        losing_trades = [t for t in trades if t['return_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        total_return = (final_capital / initial_capital - 1) * 100
        
        # Buy & Hold comparison
        start_price = df['open'].iloc[0]
        end_price = df['close'].iloc[-1]
        buy_hold_return = (end_price / start_price - 1) * 100
        
        # Performance mensual
        monthly_performance = {}
        for trade in trades:
            month_key = trade['entry_time'].strftime('%Y-%m')
            if month_key not in monthly_performance:
                monthly_performance[month_key] = []
            monthly_performance[month_key].append(trade['return_pct'] * 100)
        
        return {
            'crypto': crypto,
            'year': year,
            'crypto_config': crypto_config,
            'year_config': year_config,
            'period': {
                'start': df.index[0].strftime('%Y-%m-%d'),
                'end': df.index[-1].strftime('%Y-%m-%d'),
                'total_candles': len(df)
            },
            'price_data': {
                'start_price': float(start_price),
                'end_price': float(end_price),
                'max_price': float(df['high'].max()),
                'min_price': float(df['low'].min()),
                'price_change_pct': float(buy_hold_return)
            },
            'trading_stats': {
                'initial_capital': float(initial_capital),
                'final_capital': float(final_capital),
                'total_return_pct': float(total_return),
                'buy_hold_return_pct': float(buy_hold_return),
                'outperformance_pct': float(total_return - buy_hold_return),
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate_pct': float(win_rate),
                'avg_return_pct': float(np.mean([t['return_pct'] for t in trades]) * 100) if trades else 0,
                'best_trade_pct': float(max([t['return_pct'] for t in trades]) * 100) if trades else 0,
                'worst_trade_pct': float(min([t['return_pct'] for t in trades]) * 100) if trades else 0,
                'avg_hold_hours': float(np.mean([t['hold_hours'] for t in trades])) if trades else 0
            },
            'monthly_performance': monthly_performance,
            'trades': trades[:20],  # Solo primeros 20 trades para la web
            'total_trades_count': total_trades
        }
    
    def create_empty_result(self, crypto, year, df, initial_capital):
        """Crea resultado vacío cuando no hay trades"""
        crypto_config = self.crypto_configs[crypto]
        year_config = self.year_configs[year]
        
        start_price = df['open'].iloc[0]
        end_price = df['close'].iloc[-1]
        buy_hold_return = (end_price / start_price - 1) * 100
        
        return {
            'crypto': crypto,
            'year': year,
            'crypto_config': crypto_config,
            'year_config': year_config,
            'period': {
                'start': df.index[0].strftime('%Y-%m-%d'),
                'end': df.index[-1].strftime('%Y-%m-%d'),
                'total_candles': len(df)
            },
            'price_data': {
                'start_price': float(start_price),
                'end_price': float(end_price),
                'max_price': float(df['high'].max()),
                'min_price': float(df['low'].min()),
                'price_change_pct': float(buy_hold_return)
            },
            'trading_stats': {
                'initial_capital': float(initial_capital),
                'final_capital': float(initial_capital),
                'total_return_pct': 0.0,
                'buy_hold_return_pct': float(buy_hold_return),
                'outperformance_pct': float(-buy_hold_return),
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0.0,
                'avg_return_pct': 0.0,
                'best_trade_pct': 0.0,
                'worst_trade_pct': 0.0,
                'avg_hold_hours': 0.0
            },
            'monthly_performance': {},
            'trades': [],
            'total_trades_count': 0
        }
    
    def save_backtest_result(self, crypto, year, result):
        """Guarda resultado individual"""
        filename = f"backtest_{crypto}_{year}.json"
        filepath = os.path.join('src', 'backtest_results', filename)
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    
    def save_all_results(self, results):
        """Guarda todos los resultados en un archivo consolidado"""
        filepath = os.path.join('src', 'backtest_results', 'all_results.json')
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Todos los resultados guardados en: {filepath}")

def main():
    """Función principal"""
    print("🚀 GENERADOR AUTOMÁTICO DE BACKTESTS")
    print("="*60)
    print("📊 Generando backtests para:")
    print("   Criptos: BTC, ETH, BNB")
    print("   Años: 2022, 2023, 2024")
    print("   Total: 9 backtests")
    print("="*60)
    
    generator = BacktestGenerator()
    results = generator.generate_all_backtests()
    
    print("\n🎉 GENERACIÓN COMPLETADA!")
    print(f"📊 Resultados disponibles para visualización web")

if __name__ == "__main__":
    main()