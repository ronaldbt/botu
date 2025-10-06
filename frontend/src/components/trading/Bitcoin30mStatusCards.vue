<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Scanner Status Card -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center">
          <div class="w-3 h-3 rounded-full mr-3" :class="scannerStatusColor"></div>
          <h3 class="text-sm font-medium text-slate-600">Scanner 30m</h3>
        </div>
        <span class="text-2xl">⚡</span>
      </div>
      
      <div class="space-y-2">
        <p class="text-2xl font-bold" :class="scannerStatusTextColor">
          {{ scannerStatusText }}
        </p>
        <p class="text-xs text-slate-500">
          {{ scannerSubtext }}
        </p>
      </div>
      
      <div class="mt-4 flex gap-2">
        <button 
          v-if="!scannerStatus.is_running"
          @click="$emit('start-scanner')"
          class="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs font-medium py-2 px-3 rounded-lg transition-colors hover:scale-105 active:scale-95"
          title="Iniciar scanner automático Bitcoin 30m"
        >
          ▶️ Iniciar Scanner
        </button>
        <button 
          v-if="scannerStatus.is_running"
          @click="$emit('stop-scanner')"
          class="flex-1 bg-red-600 hover:bg-red-700 text-white text-xs font-medium py-2 px-3 rounded-lg transition-colors hover:scale-105 active:scale-95"
          title="Detener scanner automático Bitcoin 30m"
        >
          ⏹️ Detener Scanner
        </button>
        <button 
          @click="$emit('refresh-status')"
          class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium py-2 px-3 rounded-lg transition-colors hover:scale-105 active:scale-95"
          title="Actualizar estado del scanner"
        >
          🔄 Actualizar
        </button>
      </div>
    </div>

    <!-- Frequency Card -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-slate-600">Frecuencia</h3>
        <span class="text-2xl">⏱️</span>
      </div>
      
      <div class="space-y-2">
        <p class="text-2xl font-bold text-orange-600">30min</p>
        <p class="text-xs text-slate-500">
          Escaneo cada 30 minutos
        </p>
        <p class="text-xs text-orange-600">
          {{ nextScanText }}
        </p>
      </div>
    </div>

    <!-- Strategy Card -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-slate-600">Estrategia</h3>
        <span class="text-2xl">🎯</span>
      </div>
      
      <div class="space-y-2">
        <div class="flex justify-between text-xs">
          <span class="text-slate-500">Take Profit:</span>
          <span class="font-medium text-green-600">+4.0%</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-slate-500">Stop Loss:</span>
          <span class="font-medium text-red-600">-1.5%</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-slate-500">Max Hold:</span>
          <span class="font-medium text-blue-600">24h</span>
        </div>
        <div class="flex justify-between text-xs">
          <span class="text-slate-500">Cooldown:</span>
          <span class="font-medium text-purple-600">30min</span>
        </div>
      </div>
    </div>

    <!-- Alerts Counter Card -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-slate-600">Alertas 30m</h3>
        <span class="text-2xl">🚨</span>
      </div>
      
      <div class="space-y-2">
        <p class="text-2xl font-bold text-blue-600">
          {{ scannerStatus.alerts_count || 0 }}
        </p>
        <p class="text-xs text-slate-500">
          Total alertas enviadas
        </p>
        <p v-if="cooldownText" class="text-xs text-orange-600">
          {{ cooldownText }}
        </p>
        <p v-else class="text-xs text-green-600">
          ✅ Listo para alertas
        </p>
      </div>
    </div>

    <!-- Last Scan Card -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 md:col-span-2 lg:col-span-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-medium text-slate-600">Último Escaneo 30m</h3>
        <span class="text-2xl">📊</span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <p class="text-xs text-slate-500 mb-1">Timestamp</p>
          <p class="text-sm font-medium">
            {{ lastScanFormatted || 'Nunca' }}
          </p>
        </div>
        
        <div>
          <p class="text-xs text-slate-500 mb-1">Estado</p>
          <p class="text-sm font-medium" :class="lastScanStatusColor">
            {{ lastScanStatus }}
          </p>
        </div>
        
        <div>
          <p class="text-xs text-slate-500 mb-1">Ambiente</p>
          <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" 
                :class="environment === 'testnet' ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800'">
            {{ environment === 'testnet' ? '🧪 Testnet' : '🔴 Mainnet' }}
          </span>
        </div>
      </div>

      <!-- Recent Logs Preview -->
      <div v-if="recentLogs.length > 0" class="mt-4 pt-4 border-t border-slate-100">
        <p class="text-xs text-slate-500 mb-2">Últimos logs:</p>
        <div class="space-y-1">
          <div v-for="log in recentLogs" :key="log.timestamp" 
               class="flex items-center justify-between text-xs p-2 bg-slate-50 rounded">
            <div class="flex items-center">
              <span class="mr-2">{{ getLogIcon(log.level) }}</span>
              <span class="truncate" :class="getLogTextClass(log.level)">
                {{ log.message }}
              </span>
            </div>
            <span class="text-slate-400 ml-2">
              {{ formatLogTime(log.timestamp) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scannerStatus: {
    type: Object,
    default: () => ({
      is_running: false,
      alerts_count: 0,
      next_scan_in_seconds: null,
      cooldown_remaining: null
    })
  },
  scannerLogs: {
    type: Array,
    default: () => []
  },
  lastScan: {
    type: String,
    default: null
  },
  environment: {
    type: String,
    default: 'testnet'
  }
})

const emit = defineEmits(['start-scanner', 'stop-scanner', 'refresh-status'])

// Computed properties para el estado del scanner
const scannerStatusColor = computed(() => {
  return props.scannerStatus.is_running ? 'bg-green-500' : 'bg-red-500'
})

const scannerStatusTextColor = computed(() => {
  return props.scannerStatus.is_running ? 'text-green-600' : 'text-red-600'
})

const scannerStatusText = computed(() => {
  return props.scannerStatus.is_running ? 'Activo' : 'Inactivo'
})

const scannerSubtext = computed(() => {
  return props.scannerStatus.is_running ? 'Escaneando patrones U' : 'Scanner detenido'
})

// Próximo escaneo
const nextScanText = computed(() => {
  if (!props.scannerStatus.is_running) return 'Scanner inactivo'
  
  const nextScan = props.scannerStatus.next_scan_in_seconds
  if (!nextScan) return 'Calculando...'
  
  const minutes = Math.floor(nextScan / 60)
  const seconds = nextScan % 60
  
  if (minutes > 0) {
    return `Próximo en ${minutes}m ${seconds}s`
  } else {
    return `Próximo en ${seconds}s`
  }
})

// Cooldown
const cooldownText = computed(() => {
  const cooldown = props.scannerStatus.cooldown_remaining
  if (!cooldown || cooldown <= 0) return null
  
  const minutes = Math.floor(cooldown / 60)
  const seconds = Math.floor(cooldown % 60)
  
  if (minutes > 0) {
    return `Cooldown: ${minutes}m ${seconds}s`
  } else {
    return `Cooldown: ${seconds}s`
  }
})

// Último escaneo
const lastScanFormatted = computed(() => {
  if (!props.lastScan) return null
  
  try {
    return new Date(props.lastScan).toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return props.lastScan
  }
})

const lastScanStatus = computed(() => {
  if (!props.lastScan) return 'Sin escaneos'
  
  const scanTime = new Date(props.lastScan)
  const now = new Date()
  const diffMinutes = (now - scanTime) / 1000 / 60
  
  if (diffMinutes < 2) return 'Reciente'
  if (diffMinutes < 35) return 'Normal'
  return 'Atrasado'
})

const lastScanStatusColor = computed(() => {
  const status = lastScanStatus.value
  if (status === 'Reciente') return 'text-green-600'
  if (status === 'Normal') return 'text-blue-600'
  if (status === 'Atrasado') return 'text-red-600'
  return 'text-slate-600'
})

// Logs recientes
const recentLogs = computed(() => {
  return props.scannerLogs.slice(-3) // Últimos 3 logs
})

// Utilidades para logs
const formatLogTime = (timestamp) => {
  try {
    return new Date(timestamp).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return timestamp
  }
}

const getLogTextClass = (level) => {
  const classes = {
    'SUCCESS': 'text-green-700',
    'ERROR': 'text-red-700', 
    'WARNING': 'text-yellow-700',
    'INFO': 'text-blue-700'
  }
  return classes[level] || 'text-gray-700'
}

const getLogIcon = (level) => {
  const icons = {
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WARNING': '⚠️',
    'INFO': 'ℹ️'
  }
  return icons[level] || '📝'
}
</script>