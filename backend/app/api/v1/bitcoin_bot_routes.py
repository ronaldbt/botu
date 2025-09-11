# backend/app/api/v1/bitcoin_bot_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
import json
import logging
from datetime import datetime

# Add src path for importing trading modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User
from app.services.bitcoin_scanner_service import bitcoin_scanner

router = APIRouter()

# Global bot status storage (in production, use Redis or database)
bot_sessions = {}

# Pydantic models
class BotConfig(BaseModel):
    timeframe: str = '4h'
    takeProfit: float = 12.0
    stopLoss: float = 5.0
    tradeAmount: float = 50.0
    maxConcurrentTrades: int = 1
    environment: str = 'testnet'
    apiKey: Optional[str] = None
    secretKey: Optional[str] = None

class StartBotRequest(BaseModel):
    mode: str  # 'manual' or 'automatic'
    config: BotConfig

class TestApiRequest(BaseModel):
    apiKey: str
    secretKey: str
    environment: str = 'testnet'

class BotAlert(BaseModel):
    id: str
    type: str  # BUY, SELL, INFO, WARNING
    title: str
    message: str
    price: Optional[float] = None
    quantity: Optional[float] = None
    timestamp: datetime

class CurrentAnalysis(BaseModel):
    currentPrice: Optional[float] = None
    ruptureLevel: Optional[float] = None
    state: Optional[str] = None
    confidence: Optional[int] = None
    lastUpdate: datetime
    details: Optional[Dict[str, Any]] = None

class BotStatistics(BaseModel):
    totalAlerts: int = 0
    buySignals: int = 0
    sellSignals: int = 0
    accuracy: int = 0
    portfolio: Optional[Dict[str, Any]] = None

@router.post("/bitcoin-bot/start")
async def start_bitcoin_bot(
    request: StartBotRequest,
    current_user: User = Depends(get_current_user)
):
    """Inicia el Bitcoin Bot en el modo especificado"""
    try:
        # Solo ADMIN puede iniciar el bot
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden iniciar el Bitcoin Bot"
            )
        
        # Verificar si el scanner ya está corriendo
        if bitcoin_scanner.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El Bitcoin Bot ya está ejecutándose"
            )
        
        # Configurar scanner con parámetros del admin
        scanner_config = {
            "profit_target": request.config.takeProfit / 100.0,  # Convertir porcentaje
            "stop_loss": request.config.stopLoss / 100.0,
            "timeframe": request.config.timeframe,
        }
        bitcoin_scanner.update_config(scanner_config)
        
        # Iniciar scanner automático
        success = await bitcoin_scanner.start_scanning()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error iniciando el scanner automático"
            )
        
        # Actualizar sesión global
        bot_sessions['global'] = {
            'isRunning': True,
            'mode': request.mode,
            'config': request.config.dict(),
            'startTime': datetime.now(),
            'admin_user': current_user.username,
            'scanner_status': bitcoin_scanner.get_status()
        }
        
        return {
            "success": True,
            "message": f"Bitcoin Bot iniciado en modo {request.mode} - Scanner automático cada 4 horas",
            "mode": request.mode,
            "startTime": datetime.now().isoformat(),
            "next_scan": "En 4 horas y 5 minutos"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error starting Bitcoin Bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error iniciando Bitcoin Bot: {str(e)}"
        )

@router.post("/bitcoin-bot/stop")
async def stop_bitcoin_bot(current_user: User = Depends(get_current_user)):
    """Detiene el Bitcoin Bot"""
    try:
        # Solo ADMIN puede detener el bot
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden detener el Bitcoin Bot"
            )
        
        if not bitcoin_scanner.is_running:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El Bitcoin Bot no está ejecutándose"
            )
        
        # Detener scanner automático
        success = await bitcoin_scanner.stop_scanning()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deteniendo el scanner automático"
            )
        
        # Actualizar sesión global
        if 'global' in bot_sessions:
            bot_sessions['global']['isRunning'] = False
            bot_sessions['global']['stopTime'] = datetime.now()
        
        return {
            "success": True,
            "message": "Bitcoin Bot detenido exitosamente",
            "stopped_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error stopping Bitcoin Bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deteniendo Bitcoin Bot: {str(e)}"
        )

@router.get("/bitcoin-bot/status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """Obtiene el estado actual del Bitcoin Bot"""
    try:
        scanner_status = bitcoin_scanner.get_status()
        
        # Estado base para todos los usuarios
        status = {
            "isRunning": scanner_status['is_running'],
            "lastCheck": scanner_status['last_scan_time'],
            "mode": "manual",
            "alerts_count": scanner_status['alerts_count']
        }
        
        # Información adicional para admin
        if current_user.is_admin:
            global_session = bot_sessions.get('global', {})
            status.update({
                "admin_controls": True,
                "startTime": global_session.get('startTime', datetime.now()).isoformat() if global_session.get('startTime') else None,
                "admin_user": global_session.get('admin_user'),
                "scanner_config": scanner_status['config'],
                "next_scan_in_seconds": scanner_status['next_scan_in_seconds']
            })
        else:
            status.update({
                "admin_controls": False,
                "message": "Solo el administrador puede controlar el Bitcoin Bot"
            })
        
        return status
        
    except Exception as e:
        logging.error(f"Error getting bot status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado: {str(e)}"
        )

@router.get("/bitcoin-bot/analysis")
async def get_current_analysis(current_user: User = Depends(get_current_user)):
    """Obtiene el análisis actual de Bitcoin"""
    try:
        user_id = current_user.id
        
        # Usar el scanner nuevo optimizado del 2023
        from app.services.bitcoin_scanner_service import bitcoin_scanner
        
        # Get current Bitcoin analysis usando el scanner optimizado
        result = bitcoin_scanner.get_current_analysis()
        current_price = result.get('current_price', 0)
        
        analysis = CurrentAnalysis(
            currentPrice=current_price,
            ruptureLevel=result.get('nivel_ruptura'),
            state=result.get('estado_sugerido', 'BASE'),
            confidence=int(result.get('signal_strength', 0) * 100) if result.get('signal_strength') else 0,
            lastUpdate=datetime.now(),
            details={
                'slopeLeft': result.get('slope_left'),
                'patternWidth': result.get('pattern_width'),
                'alert': result.get('alert', False)
            }
        )
        
        return analysis.dict()
        
    except Exception as e:
        logging.error(f"Error getting current analysis: {str(e)}")
        # Return default analysis on error
        return CurrentAnalysis(
            currentPrice=None,
            ruptureLevel=None,
            state='ERROR',
            confidence=0,
            lastUpdate=datetime.now(),
            details={'error': str(e)}
        ).dict()

@router.get("/bitcoin-bot/alerts")
async def get_bot_alerts(current_user: User = Depends(get_current_user)):
    """Obtiene las alertas recientes del bot"""
    try:
        user_id = current_user.id
        
        if user_id not in bot_sessions:
            return []
        
        return bot_sessions[user_id].get('alerts', [])
        
    except Exception as e:
        logging.error(f"Error getting alerts: {str(e)}")
        return []

@router.get("/bitcoin-bot/statistics")
async def get_bot_statistics(current_user: User = Depends(get_current_user)):
    """Obtiene las estadísticas del bot"""
    try:
        user_id = current_user.id
        
        if user_id not in bot_sessions:
            return BotStatistics().dict()
        
        return bot_sessions[user_id].get('statistics', BotStatistics().dict())
        
    except Exception as e:
        logging.error(f"Error getting statistics: {str(e)}")
        return BotStatistics().dict()

@router.post("/bitcoin-bot/test-api")
async def test_binance_api(
    request: TestApiRequest,
    current_user: User = Depends(get_current_user)
):
    """Prueba la conexión con la API de Binance"""
    try:
        from binance_client import BinanceClient
        
        # Test API connection
        client = BinanceClient(
            api_key=request.apiKey,
            secret_key=request.secretKey,
            testnet=(request.environment == 'testnet')
        )
        
        # Try to get account info
        account_info = client.get_account_info()
        
        if account_info:
            balance_info = ""
            if 'balances' in account_info:
                usdt_balance = next((b for b in account_info['balances'] if b['asset'] == 'USDT'), None)
                btc_balance = next((b for b in account_info['balances'] if b['asset'] == 'BTC'), None)
                
                if usdt_balance:
                    balance_info += f"USDT: {float(usdt_balance['free']):.2f} "
                if btc_balance:
                    balance_info += f"BTC: {float(btc_balance['free']):.6f}"
            
            return {
                "success": True,
                "accountInfo": balance_info or "Cuenta verificada"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo obtener información de la cuenta"
            }
            
    except Exception as e:
        logging.error(f"Error testing Binance API: {str(e)}")
        return {
            "success": False,
            "error": f"Error de conexión: {str(e)}"
        }

@router.get("/bitcoin-bot/logs")
async def get_scanner_logs(current_user: User = Depends(get_current_user)):
    """Obtiene los logs del scanner en tiempo real"""
    try:
        scanner_status = bitcoin_scanner.get_status()
        return {
            "logs": scanner_status.get('logs', []),
            "is_running": scanner_status['is_running'],
            "last_scan_time": scanner_status['last_scan_time'],
            "alerts_count": scanner_status['alerts_count'],
            "cooldown_remaining": scanner_status.get('cooldown_remaining')
        }
        
    except Exception as e:
        logging.error(f"Error getting scanner logs: {str(e)}")
        return {
            "logs": [],
            "is_running": False,
            "error": str(e)
        }

# Las funciones de inicio son manejadas directamente por el scanner automático
# No se necesitan funciones separadas ya que el scanner es global y administrado por admin