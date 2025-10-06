# backend/app/services/automated_trading_service.py

import asyncio
import logging
import sys
import os
from typing import Dict, Optional, List, Any
from datetime import datetime
import threading

# Add src path for trading modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from automated_trader import AutomatedTrader

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedTradingService:
    """
    Servicio para gestionar el trading automático desde el backend
    Integra el AutomatedTrader con la API del backend
    """
    
    def __init__(self):
        self.trader = None
        self.trading_thread = None
        self.is_running = False
        self.service_logs = []
        self.max_logs = 100
        
    def start_trading(self, testnet: bool = True, trading_enabled: bool = False) -> Dict[str, Any]:
        """
        Inicia el sistema de trading automático
        
        Args:
            testnet: Si usar testnet (True) o mainnet (False)
            trading_enabled: Si ejecutar trades reales (True) o solo simulación (False)
        """
        try:
            if self.is_running:
                return {
                    "success": False,
                    "message": "El trading automático ya está en ejecución",
                    "status": self.get_status()
                }
            
            # Crear trader
            self.trader = AutomatedTrader(testnet=testnet, trading_enabled=trading_enabled)
            
            # Iniciar en thread separado para no bloquear la API
            self.trading_thread = threading.Thread(
                target=self._run_trader,
                daemon=True
            )
            self.trading_thread.start()
            
            self.is_running = True
            
            log_message = f"🚀 Trading automático iniciado - {'TESTNET' if testnet else 'MAINNET'} - {'REAL' if trading_enabled else 'SIMULACIÓN'}"
            self._add_log("INFO", log_message)
            logger.info(log_message)
            
            return {
                "success": True,
                "message": "Trading automático iniciado correctamente",
                "status": self.get_status()
            }
            
        except Exception as e:
            error_message = f"Error iniciando trading automático: {str(e)}"
            self._add_log("ERROR", error_message)
            logger.error(error_message)
            
            return {
                "success": False,
                "message": error_message,
                "status": self.get_status()
            }
    
    def _run_trader(self):
        """Ejecuta el trader en un loop asyncio"""
        try:
            # Crear nuevo loop para este thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Ejecutar trader
            loop.run_until_complete(self.trader.start())
            
        except Exception as e:
            error_message = f"Error en thread de trading: {str(e)}"
            self._add_log("ERROR", error_message)
            logger.error(error_message)
        finally:
            self.is_running = False
    
    def stop_trading(self) -> Dict[str, Any]:
        """Detiene el sistema de trading automático"""
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "message": "El trading automático no está en ejecución",
                    "status": self.get_status()
                }
            
            # Detener trader
            if self.trader:
                self.trader.stop()
            
            # Esperar que termine el thread
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=10)
            
            self.is_running = False
            self.trader = None
            self.trading_thread = None
            
            log_message = "🛑 Trading automático detenido"
            self._add_log("INFO", log_message)
            logger.info(log_message)
            
            return {
                "success": True,
                "message": "Trading automático detenido correctamente",
                "status": self.get_status()
            }
            
        except Exception as e:
            error_message = f"Error deteniendo trading automático: {str(e)}"
            self._add_log("ERROR", error_message)
            logger.error(error_message)
            
            return {
                "success": False,
                "message": error_message,
                "status": self.get_status()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del trading automático"""
        base_status = {
            "service_running": self.is_running,
            "thread_alive": self.trading_thread.is_alive() if self.trading_thread else False,
            "logs_count": len(self.service_logs),
            "last_update": datetime.now().isoformat()
        }
        
        if self.trader:
            trader_status = self.trader.get_status()
            return {**base_status, **trader_status}
        else:
            return {
                **base_status,
                "trader_running": False,
                "testnet": None,
                "trading_enabled": None,
                "active_positions": 0,
                "total_trades": 0,
                "positions": {},
                "config": {}
            }
    
    def get_positions(self) -> Dict[str, Any]:
        """Obtiene las posiciones activas"""
        if self.trader:
            return self.trader.active_positions
        return {}
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Obtiene el historial de trades"""
        if self.trader:
            return self.trader.trade_history
        return []
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Obtiene los logs del servicio"""
        return self.service_logs
    
    def _add_log(self, level: str, message: str):
        """Añade un log al historial"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        self.service_logs.append(log_entry)
        
        # Mantener solo los últimos logs
        if len(self.service_logs) > self.max_logs:
            self.service_logs = self.service_logs[-self.max_logs:]
    
    def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza la configuración del trading"""
        try:
            if not self.trader:
                return {
                    "success": False,
                    "message": "No hay trader activo para actualizar configuración"
                }
            
            # Actualizar configuración del trader
            for key, value in config.items():
                if key in self.trader.trading_config:
                    self.trader.trading_config[key] = value
            
            log_message = f"⚙️ Configuración actualizada: {config}"
            self._add_log("INFO", log_message)
            logger.info(log_message)
            
            return {
                "success": True,
                "message": "Configuración actualizada correctamente",
                "config": self.trader.trading_config
            }
            
        except Exception as e:
            error_message = f"Error actualizando configuración: {str(e)}"
            self._add_log("ERROR", error_message)
            logger.error(error_message)
            
            return {
                "success": False,
                "message": error_message
            }

# Instancia singleton del servicio
automated_trading_service = AutomatedTradingService()