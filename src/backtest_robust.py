# src/backtest_robust.py
# Sistema de backtesting robusto para validar patrones U

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from scanner_crypto import scan_crypto_for_u, CRYPTO_CONFIG
from scanner_stocks import scan_stocks_for_u
from binance_client import fetch_klines
import yfinance as yf
from utils import log

@dataclass
class BacktestResult:
    """Resultado de backtesting para un símbolo"""
    symbol: str
    scanner_type: str
    total_signals: int
    successful_signals: int
    win_rate: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_return: float
    avg_hold_days: float
    signals: List[Dict]
    equity_curve: List[float]
    stats: Dict

@dataclass  
class Trade:
    """Representa un trade individual"""
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    return_pct: float
    hold_days: int
    max_profit: float
    max_loss: float
    exit_reason: str

class RobustBacktester:
    def __init__(self):
        self.results = {}
        
    def backtest_crypto_symbol(self, symbol: str, timeframe: str = '4h', 
                             lookback_days: int = 365, verbose: bool = False) -> BacktestResult:
        """
        Backtesting robusto para criptomonedas usando datos de Binance
        """
        log(f"🔄 Iniciando backtesting robusto para {symbol} (crypto)...")
        
        try:
            # Obtener datos históricos más extensos
            limit = min(1000, lookback_days * (24 // int(timeframe.replace('h', ''))))
            klines = fetch_klines(symbol, timeframe, limit)
            
            if not klines or len(klines) < 100:
                return self._create_empty_result(symbol, "CRYPTO", "Datos insuficientes")
            
            df = pd.DataFrame(klines)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            log(f"[{symbol}] Datos obtenidos: {len(df)} velas desde {df.index[0]} hasta {df.index[-1]}")
            
            return self._run_walkforward_analysis(df, symbol, "CRYPTO", scan_crypto_for_u, verbose)
            
        except Exception as e:
            log(f"❌ Error en backtesting de {symbol}: {e}")
            return self._create_empty_result(symbol, "CRYPTO", f"Error: {str(e)}")
    
    def backtest_stock_symbol(self, symbol: str, lookback_years: int = 5, verbose: bool = False) -> BacktestResult:
        """
        Backtesting robusto para acciones usando Yahoo Finance
        """
        log(f"📈 Iniciando backtesting robusto para {symbol} (stock)...")
        
        try:
            start_date = (datetime.now() - timedelta(days=lookback_years * 365)).strftime('%Y-%m-%d')
            df = yf.download(symbol, start=start_date, interval="1mo", progress=False)
            
            if df.empty or len(df) < 24:  # Mínimo 2 años de datos
                return self._create_empty_result(symbol, "STOCK", "Datos insuficientes")
            
            df.dropna(inplace=True)
            log(f"[{symbol}] Datos obtenidos: {len(df)} velas mensuales desde {df.index[0]} hasta {df.index[-1]}")
            
            return self._run_walkforward_analysis(df, symbol, "STOCK", scan_stocks_for_u, verbose)
            
        except Exception as e:
            log(f"❌ Error en backtesting de {symbol}: {e}")
            return self._create_empty_result(symbol, "STOCK", f"Error: {str(e)}")
    
    def _run_walkforward_analysis(self, df: pd.DataFrame, symbol: str, scanner_type: str, 
                                scanner_func, verbose: bool = False) -> BacktestResult:
        """
        Análisis walk-forward: entrenar en ventana móvil, testear hacia adelante
        """
        signals = []
        trades = []
        equity_curve = [1000.0]  # Capital inicial
        current_capital = 1000.0
        
        # Configurar ventanas
        if scanner_type == "CRYPTO":
            train_window = 200  # 200 períodos para entrenamiento
            test_window = 50   # 50 períodos para testing
            profit_target = CRYPTO_CONFIG['PROFIT_TARGET']
            stop_loss = CRYPTO_CONFIG['STOP_LOSS']
            max_hold_periods = 100
        else:  # STOCK
            train_window = 60   # 60 meses para entrenamiento
            test_window = 12    # 12 meses para testing  
            profit_target = 0.10  # 10% para acciones
            stop_loss = 0.08     # 8% stop loss
            max_hold_periods = 24
        
        total_windows = (len(df) - train_window) // test_window
        log(f"[{symbol}] Ejecutando {total_windows} ventanas de walk-forward analysis")
        
        for window_idx in range(total_windows):
            start_idx = window_idx * test_window
            train_end_idx = start_idx + train_window
            test_end_idx = min(train_end_idx + test_window, len(df))
            
            if test_end_idx >= len(df) - 10:  # Necesitamos datos para forward testing
                break
            
            # Datos de entrenamiento (para detectar el patrón)
            train_df = df.iloc[start_idx:train_end_idx].copy()
            
            # Simular detección de patrón al final del período de entrenamiento
            window_signals = self._detect_signals_in_window(train_df, symbol, scanner_func, verbose)
            
            # Para cada señal, simular el trade en datos futuros (out-of-sample)
            for signal in window_signals:
                trade = self._simulate_trade(
                    df, signal, train_end_idx, test_end_idx, 
                    profit_target, stop_loss, max_hold_periods, scanner_type
                )
                
                if trade:
                    trades.append(trade)
                    current_capital *= (1 + trade.return_pct)
                    equity_curve.append(current_capital)
                    
                    signals.append({
                        'date': signal['date'].strftime('%Y-%m-%d'),
                        'entry_price': signal['entry_price'],
                        'exit_price': trade.exit_price,
                        'return_pct': trade.return_pct * 100,
                        'hold_days': trade.hold_days,
                        'exit_reason': trade.exit_reason,
                        'success': trade.return_pct > 0,
                        'max_profit': trade.max_profit * 100,
                        'max_drawdown': trade.max_loss * 100
                    })
        
        return self._compile_results(symbol, scanner_type, signals, trades, equity_curve)
    
    def _detect_signals_in_window(self, df: pd.DataFrame, symbol: str, scanner_func, verbose: bool) -> List[Dict]:
        """
        Detecta señales en una ventana de datos usando el scanner
        """
        signals = []
        
        # Crear ventanas deslizantes dentro del período de entrenamiento
        min_window_size = 50 if len(df) > 100 else len(df) // 2
        
        for i in range(min_window_size, len(df) - 10, 5):  # Cada 5 períodos
            window_df = df.iloc[:i].copy()
            
            try:
                # Para crypto, necesitamos simular el input que espera el scanner
                if 'CRYPTO' in scanner_func.__name__:
                    # Convertir DataFrame a formato que espera scanner_crypto
                    klines_format = []
                    for _, row in window_df.iterrows():
                        klines_format.append({
                            'timestamp': int(row.name.timestamp() * 1000),
                            'open': row['open'],
                            'high': row['high'], 
                            'low': row['low'],
                            'close': row['close'],
                            'volume': row['volume']
                        })
                    
                    # Monkey patch temporal para evitar API calls en backtesting
                    original_fetch = None
                    import scanner_crypto
                    if hasattr(scanner_crypto, 'fetch_klines'):
                        original_fetch = scanner_crypto.fetch_klines
                        scanner_crypto.fetch_klines = lambda *args: klines_format
                    
                    result = scanner_func(symbol, verbose=False)
                    
                    # Restaurar función original
                    if original_fetch:
                        scanner_crypto.fetch_klines = original_fetch
                else:
                    # Para stocks, usar el scanner directamente con datos históricos
                    # TODO: Implementar monkey patch para yfinance también
                    continue
                
                if result.get('alert') or result.get('estado_sugerido') in ['RUPTURA', 'U_DETECTADO']:
                    signals.append({
                        'date': df.index[i],
                        'entry_price': result.get('nivel_ruptura', df.iloc[i]['close']),
                        'signal_strength': abs(result.get('slope_left', 0)),
                        'pattern_type': result.get('estado_sugerido', 'UNKNOWN')
                    })
                    
            except Exception as e:
                if verbose:
                    log(f"Error en ventana {i}: {e}")
                continue
        
        return signals
    
    def _simulate_trade(self, df: pd.DataFrame, signal: Dict, start_idx: int, end_idx: int,
                       profit_target: float, stop_loss: float, max_hold: int, scanner_type: str) -> Trade:
        """
        Simula un trade basado en una señal
        """
        entry_price = signal['entry_price']
        entry_date = signal['date']
        
        # Buscar datos futuros para simular el trade
        future_data = df.iloc[start_idx:end_idx]
        if future_data.empty:
            return None
        
        target_price = entry_price * (1 + profit_target)
        stop_price = entry_price * (1 - stop_loss)
        
        max_profit = 0
        max_loss = 0
        
        for i, (date, row) in enumerate(future_data.iterrows()):
            if i > max_hold:  # Máximo tiempo de holding
                exit_price = row['close']
                exit_reason = "MAX_HOLD"
                break
            
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            # Tracking de máximos y mínimos
            current_profit = (high_price - entry_price) / entry_price
            current_loss = (entry_price - low_price) / entry_price
            max_profit = max(max_profit, current_profit)
            max_loss = max(max_loss, current_loss)
            
            # Verificar take profit
            if high_price >= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
                exit_date = date
                break
            
            # Verificar stop loss
            if low_price <= stop_price:
                exit_price = stop_price
                exit_reason = "STOP_LOSS" 
                exit_date = date
                break
                
            # Si es el último día, cerrar al precio de cierre
            if i == len(future_data) - 1:
                exit_price = close_price
                exit_reason = "END_OF_DATA"
                exit_date = date
                break
        else:
            return None  # No se pudo simular el trade
        
        return_pct = (exit_price - entry_price) / entry_price
        hold_days = (exit_date - entry_date).days
        
        return Trade(
            symbol=signal.get('symbol', ''),
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry_price,
            exit_price=exit_price,
            return_pct=return_pct,
            hold_days=hold_days,
            max_profit=max_profit,
            max_loss=max_loss,
            exit_reason=exit_reason
        )
    
    def _compile_results(self, symbol: str, scanner_type: str, signals: List[Dict], 
                        trades: List[Trade], equity_curve: List[float]) -> BacktestResult:
        """
        Compila todos los resultados en un objeto BacktestResult
        """
        if not trades:
            return self._create_empty_result(symbol, scanner_type, "No trades generados")
        
        # Calcular métricas
        total_signals = len(signals)
        successful_signals = len([t for t in trades if t.return_pct > 0])
        win_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0
        
        returns = [t.return_pct for t in trades]
        total_return = (equity_curve[-1] / equity_curve[0] - 1) * 100
        avg_trade_return = np.mean(returns) * 100
        avg_hold_days = np.mean([t.hold_days for t in trades])
        
        # Calcular máximo drawdown
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
        max_drawdown = max_dd * 100
        
        # Calcular Sharpe ratio (simplificado)
        if np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Anualizado
        else:
            sharpe_ratio = 0
        
        stats = {
            'best_trade': max(returns) * 100 if returns else 0,
            'worst_trade': min(returns) * 100 if returns else 0,
            'avg_winning_trade': np.mean([r for r in returns if r > 0]) * 100 if any(r > 0 for r in returns) else 0,
            'avg_losing_trade': np.mean([r for r in returns if r < 0]) * 100 if any(r < 0 for r in returns) else 0,
            'win_loss_ratio': abs(np.mean([r for r in returns if r > 0]) / np.mean([r for r in returns if r < 0])) if any(r < 0 for r in returns) else float('inf'),
            'total_trades': len(trades),
            'profitable_trades': successful_signals,
            'losing_trades': len(trades) - successful_signals
        }
        
        return BacktestResult(
            symbol=symbol,
            scanner_type=scanner_type,
            total_signals=total_signals,
            successful_signals=successful_signals,
            win_rate=win_rate,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            avg_trade_return=avg_trade_return,
            avg_hold_days=avg_hold_days,
            signals=signals,
            equity_curve=equity_curve,
            stats=stats
        )
    
    def _create_empty_result(self, symbol: str, scanner_type: str, reason: str) -> BacktestResult:
        """Crea un resultado vacío para casos de error"""
        return BacktestResult(
            symbol=symbol,
            scanner_type=scanner_type,
            total_signals=0,
            successful_signals=0,
            win_rate=0.0,
            total_return=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            avg_trade_return=0.0,
            avg_hold_days=0.0,
            signals=[],
            equity_curve=[1000.0],
            stats={'error': reason}
        )
    
    def run_portfolio_backtest(self, symbols: List[Tuple[str, str]], lookback_days: int = 365) -> Dict:
        """
        Ejecuta backtesting en múltiples símbolos y genera reporte de cartera
        """
        results = {}
        portfolio_equity = [1000.0]
        
        for symbol, asset_type in symbols:
            log(f"🔄 Backtesting {symbol} ({asset_type})...")
            
            if asset_type == 'crypto':
                result = self.backtest_crypto_symbol(symbol, lookback_days=lookback_days)
            else:
                result = self.backtest_stock_symbol(symbol, lookback_years=lookback_days//365)
            
            results[symbol] = result
        
        # Compilar métricas de cartera
        total_signals = sum(r.total_signals for r in results.values())
        successful_signals = sum(r.successful_signals for r in results.values())
        portfolio_win_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0
        
        return {
            'individual_results': results,
            'portfolio_stats': {
                'total_symbols': len(symbols),
                'total_signals': total_signals,
                'successful_signals': successful_signals,
                'portfolio_win_rate': portfolio_win_rate,
                'best_performer': max(results.items(), key=lambda x: x[1].total_return)[0] if results else None,
                'worst_performer': min(results.items(), key=lambda x: x[1].total_return)[0] if results else None
            }
        }

# Función de utilidad para generar reportes
def generate_backtest_report(result: BacktestResult, save_path: str = None) -> str:
    """Genera un reporte detallado del backtesting"""
    report = f"""
📊 REPORTE DE BACKTESTING ROBUSTO
{'='*50}

Símbolo: {result.symbol}
Tipo de Scanner: {result.scanner_type}
Período Analizado: {len(result.equity_curve)} puntos

📈 RENDIMIENTO:
• Total de Señales: {result.total_signals}
• Señales Exitosas: {result.successful_signals}
• Tasa de Éxito: {result.win_rate:.1f}%
• Retorno Total: {result.total_return:.2f}%
• Retorno Promedio por Trade: {result.avg_trade_return:.2f}%

⚠️  RIESGO:
• Máximo Drawdown: {result.max_drawdown:.2f}%
• Sharpe Ratio: {result.sharpe_ratio:.2f}
• Días Promedio de Holding: {result.avg_hold_days:.1f}

💡 ESTADÍSTICAS DETALLADAS:
• Mejor Trade: {result.stats.get('best_trade', 0):.2f}%
• Peor Trade: {result.stats.get('worst_trade', 0):.2f}%
• Ratio Win/Loss: {result.stats.get('win_loss_ratio', 0):.2f}
• Trades Rentables: {result.stats.get('profitable_trades', 0)}
• Trades Perdedores: {result.stats.get('losing_trades', 0)}

🎯 EVALUACIÓN:
Tasa de Éxito: {'🟢 EXCELENTE' if result.win_rate >= 70 else '🟡 BUENA' if result.win_rate >= 50 else '🔴 MEJORABLE'}
Sharpe Ratio: {'🟢 EXCELENTE' if result.sharpe_ratio >= 1.5 else '🟡 BUENA' if result.sharpe_ratio >= 0.8 else '🔴 MEJORABLE'}
Max Drawdown: {'🟢 BAJO' if result.max_drawdown <= 10 else '🟡 MODERADO' if result.max_drawdown <= 20 else '🔴 ALTO'}
"""
    
    if save_path:
        with open(save_path, 'w') as f:
            f.write(report)
    
    return report

if __name__ == "__main__":
    # Test del sistema
    bt = RobustBacktester()
    result = bt.backtest_crypto_symbol("BTCUSDT", lookback_days=180, verbose=True)
    print(generate_backtest_report(result))