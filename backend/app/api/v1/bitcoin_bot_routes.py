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
        user_id = current_user.id
        
        # Check if bot is already running for this user
        if user_id in bot_sessions and bot_sessions[user_id].get('isRunning'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El bot ya está ejecutándose para este usuario"
            )
        
        # Initialize bot session
        bot_sessions[user_id] = {
            'isRunning': True,
            'mode': request.mode,
            'config': request.config.dict(),
            'startTime': datetime.now(),
            'lastCheck': datetime.now().isoformat(),
            'alerts': [],
            'statistics': {
                'totalAlerts': 0,
                'buySignals': 0,
                'sellSignals': 0,
                'accuracy': 0,
                'portfolio': {
                    'balance': 1000.0,  # Default testnet balance
                    'btc': 0.0,
                    'pnl': 0.0
                } if request.mode == 'automatic' else None
            }
        }
        
        # Start the appropriate bot mode
        if request.mode == 'manual':
            # Start manual mode (public API alerts only)
            await start_manual_mode(user_id, request.config)
        else:
            # Start automatic mode (testnet trading)
            if not request.config.apiKey or not request.config.secretKey:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API credentials are required for automatic mode"
                )
            await start_automatic_mode(user_id, request.config)
        
        return {
            "success": True,
            "message": f"Bitcoin Bot iniciado en modo {request.mode}",
            "mode": request.mode,
            "startTime": bot_sessions[user_id]['startTime'].isoformat()
        }
        
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
        user_id = current_user.id
        
        if user_id not in bot_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay sesión activa del bot para este usuario"
            )
        
        # Stop bot session
        bot_sessions[user_id]['isRunning'] = False
        bot_sessions[user_id]['stopTime'] = datetime.now()
        
        return {
            "success": True,
            "message": "Bitcoin Bot detenido exitosamente"
        }
        
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
        user_id = current_user.id
        
        if user_id not in bot_sessions:
            return {
                "isRunning": False,
                "lastCheck": None,
                "mode": None
            }
        
        session = bot_sessions[user_id]
        return {
            "isRunning": session.get('isRunning', False),
            "lastCheck": session.get('lastCheck'),
            "mode": session.get('mode'),
            "startTime": session.get('startTime', datetime.now()).isoformat() if session.get('startTime') else None
        }
        
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
        
        # Import and run the scanner
        from binance_client import fetch_current_price
        from scanner_crypto import scan_crypto_for_u
        
        # Get current Bitcoin analysis
        result = scan_crypto_for_u('BTCUSDT', verbose=False)
        current_price = fetch_current_price('BTCUSDT')
        
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

async def start_manual_mode(user_id: int, config: BotConfig):
    """Inicia el modo manual (solo alertas)"""
    # In production, this would start a background task
    # For now, we just mark it as running
    pass

async def start_automatic_mode(user_id: int, config: BotConfig):
    """Inicia el modo automático (trading en testnet)"""
    # In production, this would start a background trading task
    # For now, we just mark it as running
    pass