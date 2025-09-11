<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2">
              BNB Bot U-Pattern
            </h1>
            <p class="text-slate-600 text-base">Sistema avanzado de detección de patrones U para BNB Coin con backtesting probado</p>
            <div class="mt-2 flex items-center space-x-4 text-sm">
              <span class="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full font-semibold">BNB Pattern Detection</span>
              <span class="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full font-semibold">BNBUSDT Trading</span>
            </div>
          </div>
          
          <!-- Status Indicator -->
          <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
            <div class="text-center">
              <div class="flex items-center justify-center mb-2">
                <div :class="botStatus.isRunning ? 'bg-emerald-400' : 'bg-slate-400'" class="w-3 h-3 rounded-full mr-2"></div>
                <span class="font-semibold text-slate-700">
                  {{ getStatusText() }}
                </span>
              </div>
              <div class="text-xs text-slate-500">{{ botStatus.lastCheck || 'Nunca' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mode Selector -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h2 class="text-xl font-semibold text-slate-900 mb-4">Seleccionar Modo de Operación</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Manual Mode -->
          <div class="relative">
            <input type="radio" id="manual" v-model="selectedMode" value="manual" class="sr-only">
            <label for="manual" :class="[
              'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200',
              selectedMode === 'manual' 
                ? 'border-yellow-500 bg-yellow-50 shadow-md' 
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
            <input type="radio" id="automatic" v-model="selectedMode" value="automatic" class="sr-only">
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

      <!-- Configuration Panel -->
      <div v-if="selectedMode" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">
          🪙 Estrategia BNB Optimizada - Modo {{ selectedMode === 'manual' ? 'Manual' : 'Automático' }}
        </h3>
        
        <div class="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <div class="flex items-center mb-2">
            <span class="text-lg mr-2">⚙️</span>
            <h4 class="font-semibold text-slate-800">Parámetros Optimizados por Backtest 2023</h4>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-600">
            <div class="flex items-center">
              <span class="text-yellow-600 font-medium mr-2">Timeframe:</span>
              <span>4 Horas (Optimizado)</span>
            </div>
            <div class="flex items-center">
              <span class="text-green-600 font-medium mr-2">Take Profit:</span>
              <span>8% (Conservador)</span>
            </div>
            <div class="flex items-center">
              <span class="text-red-600 font-medium mr-2">Stop Loss:</span>
              <span>3% (Seguro)</span>
            </div>
          </div>
          <p class="text-xs text-slate-500 mt-2">
            ✨ Los parámetros están preconfigurados según backtests históricos exitosos. Incluye filtros anti-bajistas específicos para BNB.
          </p>
        </div>

        <!-- Telegram Integration (Manual Mode Only) -->
        <div v-if="selectedMode === 'manual'" class="mt-6 pt-6 border-t border-slate-200">
          <div class="bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-6">
            <div class="flex items-center mb-4">
              <div class="text-2xl mr-3">📱</div>
              <div>
                <h4 class="font-semibold text-slate-900">Conexión con Telegram - BNB</h4>
                <p class="text-sm text-slate-600">Recibe alertas de BNB Coin directamente en Telegram</p>
              </div>
            </div>

            <!-- Estado de Conexión -->
            <div v-if="telegramStatus" class="mb-4">
              <div class="flex items-center p-3 rounded-lg" :class="telegramStatus.connected ? 'bg-emerald-100' : 'bg-slate-100'">
                <div class="text-lg mr-2">{{ telegramStatus.connected ? '✅' : '📱' }}</div>
                <div>
                  <div class="font-semibold" :class="telegramStatus.connected ? 'text-emerald-800' : 'text-slate-700'">
                    {{ telegramStatus.connected ? 'Conectado a Telegram BNB' : 'No conectado' }}
                  </div>
                  <div class="text-sm text-slate-600" v-if="telegramStatus.connected">
                    Estado: {{ telegramStatus.subscription_status }} - Las alertas de BNB se enviarán automáticamente
                  </div>
                  <div class="text-sm text-slate-600" v-else>
                    Conecta tu Telegram para recibir alertas de patrones U de BNB Coin
                  </div>
                </div>
              </div>
            </div>

            <!-- Botones de Control -->
            <div class="flex items-center space-x-3">
              <button
                v-if="!telegramStatus?.connected"
                @click="generateTelegramConnection"
                :disabled="generatingQR"
                class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                <span v-if="!generatingQR">Conectar Telegram BNB</span>
                <span v-else class="flex items-center">
                  <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generando...
                </span>
              </button>

              <button
                v-if="telegramStatus?.connected"
                @click="disconnectTelegram"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
              >
                Desconectar
              </button>

              <button
                @click="sendTestAlert"
                :disabled="!telegramStatus?.connected"
                class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
              >
                Enviar Prueba BNB
              </button>
            </div>
          </div>
        </div>

        <!-- Control Buttons - Solo Admin -->
        <div v-if="authStore.isAdmin" class="mt-6">
          <!-- Admin Info -->
          <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
            <div class="flex items-center">
              <div class="text-amber-800 text-lg mr-2">👑</div>
              <div>
                <h4 class="font-semibold text-amber-800">Controles de Administrador</h4>
                <p class="text-sm text-amber-700">Solo tú puedes iniciar/detener el BNB Bot automático</p>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-4">
            <button
              @click="startBot"
              :disabled="loading || botStatus.isRunning"
              :class="[
                'px-6 py-3 rounded-lg font-medium transition-colors duration-200',
                selectedMode === 'manual' 
                  ? 'bg-yellow-600 hover:bg-yellow-700 text-white disabled:bg-slate-400' 
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white disabled:bg-slate-400'
              ]"
            >
              <span v-if="!loading">{{ botStatus.isRunning ? '🤖 BNB Bot Activo - Scanner 4h' : '🚀 Iniciar BNB Bot' }}</span>
              <span v-else class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Iniciando Scanner...
              </span>
            </button>

            <button
              @click="stopBot"
              :disabled="loading || !botStatus.isRunning"
              class="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              ⏹️ Detener Bot
            </button>

            <button
              @click="refreshStatus"
              :disabled="loading"
              class="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              🔄 Actualizar
            </button>
          </div>
        </div>

        <!-- Info para usuarios no admin -->
        <div v-else class="mt-6">
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <div class="text-4xl mb-3">👤</div>
            <h3 class="text-lg font-semibold text-yellow-900 mb-2">Usuario Cliente</h3>
            <p class="text-yellow-700 mb-4">
              El BNB Bot está controlado por el administrador. Tú recibirás las alertas automáticamente en Telegram cuando se detecten patrones U en BNB.
            </p>
            <div class="text-sm text-yellow-600">
              <div><strong>Estado del Bot:</strong> {{ botStatus.isRunning ? '🟢 Activo - Escaneando cada 4h' : '⭕ Inactivo' }}</div>
              <div v-if="botStatus.alerts_count"><strong>Alertas enviadas:</strong> {{ botStatus.alerts_count }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Current Analysis -->
      <div v-if="currentAnalysis" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span class="text-2xl mr-2">📊</span>
          Análisis Actual de BNB Coin
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="text-sm text-gray-600 mb-1">Precio Actual BNB</div>
            <div class="text-2xl font-bold text-gray-900">${{ currentAnalysis.currentPrice?.toLocaleString() }}</div>
          </div>
          
          <div class="bg-yellow-50 rounded-lg p-4">
            <div class="text-sm text-yellow-600 mb-1">Nivel de Ruptura</div>
            <div class="text-2xl font-bold text-yellow-900">
              {{ currentAnalysis.ruptureLevel ? `$${currentAnalysis.ruptureLevel.toLocaleString()}` : '-' }}
            </div>
          </div>
          
          <div class="bg-orange-50 rounded-lg p-4">
            <div class="text-sm text-orange-600 mb-1">Estado Patrón</div>
            <div class="text-lg font-bold" :class="getPatternStateClass(currentAnalysis.state)">
              {{ currentAnalysis.state || 'ANALIZANDO' }}
            </div>
          </div>
          
          <div class="bg-green-50 rounded-lg p-4">
            <div class="text-sm text-green-600 mb-1">Confianza</div>
            <div class="text-2xl font-bold text-green-900">
              {{ currentAnalysis.confidence ? `${currentAnalysis.confidence}%` : '-' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Scanner Logs Panel -->
      <div v-if="botStatus.isRunning" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-gray-900 flex items-center">
            <span class="text-2xl mr-2">📊</span>
            BNB Scanner Logs - Tiempo Real
          </h3>
          <div class="flex items-center space-x-2 text-sm text-gray-600">
            <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Activo</span>
          </div>
        </div>

        <div class="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto" ref="logsContainer">
          <div v-if="scannerLogs.length === 0" class="text-gray-400 text-center py-8">
            Esperando logs del scanner de BNB...
          </div>
          <div v-else>
            <div 
              v-for="(log, index) in scannerLogs" 
              :key="index"
              :class="[
                'mb-2 p-2 rounded border-l-4',
                getLogClass(log.level)
              ]"
            >
              <div class="flex items-start space-x-3">
                <span class="text-gray-400 text-xs">{{ formatLogTime(log.timestamp) }}</span>
                <span :class="getLogTextClass(log.level)">{{ getLogIcon(log.level) }}</span>
                <div class="flex-1">
                  <div :class="getLogTextClass(log.level)">{{ log.message }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 flex justify-between items-center text-sm text-gray-600">
          <div>
            <span v-if="botStatus.alerts_count">Alertas BNB enviadas: <strong>{{ botStatus.alerts_count }}</strong></span>
          </div>
          <button 
            @click="refreshLogs" 
            class="text-yellow-600 hover:text-yellow-800 transition-colors duration-200"
          >
            🔄 Actualizar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

// Reactive data
const selectedMode = ref('manual')
const loading = ref(false)
const currentAnalysis = ref(null)
const scannerLogs = ref([])

// Telegram state
const telegramStatus = ref(null)
const generatingQR = ref(false)

const botStatus = reactive({
  isRunning: false,
  lastCheck: null,
  mode: null,
  alerts_count: 0
})

const config = reactive({
  timeframe: '4h',
  takeProfit: 12.0,
  stopLoss: 5.0,
  symbol: 'BNBUSDT'
})

// Polling interval
let statusInterval = null

// Methods
const startBot = async () => {
  loading.value = true
  try {
    const response = await axios.post('http://localhost:8000/bnb-bot/start', {
      mode: selectedMode.value,
      config: config
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    botStatus.isRunning = true
    botStatus.mode = selectedMode.value
    botStatus.lastCheck = new Date().toLocaleString()
    
    startPolling()
    
    console.log('BNB Bot iniciado:', response.data)
  } catch (error) {
    console.error('Error iniciando BNB Bot:', error)
  } finally {
    loading.value = false
  }
}

const stopBot = async () => {
  loading.value = true
  try {
    await axios.post('http://localhost:8000/bnb-bot/stop', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    botStatus.isRunning = false
    botStatus.mode = null
    stopPolling()
    
  } catch (error) {
    console.error('Error deteniendo BNB Bot:', error)
  } finally {
    loading.value = false
  }
}

const refreshStatus = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchStatus(),
      fetchCurrentAnalysis()
    ])
  } catch (error) {
    console.error('Error actualizando estado:', error)
  } finally {
    loading.value = false
  }
}

const fetchStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/status', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    Object.assign(botStatus, response.data)
  } catch (error) {
    console.error('Error obteniendo estado:', error)
  }
}

const fetchCurrentAnalysis = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/analysis', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    currentAnalysis.value = response.data
  } catch (error) {
    console.error('Error obteniendo análisis:', error)
  }
}

const startPolling = () => {
  if (statusInterval) clearInterval(statusInterval)
  
  statusInterval = setInterval(async () => {
    if (botStatus.isRunning) {
      await Promise.all([
        fetchCurrentAnalysis(),
        refreshLogs()
      ])
    }
  }, 30000) // Cada 30 segundos
}

const stopPolling = () => {
  if (statusInterval) {
    clearInterval(statusInterval)
    statusInterval = null
  }
}

const getStatusText = () => {
  if (!botStatus.isRunning) return 'INACTIVO'
  if (botStatus.mode === 'manual') return 'ACTIVO MANUAL'
  if (botStatus.mode === 'automatic') return 'ACTIVO AUTOMÁTICO'
  return 'ACTIVO'
}

// Helper methods
const getPatternStateClass = (state) => {
  switch (state) {
    case 'RUPTURA': return 'text-green-900'
    case 'U_DETECTADO': return 'text-blue-900'
    case 'PALO_BAJANDO': return 'text-yellow-900'
    case 'POST_RUPTURA': return 'text-purple-900'
    default: return 'text-gray-900'
  }
}

// Telegram functions
const generateTelegramConnection = async () => {
  generatingQR.value = true
  try {
    const response = await axios.post('http://localhost:8000/telegram/connect/bnb', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    console.log('Telegram BNB connection generated:', response.data)
  } catch (error) {
    console.error('Error generando conexión de Telegram BNB:', error)
  } finally {
    generatingQR.value = false
  }
}

const disconnectTelegram = async () => {
  try {
    await axios.post('http://localhost:8000/telegram/disconnect/bnb', {}, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
  } catch (error) {
    console.error('Error desconectando de Telegram BNB:', error)
  }
}

const sendTestAlert = async () => {
  try {
    await axios.post('http://localhost:8000/telegram/send-alert/bnb', {
      type: 'INFO',
      symbol: 'BNBUSDT',
      price: 600,
      message: '🧪 Esta es una alerta de prueba para BNB Coin desde BotU. Si recibes este mensaje, tu conexión BNB funciona correctamente!'
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
  } catch (error) {
    console.error('Error enviando alerta de prueba BNB:', error)
  }
}

// Scanner logs functions
const refreshLogs = async () => {
  try {
    const response = await axios.get('http://localhost:8000/bnb-bot/logs', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (response.data.logs) {
      scannerLogs.value = response.data.logs.slice(-50) // Último 50 logs
    }
  } catch (error) {
    console.error('Error obteniendo logs del scanner BNB:', error)
  }
}

const formatLogTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour12: false })
}

const getLogClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'bg-gray-800 border-yellow-500'
    case 'warning': return 'bg-yellow-900 border-yellow-500'
    case 'error': return 'bg-red-900 border-red-500'
    case 'success': return 'bg-green-900 border-green-500'
    case 'alert': return 'bg-purple-900 border-purple-500'
    default: return 'bg-gray-800 border-gray-500'
  }
}

const getLogTextClass = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'text-yellow-300'
    case 'warning': return 'text-yellow-300'
    case 'error': return 'text-red-300'
    case 'success': return 'text-green-300'
    case 'alert': return 'text-purple-300'
    default: return 'text-gray-300'
  }
}

const getLogIcon = (level) => {
  switch (level?.toLowerCase()) {
    case 'info': return 'ℹ️'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    case 'success': return '✅'
    case 'alert': return '🚨'
    default: return '📋'
  }
}

// Lifecycle
onMounted(() => {
  refreshStatus()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>