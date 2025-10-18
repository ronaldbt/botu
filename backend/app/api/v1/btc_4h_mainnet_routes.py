# backend/app/api/v1/btc_4h_mainnet_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import User
from app.core.auth import get_current_user
from app.services.bitcoin_scanner_service import bitcoin_scanner
from app.services.auto_trading_executor import auto_trading_executor
from app.db.models import TradingOrder
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/trading/scanner/btc-4h-mainnet", tags=["btc-4h-mainnet-scanner"])

# --------------------------
# Control del Scanner BTC 4h Mainnet
# --------------------------

@router.post("/start")
async def start_btc_4h_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicia el scanner de BTC 4h para Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) iniciando scanner BTC 4h Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        if bitcoin_scanner.is_running:
            return {
                "success": False,
                "message": "El scanner BTC 4h Mainnet ya está ejecutándose",
                "status": bitcoin_scanner.get_status()
            }
        
        # Iniciar scanner
        import asyncio
        asyncio.create_task(bitcoin_scanner.start_scanning())
        
        logger.info("✅ Scanner BTC 4h Mainnet iniciado exitosamente")
        return {
            "success": True,
            "message": "Scanner BTC 4h Mainnet iniciado exitosamente",
            "status": bitcoin_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error iniciando scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando scanner: {str(e)}")

@router.post("/stop")
async def stop_btc_4h_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detiene el scanner de BTC 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) deteniendo scanner BTC 4h Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        await bitcoin_scanner.stop_scanning()
        
        logger.info("⏹️ Scanner BTC 4h Mainnet detenido exitosamente")
        return {
            "success": True,
            "message": "Scanner BTC 4h Mainnet detenido exitosamente",
            "status": bitcoin_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error deteniendo scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error deteniendo scanner: {str(e)}")

@router.get("/status")
async def get_btc_4h_scanner_status(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el estado actual del scanner BTC 4h Mainnet"""
    try:
        status_data = bitcoin_scanner.get_status()
        
        return {
            "success": True,
            "data": status_data
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@router.get("/logs")
async def get_btc_4h_scanner_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """Obtiene los logs del scanner BTC 4h Mainnet"""
    try:
        logs = bitcoin_scanner.scanner_logs[-limit:] if bitcoin_scanner.scanner_logs else []
        
        return {
            "success": True,
            "data": {
                "logs": logs,
                "total_logs": len(bitcoin_scanner.scanner_logs),
                "latest_log": logs[-1]['message'] if logs else "No hay logs disponibles"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

# --------------------------
# Simulación/Forzado de compra (para pruebas controladas)
# --------------------------

@router.post("/force-buy")
async def force_buy_btc_4h_mainnet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fuerza una señal de compra simulada como si viniera del escáner (MAINNET)."""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")

        # Asegurar que el usuario tenga al menos una API key mainnet habilitada para BTC 4h
        from app.db.models import TradingApiKey
        enabled_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True,
            TradingApiKey.btc_4h_mainnet_enabled == True
        ).all()

        auto_enabled = False
        if not enabled_keys:
            # Buscar alguna key mainnet activa del usuario y habilitarla para BTC 4h
            candidate = db.query(TradingApiKey).filter(
                TradingApiKey.user_id == current_user.id,
                TradingApiKey.is_testnet == False,
                TradingApiKey.is_active == True
            ).first()
            if candidate:
                candidate.btc_4h_mainnet_enabled = True
                # Mantener la asignación tal cual; si es 0, el ejecutor podría abortar por falta de USDT
                db.commit()
                auto_enabled = True
                logger.info(f"🟢 Habilitada BTC 4h Mainnet en API key {candidate.id} para usuario {current_user.id}")
                enabled_keys = [candidate]
            else:
                raise HTTPException(status_code=400, detail="No hay API keys mainnet activas para habilitar")

        # Precio del último escaneo o endpoint directo
        price = bitcoin_scanner.last_scan_price
        if not price:
            # Fallback rápido al endpoint público de Binance
            import requests
            resp = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=8)
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

        logger.info(f"🧪 Forzando compra BTC 4h Mainnet con precio ${price:.2f}")
        await auto_trading_executor.execute_buy_signal('btc', fake_signal, alerta_id=None)

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
async def test_btc_4h_mainnet_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ejecuta un escaneo de prueba del scanner BTC 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) ejecutando escaneo de prueba BTC 4h Mainnet")
        
        # Solo admins pueden ejecutar escaneos de prueba
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden ejecutar escaneos de prueba"
            )
        
        # Ejecutar un ciclo de escaneo
        await bitcoin_scanner._perform_scan()
        
        logger.info("✅ Escaneo de prueba BTC 4h Mainnet completado")
        return {
            "success": True,
            "message": "Escaneo de prueba completado exitosamente",
            "status": bitcoin_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error en escaneo de prueba BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error en escaneo de prueba: {str(e)}")

@router.get("/config")
async def get_btc_4h_scanner_config(
    current_user: User = Depends(get_current_user)
):
    """Obtiene la configuración del scanner BTC 4h Mainnet"""
    try:
        config = bitcoin_scanner.config.copy()
        
        return {
            "success": True,
            "data": {
                "config": config,
                "environment": "mainnet"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")

@router.put("/config")
async def update_btc_4h_scanner_config(
    config_updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Actualiza la configuración del scanner BTC 4h Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) actualizando configuración scanner BTC 4h Mainnet")
        
        # Solo admins pueden actualizar configuración
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden actualizar configuración"
            )
        
        # Actualizar configuración
        if 'config' in config_updates:
            bitcoin_scanner.config.update(config_updates['config'])
        
        logger.info("✅ Configuración del scanner BTC 4h Mainnet actualizada")
        return {
            "success": True,
            "message": "Configuración actualizada exitosamente",
            "config": bitcoin_scanner.config
        }
            
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración: {str(e)}")

@router.get("/alerts")
async def get_btc_4h_scanner_alerts(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Obtiene las alertas generadas por el scanner BTC 4h Mainnet"""
    try:
        # Filtrar logs que contienen alertas
        alert_logs = []
        for log in bitcoin_scanner.scanner_logs:
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
        logger.error(f"❌ Error obteniendo alertas del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo alertas: {str(e)}")

@router.get("/current-price")
async def get_btc_4h_current_price_mainnet(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el precio actual de BTC para Mainnet"""
    try:
        import requests
        
        # Obtener precio desde Binance
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': 'BTCUSDT'}
        
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
        logger.error(f"❌ Error obteniendo precio actual de BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio: {str(e)}")

@router.get("/positions")
async def get_btc_4h_mainnet_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las posiciones abiertas de BTC 4h Mainnet"""
    try:
        from app.db.models import TradingOrder, TradingApiKey
        from sqlalchemy import and_
        
        logger.info(f"📊 Obteniendo posiciones BTC 4h Mainnet para usuario {current_user.id}")
        
        # Obtener API keys del usuario para mainnet
        api_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True
        ).all()
        
        logger.info(f"📊 Encontradas {len(api_keys)} API keys mainnet activas")
        
        positions = []
        for api_key in api_keys:
            # Buscar órdenes de compra ejecutadas para BTCUSDT
            buy_orders = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key.id,
                TradingOrder.symbol == 'BTCUSDT',
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'
            ).order_by(TradingOrder.created_at.desc()).all()
            
            logger.info(f"📊 API Key {api_key.id}: {len(buy_orders)} órdenes BUY ejecutadas")
            
            for buy_order in buy_orders:
                # Verificar si ya tiene orden de venta posterior
                sell_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == 'BTCUSDT',
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
                    logger.info(f"📊 Posición abierta encontrada: {position['quantity']:.6f} BTC @ ${position['entry_price']:.2f}")
        
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
        logger.error(f"❌ Error obteniendo posiciones BTC 4h Mainnet: {e}")
        logger.error(f"❌ Error details: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")

@router.get("/performance")
async def get_btc_4h_scanner_performance(
    current_user: User = Depends(get_current_user)
):
    """Obtiene métricas de rendimiento del scanner BTC 4h Mainnet"""
    try:
        status_data = bitcoin_scanner.get_status()
        
        # Calcular métricas básicas
        uptime = None
        if bitcoin_scanner.is_running and bitcoin_scanner.last_scan_time:
            uptime = (datetime.now() - bitcoin_scanner.last_scan_time).total_seconds()
        
        return {
            "success": True,
            "data": {
                "is_running": bitcoin_scanner.is_running,
                "alerts_count": bitcoin_scanner.alerts_count,
                "last_scan_time": bitcoin_scanner.last_scan_time.isoformat() if bitcoin_scanner.last_scan_time else None,
                "uptime_seconds": uptime,
                "total_logs": len(bitcoin_scanner.scanner_logs),
                "environment": "mainnet",
                "config": bitcoin_scanner.config
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo rendimiento del scanner BTC 4h Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo rendimiento: {str(e)}")
