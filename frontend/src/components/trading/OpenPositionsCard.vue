<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center">
        <span class="text-2xl mr-3">📈</span>
        <div>
          <h3 class="text-lg font-semibold text-slate-900">Posiciones Abiertas</h3>
          <p class="text-sm text-slate-600">Trading automático activo</p>
        </div>
      </div>
      
      <div class="flex items-center gap-3">
        <button 
          @click="refreshPositions"
          :disabled="loading"
          class="inline-flex items-center px-3 py-2 border border-slate-300 shadow-sm text-sm leading-4 font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <span class="mr-2" :class="{ 'animate-spin': loading }">🔄</span>
          {{ loading ? 'Actualizando...' : 'Actualizar' }}
        </button>
      </div>
    </div>

    <div class="space-y-4">
      <div v-if="positions.length === 0" class="text-center py-8 text-slate-500">
        <span class="text-4xl mb-2 block">📊</span>
        <p class="text-sm">No hay posiciones abiertas</p>
        <p class="text-xs text-slate-400 mt-1">El bot puede comprar cuando detecte señales</p>
      </div>
      
      <div 
        v-for="position in positions" 
        :key="position.order_id"
        class="border border-green-200 rounded-lg p-4 bg-green-50"
      >
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center space-x-2">
            <span class="text-green-500">💰</span>
            <span class="font-semibold text-slate-900">Posición BTC</span>
          </div>
          <span class="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
            ABIERTA
          </span>
        </div>
        
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-slate-500">Cantidad:</span>
            <span class="font-medium text-slate-900">{{ position.quantity.toFixed(6) }} BTC</span>
          </div>
          <div>
            <span class="text-slate-500">Precio entrada:</span>
            <span class="font-medium text-slate-900">${{ position.entry_price.toFixed(2) }}</span>
          </div>
          <div>
            <span class="text-slate-500">Total invertido:</span>
            <span class="font-medium text-slate-900">${{ position.total_usdt.toFixed(2) }}</span>
          </div>
          <div>
            <span class="text-slate-500">Fecha:</span>
            <span class="font-medium text-slate-900">{{ formatDate(position.entry_time) }}</span>
          </div>
        </div>
        
        <div class="mt-3 pt-3 border-t border-green-200">
          <div class="flex items-center justify-between text-xs">
            <span class="text-slate-500">Take Profit: +4% | Stop Loss: -1.5%</span>
            <span class="text-green-600 font-medium">Esperando venta automática</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer con estadísticas -->
    <div v-if="positions.length > 0" class="mt-4 pt-4 border-t border-slate-100">
      <div class="grid grid-cols-3 gap-4 text-center">
        <div>
          <p class="text-lg font-semibold text-green-600">{{ positions.length }}</p>
          <p class="text-xs text-slate-500">Posiciones</p>
        </div>
        <div>
          <p class="text-lg font-semibold text-slate-900">${{ totalInvested.toFixed(2) }}</p>
          <p class="text-xs text-slate-500">Total Invertido</p>
        </div>
        <div>
          <p class="text-lg font-semibold text-blue-600">{{ totalBTC.toFixed(6) }}</p>
          <p class="text-xs text-slate-500">BTC Total</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/config/api'

const props = defineProps({
  environment: {
    type: String,
    default: 'mainnet'
  },
  endpoint: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['refresh'])

// Estado
const positions = ref([])
const loading = ref(false)

// Computed
const totalInvested = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.total_usdt, 0)
})

const totalBTC = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.quantity, 0)
})

// Métodos
const loadPositions = async () => {
  try {
    loading.value = true
    const endpoint = props.endpoint || (
      props.environment === 'mainnet' 
        ? '/trading/scanner/bitcoin-30m-mainnet/positions'
        : '/trading/scanner/bitcoin-30m/positions'
    )
      
    const response = await apiClient.get(endpoint)
    
    if (response.data && response.data.success) {
      positions.value = response.data.data.positions || []
      console.log(`[OpenPositionsCard] Posiciones ${props.environment}:`, positions.value)
    }
  } catch (error) {
    console.error(`Error cargando posiciones ${props.environment}:`, error)
  } finally {
    loading.value = false
  }
}

const refreshPositions = async () => {
  await loadPositions()
  emit('refresh')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadPositions()
})

// Exponer métodos
defineExpose({
  loadPositions,
  refreshPositions
})
</script>
