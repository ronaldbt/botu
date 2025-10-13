<template>
  <div class="bg-gray-900 rounded-xl shadow-lg border border-gray-700 mb-8">
    <!-- Terminal Header -->
    <div class="px-6 py-4 border-b border-gray-700 bg-gray-800">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <div class="flex space-x-2 mr-4">
            <div class="w-3 h-3 bg-red-500 rounded-full"></div>
            <div class="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div class="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-white">{{ cryptoName }} {{ timeframe}} Scanner Terminal</h3>
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
          
          <!-- Current Price -->
          <div class="text-sm text-green-400 font-mono">
            {{ cryptoSymbol }}: ${{ currentPrice.toLocaleString() }}
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
    <div class="bg-black p-4 font-mono text-sm">
      <!-- Terminal Prompt -->
      <div class="mb-2 text-green-400">
        <span class="text-yellow-400">user@botu-scanner</span>:<span class="text-blue-400">~/{{ cryptoSlug }}</span>$ 
        <span class="text-white">tail -f scanner.log</span>
      </div>
      
      <!-- Logs Container -->
      <div class="max-h-96 overflow-y-auto space-y-1">
        <div v-if="filteredLogs.length === 0" class="text-gray-500 text-center py-8">
          <div class="text-gray-600">No hay logs disponibles</div>
          <div class="text-gray-700 text-xs mt-1">El scanner aún no ha generado actividad</div>
        </div>
        
        <div 
          v-for="log in filteredLogs" 
          :key="`${log.timestamp}-${log.message}`"
          class="flex items-start gap-2 py-1"
        >
          <!-- Timestamp -->
          <span class="text-gray-500 text-xs flex-shrink-0">
            {{ formatLogTime(log.timestamp) }}
          </span>
          
          <!-- Log Level Badge -->
          <span 
            class="text-xs font-bold px-2 py-0.5 rounded flex-shrink-0"
            :class="getTerminalLogLevelClass(log.level)"
          >
            {{ log.level }}
          </span>
          
          <!-- Log Message -->
          <span 
            class="flex-1 break-words"
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
    <div v-if="logs.length > 0" class="bg-gray-800 px-4 py-3 border-t border-gray-700">
      <div class="flex items-center justify-between text-xs text-gray-300">
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
  scannerStatus: {
    type: Object,
    default: () => ({})
  },
  currentPrice: {
    type: Number,
    default: 0
  },
  cryptoName: {
    type: String,
    default: 'Crypto'
  },
  cryptoSymbol: {
    type: String,
    default: 'CRYPTO'
  },
  cryptoSlug: {
    type: String,
    default: 'crypto'
  },
  timeframe: {
    type: String,
    default: '4h'
  }
})

const emit = defineEmits(['refresh'])

// Estado local
const selectedLevel = ref(null)
const nextScanRemaining = ref(null)
const countdownText = ref('')
let countdownTimer = null
const readiness = computed(() => props.scannerStatus?.auto_trading_readiness || { auto_ready: false, reasons: [] })

// Computed properties
const filteredLogs = computed(() => {
  if (!selectedLevel.value) return props.logs.slice().reverse()
  
  return props.logs
    .filter(log => log.level === selectedLevel.value)
    .slice()
    .reverse()
})

// Contadores por tipo
const successCount = computed(() => props.logs.filter(log => log.level === 'SUCCESS').length)
const errorCount = computed(() => props.logs.filter(log => log.level === 'ERROR').length)
const warningCount = computed(() => props.logs.filter(log => log.level === 'WARNING').length)
const infoCount = computed(() => props.logs.filter(log => log.level === 'INFO').length)
const tradeCount = computed(() => props.logs.filter(log => log.level === 'TRADE').length)
const alertCount = computed(() => props.logs.filter(log => log.level === 'ALERT').length)

// Countdown helpers
const computeRemainingSeconds = () => {
  try {
    if (!props.scannerStatus?.is_running) return null
    const lastStr = props.scannerStatus.last_scan_time || props.scannerStatus.last_scan
    const intervalSec = props.scannerStatus?.config?.scan_interval || 3600
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
</script>

