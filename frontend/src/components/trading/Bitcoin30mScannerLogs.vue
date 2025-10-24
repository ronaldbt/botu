<template>
  <div class="bg-gray-900 rounded-xl shadow-lg border border-gray-700 mb-8">
    <!-- Terminal Header -->
    <div class="px-4 md:px-6 py-4 border-b border-gray-700 bg-gray-800">
      <!-- Mobile Layout -->
      <div class="md:hidden space-y-3">
        <!-- Title Row -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="flex space-x-2 mr-3">
              <div class="w-2 h-2 bg-red-500 rounded-full"></div>
              <div class="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <div class="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
            <div>
              <h3 class="text-base font-semibold text-white">Bitcoin 30m Scanner</h3>
              <p class="text-xs text-gray-400">Actividad en tiempo real</p>
            </div>
          </div>
          <button 
            @click="$emit('refresh')"
            :disabled="refreshing"
            class="inline-flex items-center px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs font-medium rounded transition-colors disabled:opacity-50"
          >
            <span class="mr-1" :class="{ 'animate-spin': refreshing }">🔄</span>
            {{ refreshing ? '...' : '↻' }}
          </button>
        </div>
        
        <!-- Status Row -->
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2">
            <div :class="[
              'w-2 h-2 rounded-full',
              scannerStatus.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            ]"></div>
            <span class="text-gray-300">
              {{ scannerStatus.is_running ? 'ACTIVO' : 'INACTIVO' }}
            </span>
          </div>
          
          <div class="text-gray-400 font-mono">
            <span v-if="countdownText">{{ countdownText }}</span>
            <span v-else>...</span>
          </div>
          
          <div class="text-xs" :class="readiness.auto_ready ? 'text-green-400' : 'text-red-400'">
            {{ readiness.auto_ready ? 'LISTO' : 'NO LISTO' }}
          </div>
        </div>
        
        <!-- BTC Price Row -->
        <div class="text-center">
          <div class="text-sm text-green-400 font-mono">
            BTC: ${{ currentBtcPrice.toLocaleString() }}
          </div>
        </div>
      </div>
      
      <!-- Desktop Layout -->
      <div class="hidden md:flex items-center justify-between">
        <div class="flex items-center">
          <div class="flex space-x-2 mr-4">
            <div class="w-3 h-3 bg-red-500 rounded-full"></div>
            <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div class="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-white">Bitcoin 30m Scanner Terminal</h3>
            <p class="text-sm text-gray-400">Actividad del scanner en tiempo real</p>
          </div>
        </div>
        
        <div class="flex items-center gap-4">
          <!-- Scanner Status -->
          <div class="flex items-center gap-2">
            <div :class="[
              'w-2 h-2 rounded-full',
              scannerStatus.is_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            ]"></div>
            <span class="text-sm text-gray-300">
              {{ scannerStatus.is_running ? 'ACTIVO' : 'INACTIVO' }}
            </span>
          </div>
          
          <!-- Next Scan Countdown + Readiness -->
          <div class="text-sm text-gray-400 font-mono">
            <span v-if="countdownText">Próximo: {{ countdownText }}</span>
            <span v-else>Calculando...</span>
          </div>
          <div class="text-xs" :class="readiness.auto_ready ? 'text-green-400' : 'text-red-400'">
            {{ readiness.auto_ready ? 'LISTO' : 'NO LISTO' }}
          </div>
          
          <!-- Current BTC Price -->
          <div class="text-sm text-green-400 font-mono">
            BTC: ${{ currentBtcPrice.toLocaleString() }}
          </div>
          
          <button 
            @click="$emit('refresh')"
            :disabled="refreshing"
            class="inline-flex items-center px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
          >
            <span class="mr-2" :class="{ 'animate-spin': refreshing }">🔄</span>
            {{ refreshing ? 'Actualizando...' : 'Actualizar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Terminal Body -->
    <div class="bg-black p-2 md:p-4 font-mono text-xs md:text-sm">
      <!-- Terminal Prompt -->
      <div class="mb-2 text-green-400">
        <span class="text-yellow-400">user@botu-scanner</span>:<span class="text-blue-400">~/bitcoin-30m</span>$ 
        <span class="text-white">tail -f scanner.log</span>
      </div>
      
      <!-- Logs Container -->
      <div class="max-h-64 md:max-h-96 overflow-y-auto overflow-x-auto space-y-1">
        <div v-if="filteredLogs.length === 0" class="text-gray-500 text-center py-8">
          <div class="text-gray-600">No hay logs disponibles</div>
          <div class="text-gray-700 text-xs mt-1">El scanner aún no ha generado actividad</div>
        </div>
        
        <div 
          v-for="log in filteredLogs" 
          :key="`${log.timestamp}-${log.message}`"
          class="flex items-start gap-1 md:gap-2 py-1 min-w-max"
        >
          <!-- Timestamp -->
          <span class="text-gray-500 text-xs flex-shrink-0 whitespace-nowrap">
            {{ formatLogTime(log.timestamp) }}
          </span>
          
          <!-- Log Level Badge -->
          <span 
            class="text-xs font-bold px-1 md:px-2 py-0.5 rounded flex-shrink-0 whitespace-nowrap"
            :class="getTerminalLogLevelClass(log.level)"
          >
            {{ log.level }}
          </span>
          
          <!-- Log Message -->
          <span 
            class="flex-1 break-words whitespace-pre-wrap"
            :class="getTerminalLogTextClass(log.level)"
          >
            {{ log.message }}
          </span>
        </div>
        
        <!-- Auto-scroll indicator -->
        <div v-if="filteredLogs.length > 0" class="text-gray-600 text-xs text-center py-2">
          <span class="animate-pulse">●</span> Live logs - Auto-scrolling
        </div>
      </div>
    </div>

    <!-- Terminal Stats Footer -->
    <div v-if="logs.length > 0" class="bg-gray-800 px-2 md:px-4 py-2 md:py-3 border-t border-gray-700">
      <!-- Mobile Layout -->
      <div class="md:hidden">
        <div class="grid grid-cols-2 gap-2 text-xs text-gray-300 mb-2">
          <div class="flex items-center justify-between">
            <span class="text-green-400">✅ {{ successCount }}</span>
            <span class="text-red-400">❌ {{ errorCount }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-yellow-400">⚠️ {{ warningCount }}</span>
            <span class="text-blue-400">ℹ️ {{ infoCount }}</span>
          </div>
        </div>
        <div class="text-center text-gray-500 text-xs">
          Total: {{ logs.length }} logs
        </div>
      </div>
      
      <!-- Desktop Layout -->
      <div class="hidden md:flex items-center justify-between text-xs text-gray-300">
        <div class="flex items-center gap-6">
          <span class="text-green-400">✅ {{ successCount }} éxitos</span>
          <span class="text-red-400">❌ {{ errorCount }} errores</span>
          <span class="text-yellow-400">⚠️ {{ warningCount }} advertencias</span>
          <span class="text-blue-400">ℹ️ {{ infoCount }} info</span>
        </div>
        <div class="text-gray-500">
          Total: {{ logs.length }} logs
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  refreshing: {
    type: Boolean,
    default: false
  },
  lastRefresh: {
    type: Date,
    default: null
  },
  scannerStatus: {
    type: Object,
    default: () => ({ is_running: false, last_scan: null })
  },
  currentBtcPrice: {
    type: Number,
    default: 0
  },
  scannerStatus: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['refresh'])

// Estado local
const selectedLevel = ref(null)
const nextScanRemaining = ref(null) // segundos
const countdownText = ref('')
let countdownTimer = null
const readiness = computed(() => props.scannerStatus?.auto_trading_readiness || { auto_ready: false, reasons: [] })

// Constantes
const logLevels = ['SUCCESS', 'ERROR', 'WARNING', 'INFO', 'TRADE', 'ALERT']

// Computed properties
const filteredLogs = computed(() => {
  if (!selectedLevel.value) return props.logs.slice().reverse() // Más recientes primero
  
  return props.logs
    .filter(log => log.level === selectedLevel.value)
    .slice()
    .reverse()
})

const noLogsMessage = computed(() => {
  if (selectedLevel.value) {
    return `No hay logs de tipo ${selectedLevel.value}`
  }
  return 'No hay logs disponibles'
})

// Contadores por tipo
const successCount = computed(() => props.logs.filter(log => log.level === 'SUCCESS').length)
const errorCount = computed(() => props.logs.filter(log => log.level === 'ERROR').length)
const warningCount = computed(() => props.logs.filter(log => log.level === 'WARNING').length)
const infoCount = computed(() => props.logs.filter(log => log.level === 'INFO').length)
const tradeCount = computed(() => props.logs.filter(log => log.level === 'TRADE').length)
const alertCount = computed(() => props.logs.filter(log => log.level === 'ALERT').length)

// Computed para el próximo escaneo
const nextScanTime = computed(() => {
  if (!props.scannerStatus.last_scan && !props.scannerStatus.last_scan_time) return null
  const lastStr = props.scannerStatus.last_scan_time || props.scannerStatus.last_scan
  const lastScan = new Date(lastStr)
  const interval = (props.scannerStatus?.config?.scan_interval || 1800) * 1000
  return new Date(lastScan.getTime() + interval)
})

// Countdown helpers
const computeRemainingSeconds = () => {
  try {
    if (!props.scannerStatus?.is_running) return null
    const lastStr = props.scannerStatus.last_scan_time || props.scannerStatus.last_scan
    const intervalSec = props.scannerStatus?.config?.scan_interval || 1800
    if (!lastStr) return null
    const lastMs = new Date(lastStr).getTime()
    const elapsed = Math.max(0, Math.floor((Date.now() - lastMs) / 1000))
    const remaining = Math.max(0, intervalSec - (elapsed % intervalSec))
    return remaining
  } catch (e) {
    return null
  }
}

const formatHMS = (total) => {
  const m = Math.floor(total / 60)
  const s = total % 60
  const mm = `${m.toString().padStart(2, '0')}`
  const ss = `${s.toString().padStart(2, '0')}`
  return `${mm}m ${ss}s`
}

const tickCountdown = () => {
  const rem = computeRemainingSeconds()
  nextScanRemaining.value = rem
  countdownText.value = rem !== null ? formatHMS(rem) : ''
}

watch(() => props.scannerStatus?.last_scan_time, () => {
  tickCountdown()
})

onMounted(() => {
  tickCountdown()
  countdownTimer = setInterval(tickCountdown, 1000)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

// Funciones de utilidad
const getLogCountByLevel = (level) => {
  return props.logs.filter(log => log.level === level).length
}

const getFilterButtonClass = (level) => {
  const isSelected = selectedLevel.value === level
  const baseClasses = 'border transition-colors cursor-pointer'
  
  if (isSelected) {
    const selectedClasses = {
      'SUCCESS': 'bg-green-100 text-green-800 border-green-300',
      'ERROR': 'bg-red-100 text-red-800 border-red-300',
      'WARNING': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'INFO': 'bg-blue-100 text-blue-800 border-blue-300'
    }
    return `${baseClasses} ${selectedClasses[level]}`
  }
  
  return `${baseClasses} bg-white text-slate-600 border-slate-300 hover:bg-slate-50`
}

const getLogRowClass = (level) => {
  const classes = {
    'SUCCESS': 'bg-green-50 border border-green-100',
    'ERROR': 'bg-red-50 border border-red-100',
    'WARNING': 'bg-yellow-50 border border-yellow-100',
    'INFO': 'bg-blue-50 border border-blue-100'
  }
  return classes[level] || 'bg-slate-50 border border-slate-100'
}

const getLogLevelClass = (level) => {
  const classes = {
    'SUCCESS': 'text-green-700',
    'ERROR': 'text-red-700',
    'WARNING': 'text-yellow-700',
    'INFO': 'text-blue-700'
  }
  return classes[level] || 'text-slate-700'
}

const getLogIcon = (level) => {
  const icons = {
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WARNING': '⚠️',
    'INFO': 'ℹ️',
    'TRADE': '💰',
    'ALERT': '🚨'
  }
  return icons[level] || '📝'
}

// Nuevas funciones para el estilo de terminal
const getTerminalLogLevelClass = (level) => {
  const classes = {
    'SUCCESS': 'bg-green-900 text-green-300',
    'ERROR': 'bg-red-900 text-red-300',
    'WARNING': 'bg-yellow-900 text-yellow-300',
    'INFO': 'bg-blue-900 text-blue-300',
    'TRADE': 'bg-purple-900 text-purple-300',
    'ALERT': 'bg-orange-900 text-orange-300'
  }
  return classes[level] || 'bg-gray-800 text-gray-300'
}

const getTerminalLogTextClass = (level) => {
  const classes = {
    'SUCCESS': 'text-green-400',
    'ERROR': 'text-red-400',
    'WARNING': 'text-yellow-400',
    'INFO': 'text-blue-400',
    'TRADE': 'text-purple-400',
    'ALERT': 'text-orange-400'
  }
  return classes[level] || 'text-white'
}

const formatNextScan = (date) => {
  try {
    const now = new Date()
    const diff = date.getTime() - now.getTime()
    
    if (diff <= 0) return 'Ahora'
    
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`
    } else {
      return `${minutes}m`
    }
  } catch (error) {
    return 'Error'
  }
}

const formatLogTime = (timestamp) => {
  try {
    return new Date(timestamp).toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return timestamp
  }
}

const formatRefreshTime = (date) => {
  try {
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return 'Error'
  }
}
</script>