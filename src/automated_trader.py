# src/automated_trader.py

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv
import sys

# Add backend path for services
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from binance_client import BinanceClient, fetch_klines
from app.services.bitcoin_scanner_service import BitcoinScannerService
from app.services.eth_scanner_service import EthScannerService
from app.services.bnb_scanner_service import BnbScannerService

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutomatedTrader:
    """
    Trading automático usando los scanners exitosos del sistema
    Integra las mismas estrategias probadas (8% TP, 3% SL) para mainnet/testnet
    """
    
    def __init__(self, testnet: bool = True, trading_enabled: bool = False):
        self.testnet = testnet
        self.trading_enabled = trading_enabled
        self.is_running = False
        
        # Configuración de API keys
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            logger.warning("⚠️ API keys no configuradas - Solo modo simulación disponible")
            self.client = None
        else:
            self.client = BinanceClient(api_key, secret_key, testnet=testnet)
            logger.info(f"🔑 Cliente Binance configurado ({'TESTNET' if testnet else 'MAINNET'})")
        
        # Inicializar scanners con las estrategias exitosas
        self.bitcoin_scanner = BitcoinScannerService()
        self.eth_scanner = EthScannerService() 
        self.bnb_scanner = BnbScannerService()
        
        # Estado del trading
        self.active_positions = {}
        self.trading_config = {
            "max_positions": 3,  # Máximo 3 posiciones simultáneas
            "position_size_usdt": 50,  # $50 por posición en testnet
            "risk_per_trade": 0.02,  # 2% del capital por operación
            "cooldown_between_trades": 1800,  # 30 minutos entre trades del mismo símbolo
        }
        
        # Histórico de trades
        self.trade_history = []
        self.last_trade_times = {}  # Para cooldown por símbolo
        
    async def start(self):
        """Inicia el sistema de trading automático"""
        if self.is_running:
            logger.warning("⚠️ El trader automático ya está en ejecución")
            return
            
        self.is_running = True
        logger.info("🚀 Iniciando sistema de trading automático...")
        
        if self.client:
            # Verificar conexión
            success, result = self.client.test_connection()
            if not success:
                logger.error(f"❌ Error de conexión: {result}")
                return
            logger.info("✅ Conexión con Binance establecida")
            
        # Iniciar scanners
        await self._start_scanners()
        
        # Iniciar loop principal de trading
        await self._trading_loop()
    
    async def _start_scanners(self):
        """Inicia todos los scanners"""
        try:
            logger.info("🔍 Iniciando scanners de patrones...")
            
            # Iniciar scanners en paralelo
            scanner_tasks = [
                asyncio.create_task(self.bitcoin_scanner.start_scanning()),
                asyncio.create_task(self.eth_scanner.start_scanning()),
                asyncio.create_task(self.bnb_scanner.start_scanning())
            ]
            
            logger.info("✅ Todos los scanners iniciados")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scanners: {e}")
    
    async def _trading_loop(self):
        """Loop principal de trading"""
        logger.info("🔄 Iniciando loop de trading automático...")
        
        while self.is_running:
            try:
                # Verificar señales de los scanners
                await self._check_scanner_signals()
                
                # Gestionar posiciones activas
                await self._manage_positions()
                
                # Esperar antes del siguiente ciclo
                await asyncio.sleep(30)  # Revisar cada 30 segundos
                
            except Exception as e:
                logger.error(f"❌ Error en loop de trading: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo si hay error
    
    async def _check_scanner_signals(self):
        """Revisa señales de todos los scanners"""
        scanners = [
            ("BTC", self.bitcoin_scanner),
            ("ETH", self.eth_scanner), 
            ("BNB", self.bnb_scanner)
        ]
        
        for crypto, scanner in scanners:
            try:
                # Verificar si el scanner detectó un patrón U válido
                if await self._has_valid_u_pattern(scanner):
                    symbol = f"{crypto}USDT"
                    
                    # Verificar si podemos operar este símbolo
                    if await self._can_trade_symbol(symbol):
                        await self._execute_buy_signal(symbol, scanner)
                        
            except Exception as e:
                logger.error(f"❌ Error revisando señales de {crypto}: {e}")
    
    async def _has_valid_u_pattern(self, scanner) -> bool:
        """
        Verifica si el scanner ha detectado un patrón U válido
        Usa la misma lógica exitosa de los scanners
        """
        try:
            # Obtener el último status del scanner
            if not hasattr(scanner, 'scanner_logs') or not scanner.scanner_logs:
                return False
                
            # Buscar logs recientes de detección de patrón
            recent_logs = scanner.scanner_logs[-5:]  # Últimos 5 logs
            
            for log in recent_logs:
                if "patrón U detectado" in log.get('message', '').lower():
                    # Verificar que no sea muy antiguo (últimos 10 minutos)
                    log_time = datetime.fromisoformat(log.get('timestamp', ''))
                    if (datetime.now() - log_time).total_seconds() < 600:
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Error verificando patrón U: {e}")
            return False
    
    async def _can_trade_symbol(self, symbol: str) -> bool:
        """Verifica si podemos operar el símbolo"""
        try:
            # Verificar máximo de posiciones
            if len(self.active_positions) >= self.trading_config["max_positions"]:
                return False
                
            # Verificar si ya tenemos posición abierta en este símbolo
            if symbol in self.active_positions:
                return False
                
            # Verificar cooldown
            last_trade = self.last_trade_times.get(symbol, 0)
            if time.time() - last_trade < self.trading_config["cooldown_between_trades"]:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error verificando si se puede operar {symbol}: {e}")
            return False
    
    async def _execute_buy_signal(self, symbol: str, scanner):
        """Ejecuta señal de compra"""
        try:
            logger.info(f"🎯 Señal de compra detectada para {symbol}")
            
            if not self.trading_enabled:
                logger.info(f"📊 SIMULACIÓN: Comprando {symbol} por ${self.trading_config['position_size_usdt']}")
                await self._simulate_trade(symbol, "BUY")
                return
            
            if not self.client:
                logger.warning("⚠️ No hay cliente configurado - Solo simulación")
                return
                
            # Ejecutar compra real
            position_size = self.trading_config["position_size_usdt"]
            
            # TODO: Implementar lógica de compra real usando self.client
            # order = await self._place_buy_order(symbol, position_size)
            
            # Por ahora solo simulación hasta completar implementación
            await self._simulate_trade(symbol, "BUY")
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando compra de {symbol}: {e}")
    
    async def _simulate_trade(self, symbol: str, side: str):
        """Simula una operación de trading"""
        try:
            current_price = await self._get_current_price(symbol)
            position_size = self.trading_config["position_size_usdt"]
            quantity = position_size / current_price
            
            trade = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": current_price,
                "timestamp": datetime.now(),
                "position_size_usdt": position_size,
                "stop_loss": current_price * 0.97,  # 3% SL
                "take_profit": current_price * 1.08,  # 8% TP
                "simulated": True
            }
            
            self.active_positions[symbol] = trade
            self.trade_history.append(trade)
            self.last_trade_times[symbol] = time.time()
            
            logger.info(f"📊 SIMULACIÓN {side}: {symbol} - Cantidad: {quantity:.6f} - Precio: ${current_price:.2f}")
            logger.info(f"🎯 TP: ${trade['take_profit']:.2f} | 🛡️ SL: ${trade['stop_loss']:.2f}")
            
        except Exception as e:
            logger.error(f"Error simulando trade: {e}")
    
    async def _get_current_price(self, symbol: str) -> float:
        """Obtiene precio actual del símbolo"""
        try:
            from binance_client import get_ticker_price
            return get_ticker_price(symbol)
        except Exception as e:
            logger.error(f"Error obteniendo precio de {symbol}: {e}")
            return 0.0
    
    async def _manage_positions(self):
        """Gestiona posiciones activas (TP/SL)"""
        positions_to_close = []
        
        for symbol, position in self.active_positions.items():
            try:
                current_price = await self._get_current_price(symbol)
                if current_price == 0:
                    continue
                    
                entry_price = position["price"]
                pnl_pct = (current_price - entry_price) / entry_price
                
                # Verificar Take Profit (8%)
                if current_price >= position["take_profit"]:
                    logger.info(f"🎯 TAKE PROFIT alcanzado para {symbol} - PnL: +{pnl_pct*100:.2f}%")
                    positions_to_close.append(symbol)
                    
                # Verificar Stop Loss (3%)
                elif current_price <= position["stop_loss"]:
                    logger.info(f"🛡️ STOP LOSS activado para {symbol} - PnL: {pnl_pct*100:.2f}%")
                    positions_to_close.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error gestionando posición de {symbol}: {e}")
        
        # Cerrar posiciones
        for symbol in positions_to_close:
            await self._close_position(symbol)
    
    async def _close_position(self, symbol: str):
        """Cierra una posición"""
        try:
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                current_price = await self._get_current_price(symbol)
                
                # Calcular PnL
                entry_price = position["price"]
                pnl_pct = (current_price - entry_price) / entry_price
                pnl_usdt = position["position_size_usdt"] * pnl_pct
                
                logger.info(f"✅ Cerrando posición {symbol} - PnL: {pnl_pct*100:.2f}% (${pnl_usdt:.2f})")
                
                # Remover de posiciones activas
                del self.active_positions[symbol]
                
        except Exception as e:
            logger.error(f"Error cerrando posición de {symbol}: {e}")
    
    def stop(self):
        """Detiene el trading automático"""
        self.is_running = False
        logger.info("🛑 Deteniendo sistema de trading automático...")
    
    def get_status(self) -> Dict:
        """Retorna estado actual del trader"""
        return {
            "is_running": self.is_running,
            "testnet": self.testnet,
            "trading_enabled": self.trading_enabled,
            "active_positions": len(self.active_positions),
            "total_trades": len(self.trade_history),
            "positions": self.active_positions,
            "config": self.trading_config
        }

if __name__ == "__main__":
    # Ejemplo de uso
    trader = AutomatedTrader(testnet=True, trading_enabled=False)
    
    try:
        asyncio.run(trader.start())
    except KeyboardInterrupt:
        trader.stop()
        logger.info("👋 Trading automático detenido por el usuario")