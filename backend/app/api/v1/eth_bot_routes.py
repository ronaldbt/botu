# backend/app/api/v1/eth_bot_routes.py

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
from app.services.eth_scanner_service import eth_scanner

router = APIRouter()

# Global bot status storage (in production, use Redis or database)
eth_bot_sessions = {}

# Pydantic models
class BotConfig(BaseModel):
    timeframe: str = '4h'
    takeProfit: float = 12.0
    stopLoss: float = 5.0
    tradeAmount: float = 50.0
    maxConcurrentTrades: int = 1
    environment: str = 'testnet'
    symbol: str = 'ETHUSDT'
    apiKey: Optional[str] = None
    secretKey: Optional[str] = None

class StartBotRequest(BaseModel):
    mode: str  # 'manual' or 'automatic'
    config: BotConfig

class CurrentAnalysis(BaseModel):
    currentPrice: Optional[float] = None
    ruptureLevel: Optional[float] = None
    state: Optional[str] = None
    confidence: Optional[int] = None
    lastUpdate: datetime
    details: Optional[Dict[str, Any]] = None

@router.post("/eth-bot/start")
async def start_eth_bot(
    request: StartBotRequest,
    current_user: User = Depends(get_current_user)
):
    """Inicia el Ethereum Bot en el modo especificado"""
    try:
        # Solo ADMIN puede iniciar el bot
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden iniciar el Ethereum Bot"
            )
        
        # Verificar si el scanner ya está corriendo
        if eth_scanner.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El Ethereum Bot ya está ejecutándose"
            )
        
        # Configurar scanner con parámetros del admin
        scanner_config = {
            "profit_target": request.config.takeProfit / 100.0,  # Convertir porcentaje
            "stop_loss": request.config.stopLoss / 100.0,
            "timeframe": request.config.timeframe,
        }
        eth_scanner.update_config(scanner_config)
        
        # Iniciar scanner automático
        success = await eth_scanner.start_scanning()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error iniciando el scanner automático ETH"
            )
        
        # Actualizar sesión global
        eth_bot_sessions['global'] = {
            'isRunning': True,
            'mode': request.mode,
            'config': request.config.dict(),
            'startTime': datetime.now(),
            'admin_user': current_user.username,
            'scanner_status': eth_scanner.get_status()
        }
        
        return {
            "success": True,
            "message": f"Ethereum Bot iniciado en modo {request.mode} - Scanner automático cada 4 horas",
            "mode": request.mode,
            "startTime": datetime.now().isoformat(),
            "next_scan": "En 4 horas y 5 minutos"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error starting Ethereum Bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error iniciando Ethereum Bot: {str(e)}"
        )

@router.post("/eth-bot/stop")
async def stop_eth_bot(current_user: User = Depends(get_current_user)):
    """Detiene el Ethereum Bot"""
    try:
        # Solo ADMIN puede detener el bot
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden detener el Ethereum Bot"
            )
        
        if not eth_scanner.is_running:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El Ethereum Bot no está ejecutándose"
            )
        
        # Detener scanner automático
        success = await eth_scanner.stop_scanning()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deteniendo el scanner automático ETH"
            )
        
        # Actualizar sesión global
        if 'global' in eth_bot_sessions:
            eth_bot_sessions['global']['isRunning'] = False
            eth_bot_sessions['global']['stopTime'] = datetime.now()
        
        return {
            "success": True,
            "message": "Ethereum Bot detenido exitosamente",
            "stopped_by": current_user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error stopping Ethereum Bot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deteniendo Ethereum Bot: {str(e)}"
        )

@router.get("/eth-bot/status")
async def get_eth_bot_status(current_user: User = Depends(get_current_user)):
    """Obtiene el estado actual del Ethereum Bot"""
    try:
        scanner_status = eth_scanner.get_status()
        global_session = eth_bot_sessions.get('global', {})
        
        # Estado base para todos los usuarios
        status = {
            "isRunning": scanner_status['is_running'],
            "lastCheck": scanner_status['last_scan_time'],
            "mode": global_session.get('mode', 'manual'),
            "alerts_count": scanner_status['alerts_count']
        }
        
        # Información adicional para admin
        if current_user.is_admin:
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
                "message": "Solo el administrador puede controlar el Ethereum Bot"
            })
        
        return status
        
    except Exception as e:
        logging.error(f"Error getting ETH bot status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estado: {str(e)}"
        )

@router.get("/eth-bot/analysis")
async def get_current_eth_analysis(current_user: User = Depends(get_current_user)):
    """Obtiene el análisis actual de Ethereum"""
    try:
        # Usar el scanner nuevo optimizado del 2023 para Ethereum
        from app.services.eth_scanner_service import eth_scanner
        
        # Get current Ethereum analysis usando el scanner optimizado
        result = eth_scanner.get_current_analysis()
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
        logging.error(f"Error getting current ETH analysis: {str(e)}")
        # Return default analysis on error
        return CurrentAnalysis(
            currentPrice=None,
            ruptureLevel=None,
            state='ERROR',
            confidence=0,
            lastUpdate=datetime.now(),
            details={'error': str(e)}
        ).dict()

@router.get("/eth-bot/logs")
async def get_eth_scanner_logs(current_user: User = Depends(get_current_user)):
    """Obtiene los logs del scanner de Ethereum en tiempo real"""
    try:
        scanner_status = eth_scanner.get_status()
        return {
            "logs": scanner_status.get('logs', []),
            "is_running": scanner_status['is_running'],
            "last_scan_time": scanner_status['last_scan_time'],
            "alerts_count": scanner_status['alerts_count'],
            "cooldown_remaining": scanner_status.get('cooldown_remaining')
        }
        
    except Exception as e:
        logging.error(f"Error getting ETH scanner logs: {str(e)}")
        return {
            "logs": [],
            "is_running": False,
            "error": str(e)
        }

@router.get("/eth-bot/alerts")
async def get_eth_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene las alertas recientes del bot de Ethereum desde la base de datos"""
    try:
        # Obtener alertas de Ethereum de los últimos 7 días
        from datetime import datetime, timedelta
        from app.db import crud_alertas
        
        one_week_ago = datetime.now() - timedelta(days=7)
        alertas_eth = crud_alertas.get_alertas_by_crypto_since(
            db=db, 
            crypto_symbol='ETH', 
            since_date=one_week_ago,
            limit=50
        )
        
        # Convertir a formato que espera el frontend
        alerts = []
        for alerta in alertas_eth:
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
        logging.error(f"Error getting Ethereum alerts from database: {str(e)}")
        return []