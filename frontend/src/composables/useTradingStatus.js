import { ref } from 'vue'
import apiClient from '@/config/api'

export function useTradingStatus() {
  // Estado reactivo
  const tradingStatus = ref({
    auto_trading_enabled: false,
    active_positions: 0,
    total_orders_today: 0,
    pnl_today_usdt: 0,
    available_balance_usdt: 0
  })

  // Funciones
  const loadTradingStatus = async () => {
    console.log('[useTradingStatus] loadTradingStatus() -> GET /trading/status')
    try {
      const response = await apiClient.get('/trading/status')
      tradingStatus.value = response.data
      console.log('[useTradingStatus] Estado de trading:', tradingStatus.value)
    } catch (error) {
      console.error('Error cargando estado de trading:', error)
    }
  }

  return {
    // Estado
    tradingStatus,
    
    // Funciones
    loadTradingStatus
  }
}