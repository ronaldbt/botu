<template>
  <div v-if="analysis" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h3 class="text-lg font-semibold text-slate-900 mb-6 flex items-center">
      <span class="text-2xl mr-2">📊</span>
      Análisis en Tiempo Real - {{ config.name }}
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Precio Actual -->
      <div class="text-center">
        <div class="text-3xl font-bold text-slate-900 mb-1">
          {{ formatPrice(analysis.currentPrice) }}
        </div>
        <div class="text-sm text-slate-600">Precio Actual {{ config.name }}</div>
        <div 
          v-if="analysis.priceChange"
          :class="parseFloat(analysis.priceChange) >= 0 ? 'text-emerald-600' : 'text-red-600'"
          class="text-xs font-medium mt-1"
        >
          {{ parseFloat(analysis.priceChange) >= 0 ? '+' : '' }}{{ analysis.priceChange }}%
        </div>
      </div>

      <!-- Estado del Patrón -->
      <div class="text-center">
        <div :class="getPatternStateClass(analysis.patternState)" class="inline-block px-3 py-2 rounded-lg font-semibold text-sm mb-1">
          {{ analysis.patternState || 'Monitoreando' }}
        </div>
        <div class="text-sm text-slate-600">Estado U-Pattern</div>
        <div class="text-xs text-slate-500 mt-1">
          {{ analysis.patternDescription || 'Esperando señal' }}
        </div>
      </div>

      <!-- Tiempo Restante -->
      <div class="text-center">
        <div class="text-2xl font-bold text-blue-600 mb-1">
          {{ analysis.timeUntilNextScan || '00:00:00' }}
        </div>
        <div class="text-sm text-slate-600">Próximo Escaneo</div>
        <div class="text-xs text-slate-500 mt-1">
          Ventana: {{ botConfig.timeframe }}
        </div>
      </div>

      <!-- Confianza -->
      <div class="text-center">
        <div class="text-2xl font-bold text-purple-600 mb-1">
          {{ analysis.confidence || 0 }}%
        </div>
        <div class="text-sm text-slate-600">Confianza Señal</div>
        <div class="text-xs text-slate-500 mt-1">
          Min: 85% para trade
        </div>
      </div>
    </div>

    <!-- Detalles adicionales si existen -->
    <div v-if="analysis.details" class="mt-6 pt-6 border-t border-slate-200">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div v-if="analysis.details.support" class="flex justify-between">
          <span class="text-slate-600">Soporte:</span>
          <span class="font-medium text-slate-900">{{ formatPrice(analysis.details.support) }}</span>
        </div>
        
        <div v-if="analysis.details.resistance" class="flex justify-between">
          <span class="text-slate-600">Resistencia:</span>
          <span class="font-medium text-slate-900">{{ formatPrice(analysis.details.resistance) }}</span>
        </div>
        
        <div v-if="analysis.details.volume" class="flex justify-between">
          <span class="text-slate-600">Volumen 24h:</span>
          <span class="font-medium text-slate-900">{{ analysis.details.volume.toLocaleString() }}</span>
        </div>
        
        <div v-if="analysis.details.lastUpdate" class="flex justify-between">
          <span class="text-slate-600">Actualización:</span>
          <span class="font-medium text-slate-900">{{ formatTime(analysis.details.lastUpdate) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  analysis: {
    type: Object,
    required: true
  },
  config: {
    type: Object,
    required: true
  },
  botConfig: {
    type: Object,
    required: true
  },
  formatPrice: {
    type: Function,
    required: true
  },
  getPatternStateClass: {
    type: Function,
    required: true
  }
})

const formatTime = (timestamp) => {
  try {
    return new Date(timestamp).toLocaleTimeString()
  } catch {
    return timestamp
  }
}
</script>