# backend/app/api/v1/test_tools_routes.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_tickers
from app.core.auth import get_current_user
from app.schemas.user_schema import UserOut
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import asyncio
import threading
import time

# Agregar src al path para importar binance_backtest
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
sys.path.insert(0, src_path)

# Importación opcional para evitar errores al iniciar
binance_backtest_available = False
try:
    from binance_backtest import get_available_tickers, backtest_single_ticker
    binance_backtest_available = True
except ImportError as e:
    print(f"Warning: binance_backtest not available: {e}")
    # Funciones mock para evitar errores
    def get_available_tickers():
        return []
    
    def backtest_single_ticker(symbol, years_back):
        return {
            "symbol": symbol,
            "error": "Backtest module not available",
            "signals": [],
            "total_signals": 0,
            "successful_signals": 0,
            "success_rate": 0,
            "years_analyzed": years_back,
            "total_candles": 0
        }

router = APIRouter(prefix="/test-tools", tags=["test-tools"])

# Modelos Pydantic
class BacktestRequest(BaseModel):
    symbol: str
    years_back: int = 5

class BacktestResult(BaseModel):
    symbol: str
    error: Optional[str]
    signals: List[Dict[str, Any]]
    total_signals: int
    successful_signals: int
    success_rate: float
    years_analyzed: int
    total_candles: int

class TickerInfo(BaseModel):
    symbol: str
    name: Optional[str]
    type: str

# Almacenar resultados de backtest en memoria (en producción usar Redis o DB)
backtest_results = {}
backtest_status = {}

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

@router.post("/backtest/start", response_model=Dict[str, str])
def start_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user)
):
    """Inicia un backtest en segundo plano"""
    try:
        # Verificar si ya hay un backtest en progreso para este símbolo
        if request.symbol in backtest_status and backtest_status[request.symbol] == "running":
            raise HTTPException(
                status_code=400, 
                detail=f"Ya hay un backtest en progreso para {request.symbol}"
            )
        
        # Marcar como en progreso
        backtest_status[request.symbol] = "running"
        
        # Iniciar backtest en segundo plano
        background_tasks.add_task(
            run_backtest_task, 
            request.symbol, 
            request.years_back
        )
        
        return {
            "message": f"Backtest iniciado para {request.symbol}",
            "symbol": request.symbol,
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando backtest: {str(e)}")

@router.get("/backtest/status/{symbol}", response_model=Dict[str, str])
def get_backtest_status(
    symbol: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Obtiene el estado de un backtest"""
    status = backtest_status.get(symbol, "not_started")
    return {
        "symbol": symbol,
        "status": status
    }

@router.get("/backtest/result/{symbol}", response_model=BacktestResult)
def get_backtest_result(
    symbol: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Obtiene el resultado de un backtest"""
    if symbol not in backtest_results:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró resultado para {symbol}"
        )
    
    result = backtest_results[symbol]
    return BacktestResult(**result)

@router.get("/backtest/results", response_model=List[BacktestResult])
def get_all_backtest_results(
    current_user: UserOut = Depends(get_current_user)
):
    """Obtiene todos los resultados de backtest"""
    results = []
    for symbol, result in backtest_results.items():
        results.append(BacktestResult(**result))
    return results

@router.delete("/backtest/result/{symbol}")
def clear_backtest_result(
    symbol: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Elimina el resultado de un backtest"""
    if symbol in backtest_results:
        del backtest_results[symbol]
    if symbol in backtest_status:
        del backtest_status[symbol]
    
    return {"message": f"Resultado de {symbol} eliminado"}

async def run_backtest_task(symbol: str, years_back: int):
    """Ejecuta el backtest en segundo plano"""
    try:
        print(f"🚀 Iniciando backtest para {symbol} (últimos {years_back} años)")
        
        # Ejecutar backtest (función síncrona en hilo separado)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            backtest_single_ticker, 
            symbol, 
            years_back
        )
        
        # Guardar resultado
        backtest_results[symbol] = result
        backtest_status[symbol] = "completed"
        
        print(f"✅ Backtest completado para {symbol}")
        print(f"   Señales: {result['total_signals']}")
        print(f"   Éxito: {result['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error en backtest para {symbol}: {e}")
        backtest_results[symbol] = {
            "symbol": symbol,
            "error": str(e),
            "signals": [],
            "total_signals": 0,
            "successful_signals": 0,
            "success_rate": 0,
            "years_analyzed": years_back,
            "total_candles": 0
        }
        backtest_status[symbol] = "error"

@router.get("/health")
def health_check():
    """Verifica que el servicio esté funcionando"""
    return {"status": "ok", "message": "Test tools service is running"}
