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

# Import trading modules from trading_core

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
        from app.services.bitcoin_scanner_service import bitcoin_scanner
        
        # Obtener precio actual de Bitcoin directamente de Binance si el scanner falla
        current_price = 0
        try:
            import requests
            response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
            if response.status_code == 200:
                current_price = float(response.json()['price'])
        except:
            current_price = 0
        
        # Intentar obtener análisis del scanner (sin modificar el scanner)
        analysis_data = {}
        try:
            analysis_data = bitcoin_scanner.get_current_analysis()
        except Exception as scanner_error:
            logging.warning(f"Scanner analysis failed: {scanner_error}")
            analysis_data = {}
        
        # Usar datos del scanner si están disponibles, sino usar valores por defecto
        result_price = analysis_data.get('current_price', current_price)
        if result_price == 0:
            result_price = current_price
            
        # Calcular próximo escaneo
        next_scan_time = "Bot detenido"
        if bitcoin_scanner.is_running:
            try:
                # Obtener el último tiempo de escaneo y el intervalo
                last_scan = bitcoin_scanner.last_scan_time
                scan_interval = bitcoin_scanner.config.get('scan_interval', 300)  # 5 minutos por defecto
                
                if last_scan:
                    from datetime import timedelta
                    next_scan_datetime = last_scan + timedelta(seconds=scan_interval)
                    now = datetime.now()
                    
                    if next_scan_datetime > now:
                        # Calcular tiempo restante
                        remaining = next_scan_datetime - now
                        hours, remainder = divmod(remaining.total_seconds(), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        next_scan_time = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                    else:
                        next_scan_time = "Escaneando..."
                else:
                    next_scan_time = "Iniciando..."
            except Exception:
                next_scan_time = "00:05:00"  # Fallback a 5 minutos
        
        # Crear respuesta con los campos que necesita el frontend
        response_data = {
            "currentPrice": result_price,
            "ruptureLevel": analysis_data.get('nivel_ruptura'),
            "state": analysis_data.get('estado_sugerido', 'MONITORING'),
            "confidence": int(analysis_data.get('signal_strength', 0) * 10) if analysis_data.get('signal_strength') else 0,
            "atr": analysis_data.get('atr'),
            "signal_strength": analysis_data.get('signal_strength', 0),
            "isMonitoring": bitcoin_scanner.is_running,
            "timeUntilNextScan": next_scan_time,
            "lastUpdate": datetime.now().isoformat(),
            "details": {
                'slopeLeft': analysis_data.get('slope_left'),
                'patternWidth': analysis_data.get('pattern_width'),
                'depth': analysis_data.get('min_local_depth'),
                'description': analysis_data.get('pattern_description', 'Obteniendo datos...')
            }
        }
        
        return response_data
        
    except Exception as e:
        logging.error(f"Error getting current analysis: {str(e)}")
        # Return safe default analysis on error
        return {
            "currentPrice": 0,
            "ruptureLevel": None,
            "state": 'ERROR',
            "confidence": 0,
            "atr": None,
            "signal_strength": 0,
            "isMonitoring": False,
            "timeUntilNextScan": "Error",
            "lastUpdate": datetime.now().isoformat(),
            "details": {'error': str(e), 'description': 'Error obteniendo análisis'}
        }

@router.get("/bitcoin-bot/alerts")
async def get_bot_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene las alertas recientes del bot de Bitcoin desde la base de datos"""
    try:
        # Obtener alertas de Bitcoin de los últimos 7 días
        from datetime import datetime, timedelta
        from app.db import crud_alertas
        
        one_week_ago = datetime.now() - timedelta(days=7)
        alertas_btc = crud_alertas.get_alertas_by_crypto_since(
            db=db, 
            crypto_symbol='BTC', 
            since_date=one_week_ago,
            limit=50
        )
        
        # Convertir a formato que espera el frontend
        alerts = []
        for alerta in alertas_btc:
            # Formatear fecha y hora en UTC para usuarios internacionales
            fecha_utc = alerta.fecha_creacion.replace(tzinfo=None)
            fecha_formateada = fecha_utc.strftime('%d/%m/%Y %H:%M UTC')
            
            alerts.append({
                'id': alerta.id,
                'timestamp': alerta.fecha_creacion.isoformat(),
                'formatted_date': fecha_formateada,
                'date_day': fecha_utc.strftime('%d/%m/%Y'),
                'date_time': fecha_utc.strftime('%H:%M UTC'),
                'type': alerta.tipo_alerta,
                'symbol': alerta.ticker,
                'crypto_symbol': alerta.crypto_symbol,
                'message': alerta.mensaje,
                'rupture_level': alerta.nivel_ruptura,
                'entry_price': alerta.precio_entrada,
                'exit_price': alerta.precio_salida,
                'profit_usd': alerta.profit_usd,
                'profit_percentage': alerta.profit_percentage,
                'bot_mode': alerta.bot_mode,
                'read': alerta.leida
            })
        
        return alerts
        
    except Exception as e:
        logging.error(f"Error getting Bitcoin alerts from database: {str(e)}")
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
        from trading_core.binance_client import BinanceClient
        
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