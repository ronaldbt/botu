import { ref, onMounted, onUnmounted } from 'vue'
import apiClient from '@/config/api'

export function useScannerLogs() {
  // Estado reactivo
  const activeScannerTab = ref('btc')
  const btcLogs = ref([])
  const ethLogs = ref([])
  const bnbLogs = ref([])
  const lastLogsRefresh = ref(null)
  const refreshingLogs = ref(false)
  let logsInterval = null

  // Funciones
  const refreshAllScannerLogs = async () => {
    console.log('[useScannerLogs] refreshAllScannerLogs() iniciando...')
    refreshingLogs.value = true
    
    try {
      console.log('[useScannerLogs] Llamando a endpoints de logs...')
      
      const [btcRes, ethRes, bnbRes] = await Promise.all([
        apiClient.get('/bitcoin-bot/logs').catch((err) => {
          console.error('[useScannerLogs] Error en bitcoin-bot/logs:', err)
          return { data: { logs: [] } }
        }),
        apiClient.get('/eth-bot/logs').catch((err) => {
          console.error('[useScannerLogs] Error en eth-bot/logs:', err)
          return { data: { logs: [] } }
        }),
        apiClient.get('/bnb-bot/logs').catch((err) => {
          console.error('[useScannerLogs] Error en bnb-bot/logs:', err)
          return { data: { logs: [] } }
        }),
      ])
      
      console.log('[useScannerLogs] Respuestas recibidas:', {
        btc: btcRes.data,
        eth: ethRes.data, 
        bnb: bnbRes.data
      })
      
      btcLogs.value = btcRes.data?.logs || []
      ethLogs.value = ethRes.data?.logs || []
      bnbLogs.value = bnbRes.data?.logs || []
      lastLogsRefresh.value = Date.now()
      
      console.log('[useScannerLogs] Logs actualizados:', { 
        btc: btcLogs.value.length, 
        eth: ethLogs.value.length, 
        bnb: bnbLogs.value.length,
        timestamp: new Date(lastLogsRefresh.value).toLocaleTimeString()
      })
      
    } catch (e) {
      console.error('[useScannerLogs] Error refrescando logs de scanners:', e)
    } finally {
      refreshingLogs.value = false
      console.log('[useScannerLogs] refreshAllScannerLogs() completado')
    }
  }

  const getActiveLogs = () => {
    if (activeScannerTab.value === 'eth') return ethLogs.value
    if (activeScannerTab.value === 'bnb') return bnbLogs.value
    return btcLogs.value
  }

  const formatLogTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString('es-ES', { hour12: false })
  }

  const getScannerLogTextClass = (level) => {
    switch ((level || '').toLowerCase()) {
      case 'warning': return 'text-yellow-300'
      case 'error': return 'text-red-300'
      case 'success': return 'text-green-300'
      case 'alert': return 'text-purple-300'
      default: return 'text-blue-300'
    }
  }

  const getScannerLogIcon = (level) => {
    switch ((level || '').toLowerCase()) {
      case 'warning': return '⚠️'
      case 'error': return '❌'
      case 'success': return '✅'
      case 'alert': return '🚨'
      default: return 'ℹ️'
    }
  }

  // Inicialización automática
  const initializePolling = () => {
    // Primer fetch de logs y polling cada 30s
    refreshAllScannerLogs()
    logsInterval = setInterval(refreshAllScannerLogs, 30000)
  }

  const cleanupPolling = () => {
    if (logsInterval) {
      clearInterval(logsInterval)
      logsInterval = null
    }
  }

  return {
    // Estado
    activeScannerTab,
    btcLogs,
    ethLogs,
    bnbLogs,
    lastLogsRefresh,
    refreshingLogs,
    
    // Funciones
    refreshAllScannerLogs,
    getActiveLogs,
    formatLogTime,
    getScannerLogTextClass,
    getScannerLogIcon,
    initializePolling,
    cleanupPolling
  }
}