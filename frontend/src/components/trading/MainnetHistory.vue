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

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
      <!-- Page Info -->
      <div class="text-sm text-slate-600">
        Página {{ currentPage }} de {{ totalPages }} ({{ total }} órdenes total)
      </div>
      
      <!-- Navigation Controls -->
      <div class="flex items-center space-x-2">
        <!-- Previous Button -->
        <button 
          @click="prevPage"
          :disabled="!hasPrevPage || loading"
          :class="[
            'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            hasPrevPage && !loading
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          ]"
        >
          ← Anterior
        </button>
        
        <!-- Page Numbers -->
        <div class="flex items-center space-x-1">
          <button 
            v-for="page in getVisiblePages()" 
            :key="page"
            @click="goToPage(page)"
            :disabled="loading"
            :class="[
              'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
            ]"
          >
            {{ page }}
          </button>
        </div>
        
        <!-- Next Button -->
        <button 
          @click="nextPage"
          :disabled="!hasNextPage || loading"
          :class="[
            'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            hasNextPage && !loading
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          ]"
        >
          Siguiente →
        </button>
      </div>
    </div>

    <!-- Loading Indicator -->
    <div v-if="loading" class="mt-6 text-center">
      <div class="flex items-center justify-center space-x-2 text-slate-600">
        <div class="animate-spin">⟳</div>
        <span>Cargando órdenes...</span>
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
  currentPage,
  totalPages,
  hasNextPage,
  hasPrevPage,
  isEmpty,
  loadHistory,
  nextPage,
  prevPage,
  goToPage,
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

// Función para obtener páginas visibles en la paginación
const getVisiblePages = () => {
  const pages = []
  const maxVisible = 5 // Máximo 5 números de página visibles
  
  if (totalPages.value <= maxVisible) {
    // Si hay pocas páginas, mostrar todas
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // Lógica para mostrar páginas con elipsis
    const start = Math.max(1, currentPage.value - 2)
    const end = Math.min(totalPages.value, start + maxVisible - 1)
    
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
  }
  
  return pages
}

// Removed infinite scroll - now using pagination

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
    await loadHistory(1) // Cargar primera página
    console.log('[MainnetHistory] loadHistory completado')
  } catch (error) {
    console.error('[MainnetHistory] Error en loadHistory:', error)
  }
  // Remover infinite scroll ya que usamos paginación
  // window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  // No need to remove scroll listener since we're not using infinite scroll
})
</script>
