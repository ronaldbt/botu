#!/usr/bin/env python3
"""
Script para cargar los 50 criptos más importantes de Binance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db import crud_tickers
from app.db import models
from app.schemas.tickers_schema import TickerCreate

# Los 20 criptos más importantes disponibles en Binance testnet
TOP_20_CRYPTOS = [
    # Top 10 por capitalización (verificados en testnet)
    "BTCUSDT",   # Bitcoin
    "ETHUSDT",   # Ethereum
    "BNBUSDT",   # Binance Coin
    "SOLUSDT",   # Solana
    "XRPUSDT",   # XRP
    "ADAUSDT",   # Cardano
    "DOGEUSDT",  # Dogecoin
    "AVAXUSDT",  # Avalanche
    "SHIBUSDT",  # Shiba Inu
    "DOTUSDT",   # Polkadot
    
    # Top 11-20 (verificados en testnet)
    "LTCUSDT",   # Litecoin
    "UNIUSDT",   # Uniswap
    "LINKUSDT",  # Chainlink
    "ATOMUSDT",  # Cosmos
    "ETCUSDT",   # Ethereum Classic
    "XLMUSDT",   # Stellar
    "BCHUSDT",   # Bitcoin Cash
    "TRXUSDT",   # TRON
    "NEARUSDT",  # NEAR Protocol
    "ALGOUSDT"   # Algorand
]

def load_crypto_tickers():
    """Carga los 50 criptos más importantes en la base de datos"""
    db = SessionLocal()
    try:
        print("🪙 Cargando los 20 criptos más importantes de Binance...")
        
        added_count = 0
        skipped_count = 0
        
        for ticker in TOP_20_CRYPTOS:
            # Verificar si ya existe
            existing = crud_tickers.get_ticker(db, ticker)
            if existing:
                print(f"⏭️  {ticker} ya existe, saltando...")
                skipped_count += 1
                continue
            
            # Crear nuevo ticker
            ticker_data = TickerCreate(
                ticker=ticker,
                tipo="crypto",
                sub_tipo="binance",
                pais="Global",
                nombre=ticker.replace("USDT", ""),
                activo=True
            )
            
            new_ticker = crud_tickers.create_or_update_ticker(db, ticker_data)
            print(f"✅ {ticker} agregado exitosamente")
            added_count += 1
        
        print(f"\n📊 Resumen:")
        print(f"  ✅ Agregados: {added_count}")
        print(f"  ⏭️  Saltados: {skipped_count}")
        print(f"  📈 Total procesados: {len(TOP_20_CRYPTOS)}")
        
        # Mostrar algunos tickers agregados
        print(f"\n🔍 Algunos tickers agregados:")
        recent_tickers = db.query(models.Ticker).filter(
            models.Ticker.sub_tipo == "binance"
        ).limit(10).all()
        
        for ticker in recent_tickers:
            print(f"  {ticker.ticker} - {ticker.nombre}")
            
    except Exception as e:
        print(f"❌ Error cargando tickers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_crypto_tickers()
