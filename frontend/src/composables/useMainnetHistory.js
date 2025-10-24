import { ref, computed } from 'vue'
import apiClient from '@/config/api'

export function useMainnetHistory() {
  const orders = ref([])
  const loading = ref(false)
  const error = ref(null)
  const total = ref(0)
  const hasMore = ref(false)
  const currentOffset = ref(0)
  const limit = ref(5)
  const systemOnly = ref(false)

  // Computed
  const isEmpty = computed(() => orders.value.length === 0)
  const isLoading = computed(() => loading.value)

  // Methods
  const loadHistory = async (reset = false) => {
    try {
      loading.value = true
      error.value = null

      const offset = reset ? 0 : currentOffset.value
      
      console.log('[useMainnetHistory] Cargando historial:', {
        limit: limit.value,
        offset: offset,
        system_only: systemOnly.value
      })
      
      const url = '/mainnet/history'
      const params = {
        limit: limit.value,
        offset: offset,
        system_only: systemOnly.value
      }
      
      console.log('[useMainnetHistory] URL y parámetros:', { url, params })
      
      const response = await apiClient.get(url, { params })
      
      console.log('[useMainnetHistory] Respuesta recibida:', {
        status: response.status,
        data: response.data
      })

      if (response.data) {
        const newOrders = response.data.orders || []
        
        console.log('[useMainnetHistory] Procesando órdenes:', {
          newOrdersCount: newOrders.length,
          reset: reset,
          currentOrdersCount: orders.value.length
        })
        
        if (reset) {
          orders.value = newOrders
          currentOffset.value = newOrders.length
        } else {
          orders.value = [...orders.value, ...newOrders]
          currentOffset.value += newOrders.length
        }
        
        total.value = response.data.total || 0
        hasMore.value = response.data.has_more || false
        
        console.log('[useMainnetHistory] Estado actualizado:', {
          totalOrders: orders.value.length,
          total: total.value,
          hasMore: hasMore.value
        })
      }
    } catch (err) {
      console.error('[useMainnetHistory] Error cargando historial mainnet:', err)
      console.error('[useMainnetHistory] Error details:', {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        url: err.config?.url
      })
      error.value = err.response?.data?.detail || err.message || 'Error cargando historial'
    } finally {
      loading.value = false
      console.log('[useMainnetHistory] Carga completada, loading:', loading.value)
    }
  }

  const loadMore = async () => {
    if (!hasMore.value || loading.value) return
    await loadHistory(false)
  }

  const refresh = async () => {
    console.log('[useMainnetHistory] Refrescando historial...')
    await loadHistory(true)
  }

  const toggleSystemOnly = async () => {
    console.log('[useMainnetHistory] Cambiando filtro systemOnly:', !systemOnly.value)
    systemOnly.value = !systemOnly.value
    await loadHistory(true)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getStatusColor = (status) => {
    const colors = {
      'FILLED': 'bg-green-100 text-green-800',
      'COMPLETED': 'bg-blue-100 text-blue-800',
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'CANCELLED': 'bg-gray-100 text-gray-800',
      'REJECTED': 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusText = (status) => {
    const texts = {
      'FILLED': 'Ejecutada',
      'COMPLETED': 'Completada',
      'PENDING': 'Pendiente',
      'CANCELLED': 'Cancelada',
      'REJECTED': 'Rechazada'
    }
    return texts[status] || status
  }

  const getTypeText = (side) => {
    return side === 'BUY' ? '📈 BUY' : '📉 SELL'
  }

  const getTypeColor = (side) => {
    return side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  }

  const formatPnL = (pnl) => {
    if (pnl === null || pnl === undefined) return '-'
    const formatted = pnl.toFixed(2)
    return formatted.startsWith('-') ? `-$${formatted.slice(1)}` : `$${formatted}`
  }

  const getPnLColor = (pnl) => {
    if (pnl === null || pnl === undefined) return 'text-slate-400'
    return pnl >= 0 ? 'text-green-600' : 'text-red-600'
  }

  return {
    // State
    orders,
    loading,
    error,
    total,
    hasMore,
    currentOffset,
    limit,
    
    // Computed
    isEmpty,
    isLoading,
    
    // Methods
    loadHistory,
    loadMore,
    refresh,
    toggleSystemOnly,
    formatDate,
    getStatusColor,
    getStatusText,
    getTypeText,
    getTypeColor,
    formatPnL,
    getPnLColor
  }
}
