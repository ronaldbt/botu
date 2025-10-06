<template>
  <div class="p-6">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-slate-800 mb-2">Herramientas de Test</h1>
      <p class="text-slate-600">Analiza patrones U históricos de los últimos años para validar la efectividad del bot</p>
    </div>

    <!-- Selección de Ticker -->
    <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <h2 class="text-xl font-semibold text-slate-800 mb-4">Seleccionar Ticker para Backtest</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Selector de Ticker -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Ticker</label>
          <select 
            v-model="selectedTicker" 
            class="w-full bg-white border border-slate-300 rounded-lg px-4 py-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            :disabled="loading"
          >
            <option value="">Selecciona un ticker...</option>
            <option v-for="ticker in availableTickers" :key="ticker.symbol" :value="ticker.symbol">
              {{ ticker.symbol }} - {{ ticker.name || 'Crypto' }}
            </option>
          </select>
        </div>

        <!-- Años hacia atrás -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Años de análisis</label>
          <select 
            v-model="yearsBack" 
            class="w-full bg-white border border-slate-300 rounded-lg px-4 py-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            :disabled="loading"
          >
            <option value="1">1 año</option>
            <option value="2">2 años</option>
            <option value="3">3 años</option>
            <option value="5" selected>5 años</option>
            <option value="7">7 años</option>
            <option value="10">10 años</option>
          </select>
        </div>
      </div>

      <!-- Botón de inicio -->
      <div class="mt-6">
        <button
          @click="startBacktest"
          :disabled="!selectedTicker || loading"
          class="bg-slate-700 hover:bg-slate-600 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="!loading">Iniciar Backtest</span>
          <span v-else class="flex items-center">
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Iniciando...
          </span>
        </button>
      </div>
    </div>

    <!-- Estado del Backtest -->
    <div v-if="backtestStatus" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <h3 class="text-lg font-semibold text-slate-800 mb-4">Estado del Backtest</h3>
      
      <!-- Información del símbolo y progreso -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center">
            <div :class="backtestStatus.is_running ? 'bg-yellow-400' : (backtestStatus.completed ? 'bg-green-400' : 'bg-gray-400')" class="w-3 h-3 rounded-full mr-2"></div>
            <span class="text-slate-700 font-medium">
              {{ backtestStatus.is_running ? 'Ejecutándose' : (backtestStatus.completed ? 'Completado' : 'Inactivo') }}
            </span>
          </div>
          <span class="text-slate-500 text-sm">{{ backtestStatus.progress }}%</span>
        </div>
        
        <!-- Barra de progreso -->
        <div class="w-full bg-slate-200 rounded-full h-2">
          <div 
            class="bg-slate-600 h-2 rounded-full transition-all duration-500 ease-out"
            :style="{ width: `${backtestStatus.progress}%` }"
          ></div>
        </div>
      </div>

      <!-- Estado actual detallado -->
      <div v-if="backtestStatus.current_symbol" class="bg-slate-50 rounded-lg p-3 mb-4">
        <div class="flex items-center">
          <svg v-if="backtestStatus.is_running" class="animate-spin h-4 w-4 text-slate-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="text-slate-700 font-medium">{{ backtestStatus.current_symbol }}</span>
        </div>
      </div>

      <!-- Información de tiempo -->
      <div v-if="backtestStatus.start_time" class="text-sm text-slate-500">
        <span>Iniciado: {{ new Date(backtestStatus.start_time).toLocaleString() }}</span>
      </div>

      <!-- Error si existe -->
      <div v-if="backtestStatus.error" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
        <div class="flex items-center">
          <svg class="h-4 w-4 text-red-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-red-700 text-sm">Error: {{ backtestStatus.error }}</span>
        </div>
      </div>
    </div>

    <!-- Resultados del Backtest -->
    <div v-if="backtestResult" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
      <div class="flex justify-between items-center mb-6">
        <h3 class="text-lg font-semibold text-slate-800">Resultados del Backtest</h3>
        <button
          @click="clearResult"
          class="text-slate-500 hover:text-slate-700 text-sm"
        >
          Limpiar resultado
        </button>
      </div>

      <!-- Estadísticas principales -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-slate-50 rounded-lg p-4">
          <div class="text-2xl font-bold text-slate-800">{{ backtestResult.total_signals }}</div>
          <div class="text-sm text-slate-600">Señales detectadas</div>
        </div>
        
        <div class="bg-slate-50 rounded-lg p-4">
          <div class="text-2xl font-bold text-green-600">{{ backtestResult.successful_signals }}</div>
          <div class="text-sm text-slate-600">Señales exitosas</div>
        </div>
        
        <div class="bg-slate-50 rounded-lg p-4">
          <div class="text-2xl font-bold" :class="getSuccessRateColor(backtestResult.success_rate)">
            {{ backtestResult.success_rate.toFixed(1) }}%
          </div>
          <div class="text-sm text-slate-600">Tasa de éxito</div>
        </div>
        
        <div class="bg-slate-50 rounded-lg p-4">
          <div class="text-2xl font-bold text-slate-800">{{ backtestResult.years_analyzed }}</div>
          <div class="text-sm text-slate-600">Años analizados</div>
        </div>
      </div>

      <!-- Tabla de señales -->
      <div v-if="backtestResult.signals && backtestResult.signals.length > 0">
        <h4 class="text-md font-semibold text-slate-800 mb-4">Señales Detectadas</h4>
        
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Nivel Ruptura</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Precio Actual</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Slope Left</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Éxito</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Ganancia Potencial</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-slate-200">
              <tr v-for="(signal, index) in backtestResult.signals.slice(0, 20)" :key="index" class="hover:bg-slate-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">{{ signal.date }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">{{ signal.rupture_level.toFixed(4) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">{{ signal.current_price.toFixed(4) }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">{{ signal.slope_left.toFixed(6) }}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="signal.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                        class="px-2 py-1 text-xs font-medium rounded-full">
                    {{ signal.success ? 'Sí' : 'No' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm" :class="signal.profit_potential > 0 ? 'text-green-600' : 'text-red-600'">
                  {{ signal.profit_potential.toFixed(2) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="backtestResult.signals.length > 20" class="mt-4 text-center text-slate-600">
          Mostrando las primeras 20 señales de {{ backtestResult.signals.length }} totales
        </div>
      </div>

      <!-- Error -->
      <div v-if="backtestResult.error" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex items-center">
          <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
          <span class="text-red-700">{{ backtestResult.error }}</span>
        </div>
      </div>
    </div>

    <!-- Información adicional -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <h4 class="text-md font-semibold text-blue-800 mb-2">¿Cómo interpretar los resultados?</h4>
      <ul class="text-sm text-blue-700 space-y-1">
        <li>• <strong>Señales detectadas:</strong> Número total de patrones U encontrados en el período</li>
        <li>• <strong>Señales exitosas:</strong> Señales que resultaron en ganancias del 2% o más</li>
        <li>• <strong>Tasa de éxito:</strong> Porcentaje de señales que fueron exitosas</li>
        <li>• <strong>Ganancia potencial:</strong> Ganancia máxima alcanzada después de cada señal</li>
        <li>• <strong>Slope Left:</strong> Pendiente del lado izquierdo del patrón U</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

// Estado reactivo
const availableTickers = ref([])
const selectedTicker = ref('')
const yearsBack = ref(5)
const loading = ref(false)
const backtestStatus = ref(null)
const backtestResult = ref(null)
const statusCheckInterval = ref(null)

// Métodos
const loadTickers = async () => {
  try {
    const response = await apiClient.get('/test-tools/tickers', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    availableTickers.value = response.data
  } catch (error) {
    console.error('Error cargando tickers:', error)
  }
}

const startBacktest = async () => {
  if (!selectedTicker.value) return
  
  loading.value = true
  backtestResult.value = null
  
  try {
    const response = await apiClient.post('/test-tools/backtest/start', {
      symbol: selectedTicker.value,
      years_back: parseInt(yearsBack.value)
    }, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    console.log('Backtest iniciado:', response.data)
    startStatusCheck()
    
  } catch (error) {
    console.error('Error iniciando backtest:', error)
  } finally {
    loading.value = false
  }
}

const startStatusCheck = () => {
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
  }
  
  statusCheckInterval.value = setInterval(async () => {
    try {
      const response = await apiClient.get('/test-tools/backtest/status', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      backtestStatus.value = response.data
      console.log('Status update:', response.data)
      
      // Verificar si completado o hay error
      if (response.data.completed || response.data.error) {
        clearInterval(statusCheckInterval.value)
        backtestResult.value = response.data.results?.[0] || null
        loading.value = false
      }
      
    } catch (error) {
      console.error('Error verificando estado:', error)
      clearInterval(statusCheckInterval.value)
      loading.value = false
    }
  }, 1000) // Verificar cada 1 segundo para mejor feedback
}

// Función removida - ahora obtenemos resultados directamente del status

const clearResult = async () => {
  try {
    await apiClient.delete('/test-tools/backtest/results', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    backtestResult.value = null
    backtestStatus.value = null
  } catch (error) {
    console.error('Error limpiando resultado:', error)
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'running': return 'bg-yellow-400'
    case 'completed': return 'bg-green-400'
    case 'error': return 'bg-red-400'
    default: return 'bg-gray-400'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'running': return 'En progreso'
    case 'completed': return 'Completado'
    case 'error': return 'Error'
    default: return 'No iniciado'
  }
}

const getSuccessRateColor = (rate) => {
  if (rate >= 70) return 'text-green-600'
  if (rate >= 50) return 'text-yellow-600'
  return 'text-red-600'
}

// Lifecycle
onMounted(() => {
  loadTickers()
})

onUnmounted(() => {
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
  }
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>

