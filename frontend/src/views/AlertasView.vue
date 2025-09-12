<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
          <span class="text-4xl mr-3">📊</span>
          Trading & Alertas
        </h1>
        <p class="text-slate-600">Resumen completo de operaciones y alertas del sistema</p>
      </div>

      <!-- Trading Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Ganancia Total</h3>
            <span class="text-2xl">💰</span>
          </div>
          <p class="text-2xl font-bold" :class="tradingSummary.total_profit >= 0 ? 'text-green-600' : 'text-red-600'">
            ${{ tradingSummary.total_profit?.toFixed(2) || '0.00' }}
          </p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Operaciones</h3>
            <span class="text-2xl">📈</span>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ tradingSummary.total_operations || 0 }}</p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Tasa de Éxito</h3>
            <span class="text-2xl">🎯</span>
          </div>
          <p class="text-2xl font-bold text-blue-600">{{ tradingSummary.win_rate?.toFixed(1) || '0' }}%</p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Posiciones Abiertas</h3>
            <span class="text-2xl">⏳</span>
          </div>
          <p class="text-2xl font-bold text-amber-600">{{ openPositions.length }}</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6">
        <div class="border-b border-slate-200">
          <nav class="-mb-px flex space-x-8">
            <button
              @click="activeTab = 'operations'"
              :class="activeTab === 'operations' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'"
              class="whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
            >
              📊 Operaciones Cerradas
            </button>
            <button
              @click="activeTab = 'positions'"
              :class="activeTab === 'positions' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'"
              class="whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
            >
              ⏳ Posiciones Abiertas
            </button>
            <button
              @click="activeTab = 'all'"
              :class="activeTab === 'all' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'"
              class="whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm"
            >
              🔔 Todas las Alertas
            </button>
          </nav>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-6 flex flex-wrap gap-4">
        <select 
          v-model="filtro.crypto" 
          @change="loadData"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700"
        >
          <option value="">Todas las criptos</option>
          <option value="BTC">Bitcoin (BTC)</option>
          <option value="ETH">Ethereum (ETH)</option>
          <option value="BNB">Binance Coin (BNB)</option>
        </select>
        
        <select 
          v-if="activeTab === 'all'"
          v-model="filtro.tipo" 
          @change="loadData"
          class="bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700"
        >
          <option value="">Todos los tipos</option>
          <option value="BUY">Compras</option>
          <option value="SELL">Ventas</option>
          <option value="ERROR">Errores</option>
          <option value="INFO">Info</option>
        </select>

        <button 
          @click="loadData" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          🔄 Actualizar
        </button>
      </div>

      <!-- Operations Tab -->
      <div v-if="activeTab === 'operations'" class="space-y-4">
        <div 
          v-for="operation in operations" 
          :key="operation.id"
          class="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-4">
              <div class="w-12 h-12 rounded-lg flex items-center justify-center"
                   :class="operation.profit_usd >= 0 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'">
                <span class="text-xl">{{ operation.profit_usd >= 0 ? '🟢' : '🔴' }}</span>
              </div>
              <div>
                <div class="flex items-center space-x-2 mb-1">
                  <h3 class="text-lg font-semibold text-slate-900">{{ operation.crypto_symbol }}</h3>
                  <span class="bg-slate-100 text-slate-700 px-2 py-1 rounded text-sm">{{ operation.ticker }}</span>
                </div>
                <p class="text-slate-600">{{ operation.mensaje }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm text-slate-500">{{ formatDate(operation.fecha_creacion) }}</p>
              <p v-if="operation.fecha_cierre" class="text-sm text-slate-500">Cerrado: {{ formatDate(operation.fecha_cierre) }}</p>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-slate-50 rounded-lg">
            <div>
              <p class="text-sm text-slate-600">Precio Entrada</p>
              <p class="text-lg font-semibold text-slate-900">${{ operation.precio_entrada?.toFixed(4) || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Precio Salida</p>
              <p class="text-lg font-semibold text-slate-900">${{ operation.precio_salida?.toFixed(4) || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Cantidad</p>
              <p class="text-lg font-semibold text-slate-900">{{ operation.cantidad?.toFixed(6) || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Ganancia USD</p>
              <p class="text-lg font-semibold" :class="operation.profit_usd >= 0 ? 'text-green-600' : 'text-red-600'">
                ${{ operation.profit_usd?.toFixed(2) || '0.00' }}
              </p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Ganancia %</p>
              <p class="text-lg font-semibold" :class="operation.profit_percentage >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ operation.profit_percentage?.toFixed(2) || '0.00' }}%
              </p>
            </div>
          </div>
        </div>

        <div v-if="operations.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl">📊</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay operaciones cerradas</h3>
          <p class="text-slate-600">Las operaciones completadas aparecerán aquí.</p>
        </div>
      </div>

      <!-- Open Positions Tab -->
      <div v-if="activeTab === 'positions'" class="space-y-4">
        <div 
          v-for="position in openPositions" 
          :key="position.id"
          class="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-4">
              <div class="w-12 h-12 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center">
                <span class="text-xl">⏳</span>
              </div>
              <div>
                <div class="flex items-center space-x-2 mb-1">
                  <h3 class="text-lg font-semibold text-slate-900">{{ position.crypto_symbol }}</h3>
                  <span class="bg-slate-100 text-slate-700 px-2 py-1 rounded text-sm">{{ position.ticker }}</span>
                  <span class="bg-amber-100 text-amber-800 px-2 py-1 rounded text-sm">Abierta</span>
                </div>
                <p class="text-slate-600">{{ position.mensaje }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm text-slate-500">{{ formatDate(position.fecha_creacion) }}</p>
              <button 
                @click="showClosePositionModal(position)"
                class="mt-2 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
              >
                Cerrar Posición
              </button>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
            <div>
              <p class="text-sm text-slate-600">Precio Entrada</p>
              <p class="text-lg font-semibold text-slate-900">${{ position.precio_entrada?.toFixed(4) || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Cantidad</p>
              <p class="text-lg font-semibold text-slate-900">{{ position.cantidad?.toFixed(6) || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-sm text-slate-600">Modo</p>
              <p class="text-lg font-semibold text-slate-900">{{ position.bot_mode || 'manual' }}</p>
            </div>
          </div>
        </div>

        <div v-if="openPositions.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl">⏳</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay posiciones abiertas</h3>
          <p class="text-slate-600">Las posiciones abiertas aparecerán aquí.</p>
        </div>
      </div>

      <!-- All Alerts Tab -->
      <div v-if="activeTab === 'all'" class="space-y-4">
        <div 
          v-for="alerta in alertas" 
          :key="alerta.id"
          class="bg-white rounded-lg shadow-sm border border-slate-200 p-6"
          :class="!alerta.leida ? 'border-l-4 border-l-blue-500' : ''"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center space-x-4">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center" 
                   :class="{
                     'bg-green-100 text-green-600': alerta.tipo_alerta === 'BUY',
                     'bg-blue-100 text-blue-600': alerta.tipo_alerta === 'SELL',
                     'bg-red-100 text-red-600': alerta.tipo_alerta === 'ERROR',
                     'bg-slate-100 text-slate-600': alerta.tipo_alerta === 'INFO'
                   }">
                <span class="text-lg">
                  {{ alerta.tipo_alerta === 'BUY' ? '🟢' : 
                     alerta.tipo_alerta === 'SELL' ? '🔴' : 
                     alerta.tipo_alerta === 'ERROR' ? '❌' : 'ℹ️' }}
                </span>
              </div>
              <div>
                <div class="flex items-center space-x-2 mb-1">
                  <span class="font-semibold text-slate-900">{{ alerta.tipo_alerta }}</span>
                  <span class="bg-slate-100 text-slate-700 px-2 py-1 rounded text-sm">{{ alerta.ticker }}</span>
                  <span v-if="!alerta.leida" class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">Nueva</span>
                </div>
                <p class="text-slate-600">{{ alerta.mensaje }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm text-slate-500">{{ formatDate(alerta.fecha_creacion) }}</p>
              <button 
                v-if="!alerta.leida"
                @click="markAsRead(alerta.id)"
                class="mt-1 text-blue-600 hover:text-blue-800 text-sm"
              >
                Marcar como leída
              </button>
            </div>
          </div>
        </div>

        <div v-if="alertas.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span class="text-2xl">🔔</span>
          </div>
          <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay alertas</h3>
          <p class="text-slate-600">Las alertas del sistema aparecerán aquí.</p>
        </div>
      </div>
    </div>

    <!-- Close Position Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-xl font-semibold text-slate-900 mb-4">Cerrar Posición</h3>
        
        <div class="mb-4">
          <p class="text-slate-600 mb-2">Posición: {{ selectedPosition?.crypto_symbol }}</p>
          <p class="text-slate-600 mb-4">Precio de entrada: ${{ selectedPosition?.precio_entrada?.toFixed(4) }}</p>
          
          <label class="block text-sm font-medium text-slate-700 mb-2">Precio de salida</label>
          <input 
            v-model.number="closePositionData.precio_salida"
            type="number"
            step="0.0001"
            class="w-full border border-slate-300 rounded-lg px-3 py-2"
            placeholder="Precio de salida"
          >
        </div>

        <div class="flex justify-end space-x-3">
          <button 
            @click="closeModal"
            class="px-4 py-2 text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button 
            @click="closePosition"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Cerrar Posición
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

const activeTab = ref('operations')
const operations = ref([])
const openPositions = ref([])
const alertas = ref([])
const tradingSummary = ref({})

const filtro = ref({
  crypto: '',
  tipo: ''
})

const showModal = ref(false)
const selectedPosition = ref(null)
const closePositionData = ref({
  precio_salida: null
})

const loadData = async () => {
  try {
    const headers = { 'Authorization': `Bearer ${authStore.token}` }
    
    // Load trading summary
    const summaryResponse = await apiClient.get('/alertas/trading/summary', { 
      headers,
      params: filtro.value.crypto ? { crypto_symbol: filtro.value.crypto } : {}
    })
    tradingSummary.value = summaryResponse.data
    
    // Load operations
    const operationsResponse = await apiClient.get('/alertas/trading/operations', { 
      headers,
      params: filtro.value.crypto ? { crypto_symbol: filtro.value.crypto } : {}
    })
    operations.value = operationsResponse.data
    
    // Load open positions
    const positionsResponse = await apiClient.get('/alertas/trading/open-positions', { 
      headers,
      params: filtro.value.crypto ? { crypto_symbol: filtro.value.crypto } : {}
    })
    openPositions.value = positionsResponse.data
    
    // Load all alerts
    const alertsParams = new URLSearchParams()
    if (filtro.value.tipo) alertsParams.append('tipo_alerta', filtro.value.tipo)
    if (filtro.value.crypto) {
      const ticker = filtro.value.crypto === 'BTC' ? 'BTCUSDT' : 
                     filtro.value.crypto === 'ETH' ? 'ETHUSDT' : 
                     filtro.value.crypto === 'BNB' ? 'BNBUSDT' : ''
      if (ticker) alertsParams.append('ticker', ticker)
    }
    
    const alertsResponse = await apiClient.get(`/alertas/?${alertsParams}`, { headers })
    alertas.value = alertsResponse.data
    
  } catch (error) {
    console.error('Error loading data:', error)
  }
}

const showClosePositionModal = (position) => {
  selectedPosition.value = position
  closePositionData.value.precio_salida = null
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedPosition.value = null
  closePositionData.value = { precio_salida: null }
}

const closePosition = async () => {
  if (!closePositionData.value.precio_salida) {
    alert('Por favor ingresa el precio de salida')
    return
  }

  try {
    await apiClient.post('/alertas/trading/sell', {
      buy_alert_id: selectedPosition.value.id,
      precio_salida: closePositionData.value.precio_salida,
      bot_mode: 'manual'
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })

    alert('Posición cerrada exitosamente')
    closeModal()
    loadData()
  } catch (error) {
    console.error('Error closing position:', error)
    alert('Error cerrando la posición')
  }
}

const markAsRead = async (alertaId) => {
  try {
    await apiClient.put(`/alertas/${alertaId}`, {
      leida: true
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    const alerta = alertas.value.find(a => a.id === alertaId)
    if (alerta) alerta.leida = true
    
  } catch (error) {
    console.error('Error marking as read:', error)
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('es-ES')
}

onMounted(() => {
  loadData()
})
</script>