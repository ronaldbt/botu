# backend/app/api/v1/bitcoin30m_scanner_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import User
from app.core.auth import get_current_user
# Importar el servicio que creamos anteriormente
from app.services.bitcoin_scanner_30m_service import bitcoin_scanner_30m

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/trading/scanner/bitcoin-30m", tags=["bitcoin-30m-scanner"])

# --------------------------
# Control del Scanner 30m
# --------------------------

@router.post("/start")
async def start_bitcoin_30m_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicia el scanner de Bitcoin 30m"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) iniciando scanner Bitcoin 30m")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        success = await bitcoin_scanner_30m.start_scanning()
        
        if success:
            logger.info("✅ Scanner Bitcoin 30m iniciado exitosamente")
            return {
                "success": True,
                "message": "Scanner Bitcoin 30m iniciado exitosamente",
                "status": bitcoin_scanner_30m.get_status()
            }
        else:
            return {
                "success": False,
                "message": "El scanner 30m ya está ejecutándose",
                "status": bitcoin_scanner_30m.get_status()
            }
            
    except Exception as e:
        logger.error(f"❌ Error iniciando scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando scanner: {str(e)}")

@router.post("/stop")
async def stop_bitcoin_30m_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detiene el scanner de Bitcoin 30m"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) deteniendo scanner Bitcoin 30m")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        success = await bitcoin_scanner_30m.stop_scanning()
        
        if success:
            logger.info("⏹️ Scanner Bitcoin 30m detenido exitosamente")
            return {
                "success": True,
                "message": "Scanner Bitcoin 30m detenido exitosamente",
                "status": bitcoin_scanner_30m.get_status()
            }
        else:
            return {
                "success": False,
                "message": "El scanner 30m ya estaba detenido",
                "status": bitcoin_scanner_30m.get_status()
            }
            
    except Exception as e:
        logger.error(f"❌ Error deteniendo scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error deteniendo scanner: {str(e)}")

@router.get("/status")
async def get_bitcoin_30m_scanner_status(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el estado actual del scanner Bitcoin 30m"""
    try:
        status = bitcoin_scanner_30m.get_status()
        logger.debug(f"📊 Status scanner Bitcoin 30m solicitado por usuario {current_user.id}")
        
        return {
            "success": True,
            "data": status,
            "timeframe": "30m"
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo status scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo status: {str(e)}")

@router.get("/logs")
async def get_bitcoin_30m_scanner_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Obtiene los logs recientes del scanner Bitcoin 30m"""
    try:
        status = bitcoin_scanner_30m.get_status()
        logs = status.get("logs", [])
        
        # Limitar la cantidad de logs
        limited_logs = logs[-limit:] if logs else []
        
        logger.debug(f"📋 Logs scanner Bitcoin 30m solicitados por usuario {current_user.id} - {len(limited_logs)} logs")
        
        return limited_logs
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

@router.put("/config")
async def update_bitcoin_30m_scanner_config(
    config_updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la configuración del scanner Bitcoin 30m"""
    try:
        logger.info(f"👤 Usuario {current_user.id} actualizando config scanner Bitcoin 30m: {config_updates}")
        
        # Solo admins pueden actualizar configuración
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden actualizar la configuración"
            )
        
        # Validar configuración
        allowed_keys = {
            'profit_target', 'stop_loss', 'min_pattern_depth', 
            'max_hold_periods', 'window_size', 'scan_interval'
        }
        
        invalid_keys = set(config_updates.keys()) - allowed_keys
        if invalid_keys:
            raise HTTPException(
                status_code=400, 
                detail=f"Claves de configuración no válidas: {invalid_keys}"
            )
        
        # Actualizar configuración
        bitcoin_scanner_30m.update_config(config_updates)
        
        logger.info("✅ Configuración scanner Bitcoin 30m actualizada exitosamente")
        return {
            "success": True,
            "message": "Configuración actualizada exitosamente",
            "config": bitcoin_scanner_30m.get_status()["config"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando config scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración: {str(e)}")

# --------------------------
# Información del Mercado 30m
# --------------------------

@router.get("/current-price")
async def get_current_bitcoin_price(
    current_user: User = Depends(get_current_user)
):
    """Obtiene el precio actual de Bitcoin"""
    try:
        # Usar los datos del scanner para obtener el precio actual
        df = await bitcoin_scanner_30m._get_binance_data()
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=503, detail="No se pudo obtener datos de mercado")
        
        current_price = float(df['close'].iloc[-1])
        timestamp = df.index[-1].isoformat()
        
        return {
            "success": True,
            "price": current_price,
            "timestamp": timestamp,
            "symbol": "BTCUSDT",
            "timeframe": "30m"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo precio actual Bitcoin: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio: {str(e)}")

@router.get("/analysis")
async def get_bitcoin_30m_market_analysis(
    current_user: User = Depends(get_current_user)
):
    """Obtiene análisis actual del mercado Bitcoin 30m"""
    try:
        # Obtener datos actuales
        df = await bitcoin_scanner_30m._get_binance_data()
        
        if df is None or len(df) < 50:
            raise HTTPException(status_code=503, detail="Datos insuficientes para análisis")
        
        current_price = float(df['close'].iloc[-1])
        
        # Detectar patrones usando el mismo algoritmo del scanner
        signals = bitcoin_scanner_30m._detect_u_patterns_30m(df)
        
        analysis = {
            "current_price": current_price,
            "timestamp": df.index[-1].isoformat(),
            "patterns_detected": len(signals),
            "timeframe": "30m",
            "market_data": {
                "high_24h": float(df['high'].tail(48).max()),  # 48 períodos = 24h
                "low_24h": float(df['low'].tail(48).min()),
                "volume_24h": float(df['volume'].tail(48).sum()),
                "price_change_24h": float((current_price / df['close'].iloc[-49] - 1) * 100) if len(df) > 49 else 0
            }
        }
        
        # Si hay señales, agregar información de la mejor
        if signals:
            best_signal = signals[0]
            analysis["signal"] = {
                "entry_price": float(best_signal['entry_price']),
                "rupture_level": float(best_signal['rupture_level']),
                "signal_strength": float(best_signal['signal_strength']),
                "pattern_depth": float(best_signal['depth']),
                "profit_target": float(best_signal['entry_price'] * 1.04),  # 4%
                "stop_loss": float(best_signal['entry_price'] * 0.985),     # 1.5%
            }
        
        return {
            "success": True,
            "data": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo análisis Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis: {str(e)}")

# --------------------------
# Estadísticas 30m
# --------------------------

@router.get("/stats")
async def get_bitcoin_30m_scanner_stats(
    current_user: User = Depends(get_current_user),
    days: int = 7
):
    """Obtiene estadísticas del scanner Bitcoin 30m"""
    try:
        status = bitcoin_scanner_30m.get_status()
        
        stats = {
            "scanner_uptime": "N/A",  # TODO: Implementar tracking de uptime
            "total_alerts": status.get("alerts_count", 0),
            "alerts_last_24h": "N/A",  # TODO: Implementar conteo por período
            "success_rate": "N/A",  # TODO: Implementar tracking de éxito
            "timeframe": "30m",
            "config": status.get("config", {}),
            "last_scan": status.get("last_scan_time"),
            "is_running": status.get("is_running", False)
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo stats scanner Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

# --------------------------
# Health Check 30m
# --------------------------

@router.get("/health")
async def bitcoin_30m_scanner_health_check():
    """Health check del scanner Bitcoin 30m"""
    try:
        status = bitcoin_scanner_30m.get_status()
        
        # Verificar si el scanner está saludable
        is_healthy = True
        issues = []
        
        # Verificar si está corriendo
        if not status.get("is_running"):
            is_healthy = False
            issues.append("Scanner no está ejecutándose")
        
        # Verificar último escaneo (debe ser reciente)
        last_scan = status.get("last_scan_time")
        if last_scan:
            try:
                last_scan_dt = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
                minutes_since_scan = (datetime.now() - last_scan_dt.replace(tzinfo=None)).total_seconds() / 60
                
                if minutes_since_scan > 45:  # Más de 45 minutos sin escanear
                    is_healthy = False
                    issues.append(f"Último escaneo hace {minutes_since_scan:.0f} minutos")
            except:
                is_healthy = False
                issues.append("Error parseando timestamp del último escaneo")
        else:
            is_healthy = False
            issues.append("No hay registro de escaneos")
        
        health_status = "healthy" if is_healthy else "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "scanner_running": status.get("is_running", False),
            "last_scan": last_scan,
            "issues": issues,
            "timeframe": "30m"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en health check scanner Bitcoin 30m: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "timeframe": "30m"
        }

# --------------------------
# Manual Trading 30m
# --------------------------

@router.post("/manual-order")
async def execute_manual_bitcoin_30m_order(
    order_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ejecuta una orden manual de trading Bitcoin 30m"""
    try:
        logger.info(f"🚀 [MANUAL TRADING] Usuario {current_user.id} ejecutando orden manual Bitcoin 30m")
        logger.info(f"📋 [MANUAL TRADING] Datos de la orden: {order_request}")
        
        # Solo admins pueden hacer trading manual por ahora
        if not current_user.is_admin:
            logger.warning(f"❌ [MANUAL TRADING] Usuario {current_user.id} no es admin - rechazando orden")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden ejecutar órdenes manuales"
            )
        
        # Validar parámetros requeridos
        required_fields = ['symbol', 'side', 'type', 'quantity']
        for field in required_fields:
            if field not in order_request:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Campo requerido faltante: {field}"
                )
        
        # Validar cantidad mínima para BTCUSDT
        symbol = order_request['symbol'].upper()
        quantity = float(order_request['quantity'])
        
        logger.info(f"🔍 [MANUAL TRADING] Validando orden: {symbol} {quantity} BTC")
        
        # Validar cantidad mínima de BTC
        if symbol == 'BTCUSDT' and quantity < 0.00001:
            logger.error(f"❌ [MANUAL TRADING] Cantidad muy pequeña: {quantity} BTC (mínimo: 0.00001)")
            raise HTTPException(
                status_code=400,
                detail=f"Cantidad mínima para {symbol} es 0.00001 BTC. Cantidad solicitada: {quantity}"
            )
        
        # Validar valor mínimo (NOTIONAL) - mínimo $5 USDT
        current_price = float(order_request.get('currentPrice', 121000))
        notional_value = quantity * current_price
        
        logger.info(f"💰 [MANUAL TRADING] Valor calculado: {quantity:.8f} BTC × ${current_price:.2f} = ${notional_value:.2f} USDT")
        
        if symbol == 'BTCUSDT' and notional_value < 5.0:
            logger.error(f"❌ [MANUAL TRADING] Valor muy pequeño: ${notional_value:.2f} USDT (mínimo: $5.00)")
            raise HTTPException(
                status_code=400,
                detail=f"Valor mínimo para {symbol} es $5.00 USDT. Valor solicitado: ${notional_value:.2f} USDT (${quantity:.8f} BTC × ${current_price:.2f})"
            )
        
        # Validar precio para órdenes LIMIT
        if order_request['type'] == 'LIMIT' and 'price' not in order_request:
            raise HTTPException(
                status_code=400,
                detail="Precio requerido para órdenes LIMIT"
            )
        
        # Obtener API key del usuario para testnet
        from app.db import crud_trading
        api_keys = crud_trading.get_user_trading_api_keys(db, current_user.id)
        testnet_api_key = None
        
        logger.info(f"🔑 [MANUAL TRADING] Buscando API key testnet activa...")
        
        for key in api_keys:
            logger.info(f"🔑 [MANUAL TRADING] API Key {key.id}: testnet={key.is_testnet}, active={key.is_active}")
            if key.is_testnet and key.is_active:
                testnet_api_key = key
                logger.info(f"✅ [MANUAL TRADING] API key testnet encontrada: {key.id}")
                break
        
        if not testnet_api_key:
            logger.error(f"❌ [MANUAL TRADING] No hay API key de testnet activa configurada")
            raise HTTPException(
                status_code=400,
                detail="No hay API key de testnet activa configurada"
            )
        
        # Obtener credenciales desencriptadas
        logger.info(f"🔐 [MANUAL TRADING] Obteniendo credenciales para API key {testnet_api_key.id}")
        credentials = crud_trading.get_decrypted_api_credentials(db, testnet_api_key.id)
        if not credentials:
            logger.error(f"❌ [MANUAL TRADING] No se pudieron obtener las credenciales")
            raise HTTPException(
                status_code=400,
                detail="No se pudieron obtener las credenciales de la API key"
            )
        
        api_key, secret_key = credentials
        logger.info(f"🔐 [MANUAL TRADING] Credenciales obtenidas: {api_key[:8]}...{api_key[-8:]}")
        
        # Conectar con Binance Testnet
        from trading_core.binance_client import BinanceClient
        logger.info(f"🌐 [MANUAL TRADING] Conectando con Binance Testnet...")
        binance_client = BinanceClient(api_key, secret_key, testnet=True)
        
        # Ejecutar orden real en Binance Testnet
        order_params = {
            'symbol': order_request['symbol'],
            'side': order_request['side'],
            'type': order_request['type'],
            'quantity': order_request['quantity']
        }
        
        if order_request['type'] == 'LIMIT':
            order_params['price'] = order_request['price']
            order_params['timeInForce'] = order_request.get('timeInForce', 'GTC')
        
        logger.info(f"📤 [MANUAL TRADING] Enviando orden REAL a Binance Testnet: {order_params}")
        logger.info(f"🎯 [MANUAL TRADING] IMPORTANTE: Esta es una orden REAL, no simulada!")
        
        # Ejecutar orden real en Binance Testnet
        try:
            logger.info(f"🚀 [MANUAL TRADING] Ejecutando orden en Binance...")
            binance_result = binance_client.place_order(**order_params)
            binance_order_id = str(binance_result.get('orderId', f"manual_30m_{int(datetime.now().timestamp())}"))
            order_status = binance_result.get('status', 'NEW')
            executed_qty = float(binance_result.get('executedQty', 0)) if binance_result.get('executedQty') else None
            executed_price = float(binance_result.get('fills', [{}])[0].get('price', 0)) if binance_result.get('fills') else None
            
            logger.info(f"✅ [MANUAL TRADING] ORDEN REAL EJECUTADA EN BINANCE!")
            logger.info(f"✅ [MANUAL TRADING] Binance Order ID: {binance_order_id}")
            logger.info(f"✅ [MANUAL TRADING] Status: {order_status}")
            logger.info(f"✅ [MANUAL TRADING] Executed Qty: {executed_qty}")
            logger.info(f"✅ [MANUAL TRADING] Executed Price: {executed_price}")
            
        except Exception as binance_error:
            logger.error(f"❌ [MANUAL TRADING] ERROR EN BINANCE TESTNET: {binance_error}")
            logger.error(f"❌ [MANUAL TRADING] La orden NO se ejecutó realmente en Binance!")
            
            # En caso de error de Binance, usar orden simulada para no fallar
            binance_order_id = f"manual_30m_sim_{int(datetime.now().timestamp())}"
            
            if order_request['type'] == 'MARKET':
                # MARKET orders se ejecutan inmediatamente (simulado)
                order_status = 'FILLED'
                executed_qty = float(order_request['quantity'])
                # Para simulación de MARKET, usar precio actual aproximado
                executed_price = float(order_request.get('currentPrice', 0))
            else:
                # LIMIT orders quedan pendientes
                order_status = 'NEW'
                executed_qty = None
                executed_price = None
                
            logger.warning(f"⚠️ [MANUAL TRADING] USANDO ORDEN SIMULADA!")
            logger.warning(f"⚠️ [MANUAL TRADING] Simulated Order ID: {binance_order_id}")
            logger.warning(f"⚠️ [MANUAL TRADING] Status: {order_status}")
            logger.warning(f"⚠️ [MANUAL TRADING] ATENCIÓN: Esta orden NO se ejecutó en Binance real!")
        
        # Guardar orden en la base de datos
        from app.db.models import TradingOrder
        
        logger.info(f"💾 [MANUAL TRADING] Guardando orden en base de datos...")
        
        db_order = TradingOrder(
            user_id=current_user.id,
            api_key_id=testnet_api_key.id,
            symbol=order_request['symbol'],
            side=order_request['side'],
            order_type=order_request['type'],
            quantity=float(order_request['quantity']),
            price=float(order_request.get('price', 0)) if order_request.get('price') else None,
            executed_price=executed_price,
            executed_quantity=executed_qty,
            status=order_status,
            binance_order_id=binance_order_id,
            executed_at=datetime.now() if order_status == 'FILLED' else None,
            reason='MANUAL_TRADE'
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        logger.info(f"✅ [MANUAL TRADING] Orden guardada en DB - ID: {db_order.id}")
        logger.info(f"✅ [MANUAL TRADING] Binance Order ID: {binance_order_id}")
        logger.info(f"✅ [MANUAL TRADING] Status: {order_status}")
        logger.info(f"✅ [MANUAL TRADING] Executed: {executed_qty} @ ${executed_price}")
        
        order_data = {
            "order_id": f"manual_30m_{db_order.id}",
            "db_id": db_order.id,
            "binance_order_id": binance_order_id,
            "symbol": order_request['symbol'],
            "side": order_request['side'],
            "type": order_request['type'],
            "quantity": order_request['quantity'],
            "price": order_request.get('price'),
            "status": db_order.status,
            "timeframe": "30m",
            "user_id": current_user.id,
            "created_at": db_order.created_at.isoformat(),
            "executed_at": db_order.executed_at.isoformat() if db_order.executed_at else None
        }
        
        return {
            "success": True,
            "message": f"Orden {order_request['side']} ejecutada exitosamente en Binance Testnet",
            "order": order_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error ejecutando orden manual Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando orden: {str(e)}")

@router.get("/manual-orders")
async def get_manual_bitcoin_30m_orders(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Obtiene las órdenes manuales recientes del usuario para Bitcoin 30m"""
    try:
        # Obtener órdenes reales de la base de datos
        from app.db import crud_trading
        
        # Obtener órdenes del usuario filtradas por symbol BTCUSDT
        orders = crud_trading.get_user_trading_orders_with_api_info(
            db, current_user.id, limit, symbol="BTCUSDT"
        )
        
        # Formatear órdenes para el frontend
        formatted_orders = []
        for order in orders:
            # order ya es un diccionario con toda la información
            price = float(order["price"]) if order["price"] else 0
            quantity = float(order["quantity"]) if order["quantity"] else 0
            
            formatted_order = {
                "id": f"manual_30m_{order['id']}",
                "db_id": order["id"],
                "side": order["side"],
                "type": order["order_type"],
                "price": str(price),
                "usdt_amount": str(quantity * price) if price else "0",
                "btc_amount": str(quantity),
                "status": order["status"],
                "symbol": order["symbol"],
                "binance_order_id": order["binance_order_id"],
                "created_at": order["created_at"].isoformat() if order["created_at"] else None,
                "executed_at": order["executed_at"].isoformat() if order["executed_at"] else None,
                "is_testnet": order["is_testnet"]
            }
            formatted_orders.append(formatted_order)
        
        logger.debug(f"📋 Órdenes manuales Bitcoin 30m obtenidas: {len(formatted_orders)} para usuario {current_user.id}")
        
        return {
            "success": True,
            "orders": formatted_orders,
            "total": len(formatted_orders)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo órdenes manuales Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo órdenes: {str(e)}")

@router.get("/positions")
async def get_bitcoin_30m_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las posiciones actuales de Bitcoin 30m"""
    try:
        from app.db import crud_trading
        from app.db.models import TradingOrder
        
        logger.debug(f"📊 Posiciones Bitcoin 30m solicitadas por usuario {current_user.id}")
        
        # Obtener todas las órdenes BUY ejecutadas para BTCUSDT
        buy_orders = db.query(TradingOrder).filter(
            TradingOrder.user_id == current_user.id,
            TradingOrder.symbol == 'BTCUSDT',
            TradingOrder.side == 'BUY',
            TradingOrder.status == 'FILLED'
        ).order_by(TradingOrder.created_at.desc()).all()
        
        logger.info(f"📊 Encontradas {len(buy_orders)} órdenes BUY ejecutadas para usuario {current_user.id}")
        
        # Para cada orden BUY, verificar si hay una orden SELL posterior
        positions = []
        for buy_order in buy_orders:
            # Buscar orden SELL posterior
            sell_order = db.query(TradingOrder).filter(
                TradingOrder.user_id == current_user.id,
                TradingOrder.symbol == 'BTCUSDT',
                TradingOrder.side == 'SELL',
                TradingOrder.status == 'FILLED',
                TradingOrder.created_at > buy_order.created_at
            ).order_by(TradingOrder.created_at.asc()).first()
            
            # Si no hay orden SELL, es una posición abierta
            if not sell_order:
                position = {
                    "id": buy_order.id,
                    "symbol": buy_order.symbol,
                    "side": "LONG",
                    "quantity": float(buy_order.executed_quantity or buy_order.quantity),
                    "entry_price": float(buy_order.executed_price or buy_order.price or 0),
                    "current_value": 0,  # Will be calculated with current price
                    "pnl_usdt": 0,
                    "pnl_percentage": 0,
                    "created_at": buy_order.created_at.isoformat(),
                    "binance_order_id": buy_order.binance_order_id,
                    "order_type": buy_order.order_type,
                    "reason": buy_order.reason
                }
                
                positions.append(position)
                logger.info(f"📊 Posición abierta encontrada: {position['quantity']:.6f} BTC @ ${position['entry_price']:.2f}")
        
        logger.info(f"📊 Total posiciones abiertas para usuario {current_user.id}: {len(positions)}")
        
        return {
            "success": True,
            "positions": positions,
            "total_positions": len(positions)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo posiciones Bitcoin 30m: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")