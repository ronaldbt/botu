# backend/app/api/v1/paxg_4h_mainnet_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import User
from app.core.auth import get_current_user
from app.services.paxg_scanner_service import paxg_scanner
from app.services.auto_trading_paxg4h_executor import AutoTradingPaxg4hExecutor
from app.db.models import TradingOrder
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/trading/scanner/paxg-4h-mainnet", tags=["paxg-4h-mainnet-scanner"])

# Instanciar ejecutor específico
paxg_4h_executor = AutoTradingPaxg4hExecutor()

# --------------------------
# Control del Scanner PAXG 4h Mainnet
# --------------------------

@router.post("/start")
async def start_paxg_4h_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicia el scanner de PAXG 4h para Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) iniciando scanner PAXG 4h Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        if paxg_scanner.is_running:
            return {
                "success": False,
                "message": "El scanner PAXG 4h Mainnet ya está ejecutándose",
                "status": paxg_scanner.get_status()
            }
        
        # Iniciar scanner
        import asyncio
        asyncio.create_task(paxg_scanner.start_scanner())
        
        logger.info("✅ Scanner PAXG 4h Mainnet iniciado exitosamente")
        return {
            "success": True,
            "message": "Scanner PAXG 4h Mainnet iniciado exitosamente",
            "status": paxg_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error iniciando scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando scanner: {str(e)}")

@router.post("/stop")
async def stop_paxg_4h_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detiene el scanner de PAXG 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) deteniendo scanner PAXG 4h Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        await paxg_scanner.stop_scanner()
        
        logger.info("⏹️ Scanner PAXG 4h Mainnet detenido exitosamente")
        return {
            "success": True,
            "message": "Scanner PAXG 4h Mainnet detenido exitosamente",
            "status": paxg_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error deteniendo scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error deteniendo scanner: {str(e)}")

@router.get("/status")
async def get_paxg_4h_scanner_status(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el estado actual del scanner PAXG 4h Mainnet"""
    try:
        status_data = paxg_scanner.get_status()
        
        return {
            "success": True,
            "data": status_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@router.get("/logs")
async def get_paxg_4h_scanner_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """Obtiene los logs del scanner PAXG 4h Mainnet"""
    try:
        logs = paxg_scanner.scanner_logs[-limit:] if paxg_scanner.scanner_logs else []
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "total_logs": len(paxg_scanner.scanner_logs),
                "latest_log": logs[-1]['message'] if logs else "No hay logs disponibles"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

# --------------------------
# Simulación/Forzado de compra (para pruebas controladas)
# --------------------------

@router.post("/force-buy")
async def force_buy_paxg_4h_mainnet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fuerza una señal de compra simulada como si viniera del escáner (MAINNET)."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")

        # Asegurar que el usuario tenga al menos una API key mainnet habilitada para PAXG 4h
        from app.db.models import TradingApiKey
        enabled_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True,
            TradingApiKey.paxg_4h_mainnet_enabled == True
        ).all()

        auto_enabled = False
        if not enabled_keys:
            # Buscar alguna key mainnet activa del usuario y habilitarla para PAXG 4h
            candidate = db.query(TradingApiKey).filter(
                TradingApiKey.user_id == current_user.id,
                TradingApiKey.is_testnet == False,
                TradingApiKey.is_active == True
            ).first()
            if candidate:
                candidate.paxg_4h_mainnet_enabled = True
                db.commit()
                auto_enabled = True
                logger.info(f"🟢 Habilitada PAXG 4h Mainnet en API key {candidate.id} para usuario {current_user.id}")
                enabled_keys = [candidate]
            else:
                raise HTTPException(status_code=400, detail="No hay API keys mainnet activas para habilitar")

        # Precio del último escaneo o endpoint directo
        price = paxg_scanner.last_scan_price
        if not price:
            # Fallback rápido al endpoint público de Binance
            import requests
            resp = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "PAXGUSDT"}, timeout=8)
            resp.raise_for_status()
            price = float(resp.json()["price"])

        # Señal simulada coherente con el ejecutor
        fake_signal = {
            'timestamp': datetime.now().isoformat(),
            'entry_price': float(price),
            'signal_strength': 0.12,
            'min_price': float(price) * 0.985,
            'pattern_width': 10,
            'atr': float(price) * 0.01,
            'dynamic_factor': 1.008,
            'depth': 0.018,
            'current_price': float(price),
            'environment': 'mainnet'
        }

        logger.info(f"🧪 Forzando compra PAXG 4h Mainnet con precio ${price:.2f}")
        await paxg_4h_executor.execute_buy_order(fake_signal, user_id=current_user.id)

        # Verificar persistencia de orden reciente
        recent = db.query(TradingOrder).filter(TradingOrder.user_id == current_user.id).order_by(TradingOrder.created_at.desc()).first()
        if not recent or (datetime.now() - (recent.created_at or datetime.now())).total_seconds() > 60:
            return {"success": False, "message": "No se persistió ninguna orden", "signal": fake_signal}

        return {
            "success": True,
            "message": "Compra disparada",
            "order_id": recent.id,
            "status": recent.status,
            "symbol": recent.symbol
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error forzando compra: {e}")
        raise HTTPException(status_code=500, detail=f"Error forzando compra: {str(e)}")

@router.post("/test-scan")
async def test_paxg_4h_mainnet_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ejecuta un escaneo de prueba del scanner PAXG 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) ejecutando escaneo de prueba PAXG 4h Mainnet")
        
        # Solo admins pueden ejecutar escaneos de prueba
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden ejecutar escaneos de prueba"
            )
        
        # Ejecutar un ciclo de escaneo
        await paxg_scanner._scan_cycle()
        
        logger.info("✅ Escaneo de prueba PAXG 4h Mainnet completado")
        return {
            "success": True,
            "message": "Escaneo de prueba completado exitosamente",
            "status": paxg_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error en escaneo de prueba PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error en escaneo de prueba: {str(e)}")

@router.get("/config")
async def get_paxg_4h_scanner_config(
    current_user: User = Depends(get_current_user)
):
    """Obtiene la configuración del scanner PAXG 4h Mainnet"""
    try:
        config = paxg_scanner.config.copy()
        detection_params = paxg_scanner.detection_params.copy()
        
        return {
            "success": True,
            "data": {
                "config": config,
                "detection_params": detection_params,
                "environment": "mainnet"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")

@router.put("/config")
async def update_paxg_4h_scanner_config(
    config_updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Actualiza la configuración del scanner PAXG 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) actualizando configuración scanner PAXG 4h Mainnet")
        
        # Solo admins pueden actualizar configuración
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden actualizar configuración"
            )
        
        # Actualizar configuración
        if 'config' in config_updates:
            paxg_scanner.config.update(config_updates['config'])
        
        if 'detection_params' in config_updates:
            paxg_scanner.detection_params.update(config_updates['detection_params'])
        
        logger.info("✅ Configuración del scanner PAXG 4h Mainnet actualizada")
        return {
            "success": True,
            "message": "Configuración actualizada exitosamente",
            "config": paxg_scanner.config,
            "detection_params": paxg_scanner.detection_params
        }
            
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración: {str(e)}")

@router.get("/alerts")
async def get_paxg_4h_scanner_alerts(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Obtiene las alertas generadas por el scanner PAXG 4h Mainnet"""
    try:
        # Filtrar logs que contienen alertas
        alert_logs = []
        for log in paxg_scanner.scanner_logs:
            if any(keyword in log['message'].lower() for keyword in ['señal', 'patrón', 'compra', 'alerta']):
                alert_logs.append(log)
        
        alerts = alert_logs[-limit:] if alert_logs else []
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alert_logs),
                "latest_alert": alerts[-1]['message'] if alerts else "No hay alertas disponibles"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo alertas del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")

@router.get("/current-price")
async def get_paxg_4h_current_price_mainnet(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el precio actual de PAXG para Mainnet"""
    try:
        import requests
        
        # Obtener precio desde Binance
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': 'PAXGUSDT'}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        price = float(data['price'])
        
        return {
            "success": True,
            "price": price,
            "environment": "mainnet",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo precio actual de PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio: {str(e)}")

@router.get("/positions")
async def get_paxg_4h_mainnet_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las posiciones abiertas de PAXG 4h Mainnet"""
    try:
        from app.db.models import TradingOrder, TradingApiKey
        from sqlalchemy import and_
        
        logger.info(f"📊 Obteniendo posiciones PAXG 4h Mainnet para usuario {current_user.id}")
        
        # Obtener API keys del usuario para mainnet
        api_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True
        ).all()
        
        logger.info(f"📊 Encontradas {len(api_keys)} API keys mainnet activas")
        
        positions = []
        for api_key in api_keys:
            # Buscar órdenes de compra ejecutadas para PAXGUSDT (solo las que NO están completadas)
            buy_orders = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key.id,
                TradingOrder.symbol == 'PAXGUSDT',
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'  # Solo órdenes ejecutadas que no están completadas
            ).order_by(TradingOrder.created_at.desc()).all()
            
            logger.info(f"📊 API Key {api_key.id}: {len(buy_orders)} órdenes BUY ejecutadas")
            
            for buy_order in buy_orders:
                # Verificar si ya tiene orden de venta posterior
                sell_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == 'PAXGUSDT',
                    TradingOrder.side == 'SELL',
                    TradingOrder.status == 'FILLED',
                    TradingOrder.created_at > buy_order.created_at
                ).order_by(TradingOrder.created_at.asc()).first()
                
                # Si no hay venta, es una posición abierta
                if not sell_order:
                    entry_price = buy_order.executed_price or buy_order.price or 0
                    quantity = buy_order.executed_quantity or buy_order.quantity or 0
                    
                    position = {
                        'order_id': buy_order.id,
                        'api_key_id': api_key.id,
                        'quantity': float(quantity),
                        'entry_price': float(entry_price),
                        'entry_time': buy_order.created_at.isoformat(),
                        'total_usdt': float(quantity * entry_price),
                        'status': 'open',
                        'symbol': buy_order.symbol,
                        'binance_order_id': buy_order.binance_order_id,
                        'order_type': buy_order.order_type,
                        'reason': buy_order.reason
                    }
                    
                    positions.append(position)
                    logger.info(f"📊 Posición abierta encontrada: {position['quantity']:.6f} PAXG @ ${position['entry_price']:.2f}")
        
        logger.info(f"📊 Total posiciones abiertas: {len(positions)}")
        
        return {
            "success": True,
            "data": {
                "positions": positions,
                "total_positions": len(positions),
                "environment": "mainnet"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo posiciones PAXG 4h Mainnet: {e}")
        logger.error(f"❌ Error details: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")

@router.get("/performance")
async def get_paxg_4h_scanner_performance(
    current_user: User = Depends(get_current_user)
):
    """Obtiene métricas de rendimiento del scanner PAXG 4h Mainnet"""
    try:
        status_data = paxg_scanner.get_status()
        
        # Calcular métricas básicas
        uptime = None
        if paxg_scanner.is_running and paxg_scanner.last_scan_time:
            uptime = (datetime.now() - paxg_scanner.last_scan_time).total_seconds()
        
        return {
            "success": True,
            "data": {
                "is_running": paxg_scanner.is_running,
                "alerts_count": paxg_scanner.alerts_count,
                "last_scan_time": paxg_scanner.last_scan_time.isoformat() if paxg_scanner.last_scan_time else None,
                "uptime_seconds": uptime,
                "total_logs": len(paxg_scanner.scanner_logs),
                "environment": "mainnet",
                "config": paxg_scanner.config
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo rendimiento del scanner PAXG 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo rendimiento: {str(e)}")

