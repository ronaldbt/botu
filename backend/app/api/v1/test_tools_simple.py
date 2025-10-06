# backend/app/api/v1/test_tools_simple.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_tickers
from app.core.auth import get_current_user
from app.schemas.auth_schema import UserOut
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import sys
import os
import logging
from datetime import datetime

router = APIRouter(prefix="/test-tools", tags=["test-tools"])

# Add src path for importing backtest modules
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Global backtest status storage
backtest_status: Dict[str, Any] = {
    "is_running": False,
    "current_symbol": "",
    "progress": 0,
    "total_symbols": 0,
    "results": [],
    "start_time": None,
    "error": None,
    "completed": False
}

# Modelos Pydantic
class TickerInfo(BaseModel):
    symbol: str
    name: Optional[str]
    type: str

class BacktestRequest(BaseModel):
    symbol: str  # Una sola criptomoneda
    years_back: int = 1  # Por defecto 1 año
    
class BacktestStatus(BaseModel):
    is_running: bool
    current_symbol: Optional[str] = None
    progress: int = 0
    total_symbols: int = 0
    results: List[Dict[str, Any]] = []
    start_time: Optional[str] = None
    error: Optional[str] = None
    completed: bool = False

@router.get("/tickers", response_model=List[TickerInfo])
def get_available_tickers_for_test(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista de tickers disponibles para backtest"""
    try:
        tickers_db = crud_tickers.get_all_tickers(db)
        crypto_tickers = [
            TickerInfo(
                symbol=t.ticker,
                name=t.nombre or t.ticker,
                type=t.tipo
            ) 
            for t in tickers_db if t.tipo == 'crypto' and t.activo
        ]
        print(f"Found {len(crypto_tickers)} crypto tickers")
        return crypto_tickers
    except Exception as e:
        print(f"Error getting tickers: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tickers: {str(e)}")

@router.get("/health")
def health_check():
    """Verifica que el servicio esté funcionando"""
    return {"status": "ok", "message": "Test tools service is running"}

async def run_backtest_async(symbol: str, years_back: int):
    """Ejecuta el backtest de forma asíncrona"""
    global backtest_status
    
    try:
        # TODO: Actualizar para usar scanners optimizados 2023
        # from binance_client import get_spot_client, fetch_klines
        # from binance_scanner_u import scan_for_u_binance
        import pandas as pd
        
        # Por ahora retornamos un resultado de prueba
        backtest_status["error"] = "Herramientas de testing temporalmente deshabilitadas - usando scanners optimizados 2023"
        return
        
        backtest_status["is_running"] = True
        backtest_status["completed"] = False
        backtest_status["error"] = None
        backtest_status["progress"] = 0
        backtest_status["total_symbols"] = 1  # Solo una criptomoneda
        backtest_status["results"] = []
        backtest_status["start_time"] = datetime.now().isoformat()
        
        logging.info(f"🔍 Iniciando análisis de {symbol}")
        
        try:
            # Obtener datos históricos de Binance
            client = get_spot_client()
            
            # Calcular fechas
            from datetime import timedelta
            end_time = datetime.now()
            start_time = end_time - timedelta(days=years_back * 365)
            
            start_str = start_time.strftime('%Y-%m-%d')
            end_str = end_time.strftime('%Y-%m-%d')
            
            logging.info(f"[{symbol}] Obteniendo datos desde {start_str} hasta {end_str}")
            backtest_status["current_symbol"] = f"📥 {symbol} - Conectando con Binance..."
            backtest_status["progress"] = 5
            await asyncio.sleep(0.1)
            
            # Obtener datos históricos (1 día de intervalo)
            # Calcular límite aproximado para el período solicitado
            limit = min(1000, years_back * 365 + 50)  # Máximo 1000 velas
            backtest_status["current_symbol"] = f"📈 {symbol} - Descargando {limit} velas históricas..."
            backtest_status["progress"] = 10
            
            klines = fetch_klines(symbol, '1d', limit)
            
            if not klines:
                result = {
                    "symbol": symbol,
                    "error": "No se pudieron obtener datos históricos",
                    "signals": [],
                    "total_signals": 0,
                    "success_rate": 0,
                    "years_analyzed": years_back,
                    "data_points": 0
                }
                backtest_status["results"] = [result]
                backtest_status["error"] = "❌ No se pudieron obtener datos históricos"
                backtest_status["progress"] = 100
            else:
                # Convertir a DataFrame
                backtest_status["current_symbol"] = f"🔄 {symbol} - Procesando datos históricos..."
                backtest_status["progress"] = 20
                await asyncio.sleep(0.1)
                
                df = pd.DataFrame(klines)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                logging.info(f"[{symbol}] Analizando {len(df)} velas históricas")
                backtest_status["current_symbol"] = f"🧠 {symbol} - Analizando {len(df)} velas de datos..."
                backtest_status["progress"] = 25
                
                # Analizar patrones U con progreso
                signals = []
                window_size = min(200, len(df) // 2)  # Ventana más pequeña
                step_size = 20  # Pasos más pequeños
                
                if window_size < 100:
                    window_size = min(100, len(df) - 1)
                    step_size = max(1, window_size // 10)
                
                total_windows = max(1, (len(df) - window_size) // step_size)
                
                logging.info(f"[{symbol}] Procesando {total_windows} ventanas de análisis")
                backtest_status["current_symbol"] = f"🔍 {symbol} - Configurando análisis de patrones U..."
                backtest_status["progress"] = 30
                await asyncio.sleep(0.1)
                
                for window_idx in range(0, len(df) - window_size, step_size):
                    if not backtest_status["is_running"]:
                        break
                        
                    # Actualizar progreso (rango de 30% a 90%)
                    window_progress = (window_idx // step_size) / total_windows
                    progress_pct = 30 + (window_progress * 60)  # 30% a 90%
                    backtest_status["progress"] = int(progress_pct)
                    backtest_status["current_symbol"] = f"🎯 {symbol} - Buscando patrones U ({progress_pct:.0f}%)"
                    
                    # Obtener ventana de datos
                    window_data = df.iloc[window_idx:window_idx + window_size].copy()
                    
                    if len(window_data) < 50:  # Mínimo reducido
                        continue
                    
                    try:
                        # Convertir a formato para scan_for_u_binance
                        klines_format = []
                        for _, row in window_data.iterrows():
                            klines_format.append([
                                int(row['timestamp'].timestamp() * 1000),
                                float(row['open']),
                                float(row['high']), 
                                float(row['low']),
                                float(row['close']),
                                float(row['volume']),
                                int(row['timestamp'].timestamp() * 1000),
                                0, 0, 0, 0, '0'
                            ])
                        
                        # Analizar patrón U
                        scan_result = scan_for_u_binance(symbol, klines_format, verbose=False)
                        
                        if scan_result.get('alert') and scan_result.get('estado_sugerido') == 'U_ROTO':
                            # Verificar éxito de la señal
                            current_price = scan_result.get('precio_confirmacion', 0)
                            rupture_level = scan_result.get('nivel_ruptura', 0)
                            
                            # Evaluar rendimiento futuro (próximas 20 velas)
                            future_start = window_idx + window_size
                            future_end = min(len(df), future_start + 20)
                            
                            max_future_price = current_price  # Default
                            if future_end > future_start:
                                future_data = df.iloc[future_start:future_end]
                                max_future_price = future_data['high'].max()
                            
                            success = bool(max_future_price > current_price * 1.01)  # 1% mínimo
                            profit_potential = ((max_future_price - current_price) / current_price) * 100
                            
                            signal = {
                                "date": window_data.iloc[-1]['timestamp'].strftime('%Y-%m-%d'),
                                "timestamp": window_data.iloc[-1]['timestamp'].isoformat(),
                                "rupture_level": float(rupture_level),
                                "current_price": float(current_price),
                                "slope_left": float(scan_result.get('slope_left', 0)),
                                "max_future_price": float(max_future_price),
                                "success": success,
                                "profit_potential": round(profit_potential, 2)
                            }
                            signals.append(signal)
                            
                            # Actualizar progreso cuando se encuentra una señal
                            signal_count = len(signals)
                            backtest_status["current_symbol"] = f"✅ {symbol} - Encontrada señal #{signal_count} ({signal['date']})"
                            
                            logging.info(f"[{symbol}] 🎯 Señal U detectada: {signal['date']} - "
                                       f"Ruptura: {rupture_level:.4f}, "
                                       f"Ganancia: {profit_potential:.1f}%")
                    
                    except Exception as scan_error:
                        logging.warning(f"[{symbol}] Error en análisis: {str(scan_error)[:100]}")
                        continue
                    
                    # Pequeña pausa para permitir actualizaciones
                    await asyncio.sleep(0.05)
                
                # Calcular estadísticas finales
                backtest_status["current_symbol"] = f"📊 {symbol} - Calculando estadísticas finales..."
                backtest_status["progress"] = 95
                await asyncio.sleep(0.1)
                
                total_signals = len(signals)
                successful_signals = sum(1 for s in signals if s['success'])
                success_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0
                
                result = {
                    "symbol": symbol,
                    "signals": signals,
                    "total_signals": total_signals,
                    "successful_signals": successful_signals,
                    "success_rate": round(success_rate, 1),
                    "years_analyzed": years_back,
                    "data_points": len(df),
                    "windows_analyzed": total_windows
                }
                
                backtest_status["results"] = [result]
                backtest_status["current_symbol"] = f"🎉 {symbol} - Completado: {total_signals} señales encontradas"
                
                logging.info(f"[{symbol}] ✅ Análisis completado: {total_signals} señales, "
                           f"{success_rate:.1f}% tasa de éxito")
        
        except Exception as symbol_error:
            result = {
                "symbol": symbol,
                "error": str(symbol_error),
                "signals": [],
                "total_signals": 0,
                "success_rate": 0,
                "years_analyzed": years_back
            }
            backtest_status["results"] = [result]
            backtest_status["error"] = str(symbol_error)
            logging.error(f"[{symbol}] Error en análisis: {symbol_error}")
        
        # Finalizar
        backtest_status["progress"] = 100
        backtest_status["current_symbol"] = ""
        backtest_status["completed"] = True
        backtest_status["is_running"] = False
        
        logging.info("✅ Backtest completado")
        
    except Exception as e:
        backtest_status["error"] = str(e)
        backtest_status["is_running"] = False
        backtest_status["completed"] = True
        logging.error(f"Error in backtest: {e}")

@router.post("/backtest/start")
async def start_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user)
):
    """Inicia un backtest para los símbolos especificados"""
    global backtest_status
    
    if backtest_status["is_running"]:
        raise HTTPException(status_code=409, detail="Ya hay un backtest en ejecución")
    
    if not request.symbol:
        raise HTTPException(status_code=400, detail="Debe especificar un símbolo")
    
    # Reset status
    backtest_status = {
        "is_running": True,
        "current_symbol": request.symbol,
        "progress": 0,
        "total_symbols": 1,
        "results": [],
        "start_time": datetime.now().isoformat(),
        "error": None,
        "completed": False
    }
    
    # Start background task
    background_tasks.add_task(run_backtest_async, request.symbol, request.years_back)
    
    return {
        "message": f"Backtest iniciado para {request.symbol}",
        "symbol": request.symbol,
        "years_back": request.years_back,
        "status": backtest_status
    }

@router.get("/backtest/status", response_model=BacktestStatus)
def get_backtest_status(current_user: UserOut = Depends(get_current_user)):
    """Obtiene el estado actual del backtest"""
    return BacktestStatus(**backtest_status)

@router.post("/backtest/stop")
def stop_backtest(current_user: UserOut = Depends(get_current_user)):
    """Detiene el backtest en ejecución"""
    global backtest_status
    
    if not backtest_status["is_running"]:
        raise HTTPException(status_code=400, detail="No hay backtest en ejecución")
    
    backtest_status["is_running"] = False
    backtest_status["completed"] = True
    backtest_status["current_symbol"] = ""
    
    return {"message": "Backtest detenido"}

@router.delete("/backtest/results")
def clear_backtest_results(current_user: UserOut = Depends(get_current_user)):
    """Limpia los resultados del backtest"""
    global backtest_status
    
    backtest_status["results"] = []
    backtest_status["completed"] = False
    backtest_status["error"] = None
    
    return {"message": "Resultados del backtest limpiados"}
