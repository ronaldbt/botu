import { ref } from 'vue'
import apiClient from '@/config/api'

export function useTradingOrders() {
  // Estado reactivo
  const orders = ref([])

  // Funciones
  const loadOrders = async () => {
    console.log('[useTradingOrders] loadOrders() -> GET /trading/orders?limit=20')
    try {
      const response = await apiClient.get('/trading/orders?limit=20')
      // El backend devuelve la lista directamente en data (no en data.trades)
      orders.value = Array.isArray(response.data) ? response.data : []
      console.log('[useTradingOrders] Órdenes recibidas:', orders.value.length)
    } catch (error) {
      console.error('Error cargando órdenes:', error)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'FILLED': return 'bg-green-100 text-green-800'
      case 'PENDING': return 'bg-yellow-100 text-yellow-800'
      case 'CANCELLED': return 'bg-slate-100 text-slate-800'
      case 'REJECTED': return 'bg-red-100 text-red-800'
      default: return 'bg-slate-100 text-slate-800'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'FILLED': return '✅ Ejecutada'
      case 'PENDING': return '⏳ Pendiente'
      case 'CANCELLED': return '🚫 Cancelada'
      case 'REJECTED': return '❌ Rechazada'
      default: return status
    }
  }

  return {
    // Estado
    orders,
    
    // Funciones
    loadOrders,
    formatDate,
    getStatusColor,
    getStatusText
  }
}