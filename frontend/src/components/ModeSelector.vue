<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h2 class="text-xl font-semibold text-slate-900 mb-4">Seleccionar Modo de Operación</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Manual Mode -->
      <div class="relative">
        <input type="radio" id="manual" :value="'manual'" v-model="selectedMode" class="sr-only">
        <label for="manual" :class="[
          'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200',
          selectedMode === 'manual' 
            ? 'border-blue-500 bg-blue-50 shadow-md' 
            : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
        ]">
          <div class="flex items-center mb-3">
            <div class="text-2xl mr-3">👁️</div>
            <div>
              <div class="font-semibold text-slate-900">Modo Manual</div>
              <div class="text-sm text-slate-600">Solo alertas - Trading manual</div>
            </div>
          </div>
          <ul class="text-sm text-slate-600 space-y-1">
            <li>• API pública de Binance</li>
            <li>• Solo notificaciones de compra/venta</li>
            <li>• Tú ejecutas las órdenes manualmente</li>
            <li>• Sin riesgo - Solo análisis</li>
          </ul>
        </label>
      </div>

      <!-- Automatic Mode -->
      <div class="relative">
        <input type="radio" id="automatic" :value="'automatic'" v-model="selectedMode" class="sr-only">
        <label for="automatic" :class="[
          'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200',
          selectedMode === 'automatic' 
            ? 'border-emerald-500 bg-emerald-50 shadow-md' 
            : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
        ]">
          <div class="flex items-center mb-3">
            <div class="text-2xl mr-3">🤖</div>
            <div>
              <div class="font-semibold text-slate-900">Modo Automático</div>
              <div class="text-sm text-slate-600">Trading automático - Testnet</div>
            </div>
          </div>
          <ul class="text-sm text-slate-600 space-y-1">
            <li>• Binance Testnet (dinero virtual)</li>
            <li>• Ejecuta trades automáticamente</li>
            <li>• Stop loss y take profit</li>
            <li>• Aprendizaje sin riesgo real</li>
          </ul>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
const selectedMode = defineModel()
</script>