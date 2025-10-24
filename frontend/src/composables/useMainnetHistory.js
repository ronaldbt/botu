import { ref, computed } from 'vue'
import apiClient from '@/config/api'

export function useMainnetHistory() {
  const orders = ref([])
  const loading = ref(false)
  const error = ref(null)
  const total = ref(0)
  const currentPage = ref(1)
  const limit = ref(10) // Máximo 10 órdenes por página
  const systemOnly = ref(false)
  const totalPages = ref(0)

  // Computed
  const isEmpty = computed(() => orders.value.length === 0)
  const isLoading = computed(() => loading.value)
  const hasNextPage = computed(() => currentPage.value < totalPages.value)
  const hasPrevPage = computed(() => currentPage.value > 1)

  // Methods
  const loadHistory = async (page = 1) => {
    try {
      loading.value = true
      error.value = null
      currentPage.value = page

      const offset = (page - 1) * limit.value
      
      console.log('[useMainnetHistory] Cargando historial:', {
        limit: limit.value,
        offset: offset,
        page: page,
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
        orders.value = response.data.orders || []
        total.value = response.data.total || 0
        totalPages.value = Math.ceil(total.value / limit.value)
        
        console.log('[useMainnetHistory] Estado actualizado:', {
          ordersCount: orders.value.length,
          total: total.value,
          currentPage: currentPage.value,
          totalPages: totalPages.value
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

  const nextPage = async () => {
    if (hasNextPage.value && !loading.value) {
      await loadHistory(currentPage.value + 1)
    }
  }

  const prevPage = async () => {
    if (hasPrevPage.value && !loading.value) {
      await loadHistory(currentPage.value - 1)
    }
  }

  const goToPage = async (page) => {
    if (page >= 1 && page <= totalPages.value && !loading.value) {
      await loadHistory(page)
    }
  }

  const refresh = async () => {
    console.log('[useMainnetHistory] Refrescando historial...')
    await loadHistory(currentPage.value)
  }

  const toggleSystemOnly = async () => {
    console.log('[useMainnetHistory] Cambiando filtro systemOnly:', !systemOnly.value)
    systemOnly.value = !systemOnly.value
    await loadHistory(1) // Volver a la primera página
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
    currentPage,
    totalPages,
    systemOnly,
    limit,
    
    // Computed
    isEmpty,
    isLoading,
    hasNextPage,
    hasPrevPage,
    
    // Methods
    loadHistory,
    nextPage,
    prevPage,
    goToPage,
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
