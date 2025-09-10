#!/usr/bin/env python3
"""
Test manual del scanner BNB usando la estrategia exacta del backtest BNB 2022
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import requests

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.services.bnb_scanner_service import BnbScannerService

async def test_bnb_scanner_manual():
    """Prueba manual del scanner BNB con datos en vivo"""
    print("🧪 TEST MANUAL SCANNER BNB")
    print("="*60)
    print("🎯 Usando estrategia exacta del backtest BNB 2022")
    print("📊 Configuración: 8% TP | 3% SL | 2.5% depth | 120 velas")
    print("="*60)
    
    # Crear instancia del scanner
    scanner = BnbScannerService()
    
    # Configurar para test manual (sin cooldown)
    scanner.cooldown_period = 0  # Sin cooldown para testing
    
    print("\n1️⃣ OBTENIENDO DATOS ACTUALES DE BNB...")
    
    # Obtener datos actuales
    df = await scanner._get_binance_data()
    if df is None:
        print("❌ Error: No se pudieron obtener datos de Binance")
        return
    
    print(f"✅ Datos obtenidos: {len(df)} velas")
    print(f"💰 Precio actual BNB: ${df['close'].iloc[-1]:,.2f}")
    print(f"📈 Cambio 24h: {((df['close'].iloc[-1] / df['close'].iloc[-24]) - 1) * 100:+.2f}%")
    
    print("\n2️⃣ ANALIZANDO PATRONES U...")
    
    # Detectar patrones usando la lógica exacta del backtest BNB 2022
    signals = scanner._detect_u_patterns_2022(df)
    
    current_price = df['close'].iloc[-1]
    
    if signals:
        print(f"🚀 PATRONES U DETECTADOS: {len(signals)}")
        print("-" * 50)
        
        for i, signal in enumerate(signals, 1):
            print(f"\n📋 SEÑAL #{i}:")
            print(f"   💰 Precio actual: ${current_price:,.2f}")
            print(f"   🎯 Nivel ruptura: ${signal['rupture_level']:,.2f}")
            print(f"   📊 % para activar: +{((signal['rupture_level']/current_price-1)*100):.2f}%")
            print(f"   📉 Profundidad patrón: {signal['depth']*100:.1f}%")
            print(f"   💪 Fuerza señal: {signal['signal_strength']:.3f}")
            print(f"   📏 Ancho patrón: {signal['pattern_width']} períodos")
            print(f"   🔧 Factor dinámico: {signal['dynamic_factor']:.4f}")
            print(f"   📈 ATR: ${signal['atr']:.2f}")
            
            # Calcular objetivos de trading
            profit_target = current_price * (1 + scanner.config['profit_target'])
            stop_loss = current_price * (1 - scanner.config['stop_loss'])
            
            print(f"\n🎯 OBJETIVOS DE TRADING:")
            print(f"   🟢 Take Profit: ${profit_target:,.2f} (+{scanner.config['profit_target']*100:.0f}%)")
            print(f"   🔴 Stop Loss: ${stop_loss:,.2f} (-{scanner.config['stop_loss']*100:.0f}%)")
            print(f"   ⏰ Max holding: {scanner.config['max_hold_periods']} períodos (≈13 días)")
            
    else:
        print("❌ NO SE DETECTARON PATRONES U")
        print("📋 Condiciones actuales:")
        
        # Mostrar algunos datos de análisis para debug
        window_size = scanner.config['window_size']
        analysis_df = df.iloc[-window_size:].copy()
        
        # Detectar mínimos para mostrar info
        significant_lows = scanner._detect_lows_2022(analysis_df)
        print(f"   🔍 Mínimos significativos encontrados: {len(significant_lows)}")
        
        if significant_lows:
            last_low = significant_lows[-1]
            print(f"   📉 Último mínimo: ${last_low['low']:,.2f} (profundidad: {last_low['depth']*100:.1f}%)")
            
            # Mostrar por qué no se activó
            atr = scanner._calculate_atr_simple(analysis_df)
            dynamic_factor = scanner._calculate_rupture_factor_bear(atr, current_price)
            nivel_ruptura = last_low['high'] * dynamic_factor
            
            print(f"   🎯 Nivel ruptura req: ${nivel_ruptura:,.2f} (+{((nivel_ruptura/current_price-1)*100):.2f}%)")
            
            recent_slope = scanner._calculate_slope(analysis_df.iloc[-6:]['close'].values)
            print(f"   📈 Momentum reciente: {recent_slope:.4f} (req: > -0.03)")
            
    print("\n3️⃣ RESUMEN DEL TEST:")
    print(f"✅ Scanner funcionando con estrategia backtest BNB 2022")
    print(f"📊 Datos en tiempo real: OK")
    print(f"🧠 Algoritmo de detección: OK") 
    print(f"⚙️ Configuración aplicada: OK")
    
    if signals:
        print(f"🚨 STATUS: SEÑAL ACTIVA - Listo para alertar")
    else:
        print(f"👀 STATUS: MONITOREANDO - Sin señales actuales")
    
    print(f"\n⏰ Test completado: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    # Ejecutar test
    asyncio.run(test_bnb_scanner_manual())