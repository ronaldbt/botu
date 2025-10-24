<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
    <!-- Debug Info -->
    <div class="p-2 bg-yellow-100 text-xs text-yellow-800 mb-4 rounded">
      DEBUG: MainnetHistory component rendered - orders: {{ orders.length }}, loading: {{ loading }}, total: {{ total }}
    </div>
    
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <h2 class="text-xl font-semibold text-slate-900 flex items-center">
          <span class="text-2xl mr-2">📊</span>
          Historial de Órdenes
        </h2>
        <span class="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full font-medium">💰 MAINNET</span>
      </div>
      <div class="flex items-center space-x-3">
        <span v-if="total > 0" class="text-sm text-slate-500">
          {{ orders.length }} de {{ total }} órdenes
        </span>
        
        <!-- Filtro de sistema -->
        <button 
          @click="toggleSystemOnly" 
          :disabled="loading"
          :class="[
            'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
            systemOnly 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          ]"
        >
          {{ systemOnly ? 'Solo Sistema' : 'Todas las Órdenes' }}
        </button>
        
        <button 
          @click="refresh" 
          :disabled="loading"
          class="text-blue-600 hover:text-blue-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
        >
          <span v-if="loading" class="animate-spin">⟳</span>
          <span v-else>🔄</span>
          <span>Actualizar</span>
        </button>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div class="flex items-center space-x-2">
        <span class="text-red-500">❌</span>
        <span class="text-red-700 text-sm">{{ error }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && orders.length === 0" class="text-center py-8">
      <div class="animate-spin text-4xl text-blue-500 mb-4">⟳</div>
      <p class="text-slate-600">Cargando historial...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="isEmpty && !loading" class="text-center py-8">
      <span class="text-4xl text-slate-300 mb-4 block">📝</span>
      <p class="text-slate-500">No hay órdenes de Mainnet registradas</p>
      <p class="text-xs text-slate-400 mt-2">Debug: orders={{ orders.length }}, total={{ total }}, loading={{ loading }}</p>
    </div>

    <!-- Orders Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-200">
            <th class="text-left py-3 px-2 font-medium text-slate-700">Fecha</th>
            <th class="text-left py-3 px-2 font-medium text-slate-700">Symbol</th>
            <th class="text-left py-3 px-2 font-medium text-slate-700">Tipo</th>
            <th class="text-right py-3 px-2 font-medium text-slate-700">Cantidad</th>
            <th class="text-right py-3 px-2 font-medium text-slate-700">Precio</th>
            <th class="text-right py-3 px-2 font-medium text-slate-700">PnL</th>
            <th class="text-left py-3 px-2 font-medium text-slate-700">Origen</th>
            <th class="text-left py-3 px-2 font-medium text-slate-700">Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id" class="border-b border-slate-100 hover:bg-slate-50">
            <td class="py-3 px-2">{{ formatDate(order.date) }}</td>
            <td class="py-3 px-2 font-mono">
              <span class="flex items-center space-x-1">
                <span class="text-lg">{{ getCryptoIcon(order.symbol) }}</span>
                <span>{{ order.symbol }}</span>
              </span>
            </td>
            <td class="py-3 px-2">
              <span :class="getTypeColor(order.type)" class="px-2 py-1 rounded text-xs font-medium">
                {{ getTypeText(order.type) }}
              </span>
            </td>
            <td class="py-3 px-2 text-right font-mono">{{ order.quantity?.toFixed(8) || '0.00000000' }}</td>
            <td class="py-3 px-2 text-right font-mono">${{ order.price?.toFixed(2) || '0.00' }}</td>
            <td class="py-3 px-2 text-right font-mono">
              <span v-if="order.pnl !== null && order.pnl !== undefined" :class="getPnLColor(order.pnl)">
                {{ formatPnL(order.pnl) }}
              </span>
              <span v-else class="text-slate-400">-</span>
            </td>
            <td class="py-3 px-2">
              <span :class="order.is_system_order ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'" 
                    class="px-2 py-1 rounded text-xs font-medium">
                {{ order.source }}
              </span>
            </td>
            <td class="py-3 px-2">
              <span :class="getStatusColor(order.status)" class="px-2 py-1 rounded text-xs font-medium">
                {{ getStatusText(order.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Load More Button -->
    <div v-if="hasMore && !loading" class="mt-6 text-center">
      <button 
        @click="loadMore"
        class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors shadow-sm hover:shadow-md"
      >
        📄 Cargar más órdenes ({{ total - orders.length }} restantes)
      </button>
    </div>

    <!-- Loading More Indicator -->
    <div v-if="loading && orders.length > 0" class="mt-6 text-center">
      <div class="flex items-center justify-center space-x-2 text-slate-600">
        <div class="animate-spin">⟳</div>
        <span>Cargando más órdenes...</span>
      </div>
    </div>

    <!-- End of List -->
    <div v-if="!hasMore && orders.length > 0" class="mt-6 text-center">
      <div class="flex items-center justify-center space-x-2 text-slate-500">
        <div class="w-8 h-px bg-slate-300"></div>
        <span class="text-sm">✅ Todas las órdenes cargadas</span>
        <div class="w-8 h-px bg-slate-300"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useMainnetHistory } from '@/composables/useMainnetHistory'

// Composable
const {
  orders,
  loading,
  error,
  total,
  hasMore,
  isEmpty,
  loadHistory,
  loadMore,
  refresh,
  formatDate,
  getStatusColor,
  getStatusText,
  getTypeText,
  getTypeColor,
  formatPnL,
  getPnLColor,
  systemOnly,
  toggleSystemOnly
} = useMainnetHistory()

// Debug logs
console.log('[MainnetHistory] Componente inicializado:', {
  orders: orders.value,
  loading: loading.value,
  error: error.value,
  total: total.value,
  hasMore: hasMore.value,
  isEmpty: isEmpty.value
})

// Función para obtener el icono de la criptomoneda
const getCryptoIcon = (symbol) => {
  const icons = {
    'BTCUSDT': '₿',
    'ETHUSDT': 'Ξ',
    'BNBUSDT': '🟡',
    'PAXGUSDT': '🥇'
  }
  return icons[symbol] || '💰'
}

// Infinite scroll
const handleScroll = () => {
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  // Load more when user is near bottom (100px from bottom)
  if (scrollTop + windowHeight >= documentHeight - 100) {
    if (hasMore.value && !loading.value) {
      loadMore()
    }
  }
}

// Lifecycle
onMounted(async () => {
  console.log('[MainnetHistory] Componente montado, cargando historial...')
  console.log('[MainnetHistory] Estado inicial:', {
    orders: orders.value,
    loading: loading.value,
    error: error.value,
    total: total.value
  })
  try {
    await loadHistory(true)
    console.log('[MainnetHistory] loadHistory completado')
  } catch (error) {
    console.error('[MainnetHistory] Error en loadHistory:', error)
  }
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>
