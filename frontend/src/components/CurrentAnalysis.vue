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

      <!-- ATR (Volatilidad) -->
      <div class="text-center">
        <div class="text-2xl font-bold text-orange-600 mb-1">
          {{ analysis.atr ? `$${analysis.atr.toFixed(0)}` : '--' }}
        </div>
        <div class="text-sm text-slate-600">ATR (Volatilidad)</div>
        <div class="text-xs text-slate-500 mt-1">
          {{ analysis.atr ? `${((analysis.atr / analysis.currentPrice) * 100).toFixed(1)}%` : 'Calculando...' }}
        </div>
      </div>

      <!-- Tiempo Restante -->
      <div class="text-center">
        <div class="text-2xl font-bold mb-1" :class="getNextScanClass(analysis.timeUntilNextScan)">
          {{ formatNextScanTime(analysis.timeUntilNextScan) }}
        </div>
        <div class="text-sm text-slate-600">Próximo Escaneo</div>
        <div class="text-xs text-slate-500 mt-1">
          {{ analysis.isMonitoring ? `Ventana: ${botConfig.timeframe}` : 'Bot detenido' }}
        </div>
      </div>

      <!-- Estado del Monitoreo -->
      <div class="text-center">
        <div v-if="analysis.isMonitoring" class="text-lg font-bold text-green-600 mb-1">
          🟢 ACTIVO
        </div>
        <div v-else class="text-lg font-bold text-red-600 mb-1">
          🔴 INACTIVO
        </div>
        <div class="text-sm text-slate-600">Estado Monitoreo</div>
        <div class="text-xs text-slate-500 mt-1">
          {{ analysis.isMonitoring ? 'Escaneando patrones' : 'Bot detenido' }}
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

const formatNextScanTime = (timeString) => {
  if (!timeString) return '--:--:--'
  
  // Si es un mensaje de estado (no un tiempo)
  if (timeString.includes('detenido') || timeString.includes('Error') || timeString.includes('Iniciando') || timeString.includes('Escaneando')) {
    return timeString
  }
  
  return timeString
}

const getNextScanClass = (timeString) => {
  if (!timeString) return 'text-slate-400'
  
  if (timeString === 'Bot detenido' || timeString === 'Error') {
    return 'text-red-600'
  }
  
  if (timeString === 'Escaneando...' || timeString === 'Iniciando...') {
    return 'text-green-600'
  }
  
  // Si es un tiempo válido (formato HH:MM:SS)
  if (timeString.match(/^\d{2}:\d{2}:\d{2}$/)) {
    const [hours, minutes, seconds] = timeString.split(':').map(Number)
    const totalSeconds = hours * 3600 + minutes * 60 + seconds
    
    if (totalSeconds <= 60) return 'text-red-600'      // Menos de 1 minuto - rojo
    if (totalSeconds <= 300) return 'text-orange-600'  // Menos de 5 minutos - naranja
    return 'text-blue-600'                             // Más tiempo - azul
  }
  
  return 'text-blue-600'
}
</script>