#!/usr/bin/env python3
"""
Test de estabilidad del sistema completo - simulación de servidor real
"""

import asyncio
import requests
import time
from datetime import datetime
import json

class StabilityTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.token = None
        self.errors = []
        self.success_count = 0
        self.total_requests = 0
        
    async def authenticate(self):
        """Autenticar con el servidor"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", 
                                   json={"username": "vlad", "password": "parol777"},
                                   timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"✅ Autenticación exitosa: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Error de autenticación: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error crítico en autenticación: {e}")
            return False
    
    def make_request(self, endpoint, method="GET", data=None):
        """Hacer request con manejo de errores"""
        self.total_requests += 1
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                self.success_count += 1
                return response.json()
            else:
                error_msg = f"{endpoint}: HTTP {response.status_code}"
                self.errors.append(error_msg)
                print(f"⚠️ {error_msg}")
                return None
                
        except requests.exceptions.Timeout:
            error_msg = f"{endpoint}: TIMEOUT"
            self.errors.append(error_msg)
            print(f"⏱️ {error_msg}")
            return None
        except Exception as e:
            error_msg = f"{endpoint}: {str(e)}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return None
    
    async def test_eth_bot_stability(self, cycles=10):
        """Test de estabilidad del bot ETH"""
        print(f"\n🧪 PROBANDO ESTABILIDAD ETH BOT ({cycles} ciclos)")
        print("-" * 50)
        
        for cycle in range(cycles):
            print(f"📍 Ciclo ETH {cycle + 1}/{cycles}")
            
            # Test status
            status = self.make_request("/eth-bot/status")
            if status:
                print(f"   ✅ Status: {status.get('is_running', 'unknown')}")
            
            # Test analysis  
            analysis = self.make_request("/eth-bot/analysis")
            if analysis:
                print(f"   ✅ Analysis: OK")
            
            # Test logs
            logs = self.make_request("/eth-bot/logs")
            if logs:
                print(f"   ✅ Logs: {len(logs.get('logs', []))} entradas")
            
            # Esperar entre requests
            await asyncio.sleep(2)
    
    async def test_bnb_bot_stability(self, cycles=10):
        """Test de estabilidad del bot BNB"""
        print(f"\n🧪 PROBANDO ESTABILIDAD BNB BOT ({cycles} ciclos)")
        print("-" * 50)
        
        for cycle in range(cycles):
            print(f"📍 Ciclo BNB {cycle + 1}/{cycles}")
            
            # Test status
            status = self.make_request("/bnb-bot/status")
            if status:
                print(f"   ✅ Status: {status.get('is_running', 'unknown')}")
            
            # Test analysis  
            analysis = self.make_request("/bnb-bot/analysis")
            if analysis:
                print(f"   ✅ Analysis: OK")
            
            # Test logs
            logs = self.make_request("/bnb-bot/logs")
            if logs:
                print(f"   ✅ Logs: {len(logs.get('logs', []))} entradas")
            
            # Esperar entre requests
            await asyncio.sleep(2)
    
    async def test_concurrent_load(self):
        """Test de carga concurrente"""
        print(f"\n🧪 PROBANDO CARGA CONCURRENTE")
        print("-" * 50)
        
        # Crear múltiples tareas concurrentes
        tasks = []
        
        # ETH requests
        for i in range(5):
            tasks.append(asyncio.create_task(self.concurrent_eth_requests(f"eth-{i}")))
        
        # BNB requests  
        for i in range(5):
            tasks.append(asyncio.create_task(self.concurrent_bnb_requests(f"bnb-{i}")))
        
        # Ejecutar todas las tareas concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
        print(f"✅ Tareas exitosas: {successful_tasks}/{len(tasks)}")
    
    async def concurrent_eth_requests(self, task_id):
        """Requests concurrentes para ETH"""
        for i in range(3):
            self.make_request("/eth-bot/status")
            await asyncio.sleep(0.5)
        return f"{task_id}: OK"
    
    async def concurrent_bnb_requests(self, task_id):
        """Requests concurrentes para BNB"""
        for i in range(3):
            self.make_request("/bnb-bot/status")
            await asyncio.sleep(0.5)
        return f"{task_id}: OK"
    
    async def run_full_stability_test(self):
        """Ejecutar test completo de estabilidad"""
        print("🚀 INICIANDO TEST DE ESTABILIDAD COMPLETO")
        print("="*60)
        print("🎯 Simulando condiciones de servidor real")
        print("⏱️ Estimado: 5-10 minutos")
        print("="*60)
        
        start_time = time.time()
        
        # 1. Autenticar
        if not await self.authenticate():
            print("❌ Test abortado: fallo de autenticación")
            return
        
        # 2. Test básico de conectividad
        basic_status = self.make_request("/")
        if not basic_status:
            print("❌ Test abortado: servidor no responde")
            return
        
        # 3. Test ETH Bot estabilidad
        await self.test_eth_bot_stability(cycles=5)
        
        # 4. Test BNB Bot estabilidad  
        await self.test_bnb_bot_stability(cycles=5)
        
        # 5. Test carga concurrente
        await self.test_concurrent_load()
        
        # 6. Test prolongado (simular uso real)
        print(f"\n🧪 TEST PROLONGADO (60 segundos)")
        print("-" * 50)
        
        end_time = time.time() + 60  # 1 minuto
        prolonged_requests = 0
        
        while time.time() < end_time:
            # Alternar entre ETH y BNB
            if prolonged_requests % 2 == 0:
                self.make_request("/eth-bot/status")
            else:
                self.make_request("/bnb-bot/status")
            
            prolonged_requests += 1
            await asyncio.sleep(3)  # Request cada 3 segundos
        
        # Estadísticas finales
        elapsed = time.time() - start_time
        success_rate = (self.success_count / self.total_requests) * 100 if self.total_requests > 0 else 0
        
        print(f"\n📊 RESULTADOS FINALES")
        print("="*60)
        print(f"⏱️ Tiempo total: {elapsed:.1f} segundos")
        print(f"📈 Requests totales: {self.total_requests}")
        print(f"✅ Requests exitosos: {self.success_count}")
        print(f"❌ Errores: {len(self.errors)}")
        print(f"📊 Tasa de éxito: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n⚠️ ERRORES DETECTADOS:")
            for error in self.errors[-10:]:  # Mostrar últimos 10
                print(f"   - {error}")
        
        # Evaluación final
        if success_rate >= 95:
            print(f"\n🟢 RESULTADO: EXCELENTE - Sistema listo para producción")
        elif success_rate >= 85:
            print(f"\n🟡 RESULTADO: BUENO - Sistema estable con pequeños ajustes")
        else:
            print(f"\n🔴 RESULTADO: NECESITA MEJORAS - No listo para producción")
        
        return success_rate >= 85

async def main():
    tester = StabilityTester()
    await tester.run_full_stability_test()

if __name__ == "__main__":
    asyncio.run(main())