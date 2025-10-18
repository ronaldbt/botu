import { ref, reactive } from 'vue'
import apiClient from '@/config/api'

export function usePaxgMainnetScanner() {
  // Estado reactivo
  const scannerStatus = ref({
    is_running: false,
    config: {},
    last_scan_time: null,
    alerts_count: 0,
    next_scan_in_seconds: null,
    cooldown_remaining: null,
    timeframe: '4h',
    environment: 'mainnet'
  })
  
  const scannerLogs = ref([])
  const lastScan = ref(null)
  const lastSeenScanTime = ref(null)
  const refreshingLogs = ref(false)
  const lastLogsRefresh = ref(null)
  // Telemetría mínima para evitar ruido
  let lastStatusLoggedAt = 0
  let lastLogsSignature = ''
  
  // Polling para updates en tiempo real
  let pollingInterval = null
  let logsPollingInterval = null
  
  // Funciones
  const initializeScanner = async () => {
    console.log('[usePaxgMainnetScanner] Inicializando scanner PAXG Mainnet...')
    try {
      await refreshStatus()
      await refreshLogs()
    } catch (error) {
      console.error('Error inicializando scanner PAXG Mainnet:', error)
    }
  }
  
  const refreshStatus = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/paxg-mainnet/status')
      if (response.data.success) {
        const statusData = response.data.data
        
        // Solo loggear cambios significativos
        const now = Date.now()
        if (now - lastStatusLoggedAt > 30000) { // Cada 30 segundos máximo
          console.log('[usePaxgMainnetScanner] Status actualizado:', statusData)
          lastStatusLoggedAt = now
        }
        
        scannerStatus.value = {
          is_running: statusData.is_running || false,
          config: statusData.config || {},
          last_scan_time: statusData.last_scan_time || null,
          alerts_count: statusData.alerts_count || 0,
          next_scan_in_seconds: statusData.next_scan_in_seconds || null,
          cooldown_remaining: statusData.cooldown_remaining || null,
          timeframe: statusData.config?.timeframe || '4h',
          environment: 'mainnet',
          paxg_price: statusData.paxg_price || null,
          auto_trading_readiness: statusData.auto_trading_readiness || {}
        }
        
        // Detectar nuevo escaneo
        if (statusData.last_scan_time && statusData.last_scan_time !== lastSeenScanTime.value) {
          console.log('[usePaxgMainnetScanner] 🔄 Detectado nuevo escaneo. Refrescando logs...')
          lastSeenScanTime.value = statusData.last_scan_time
          await refreshLogs()
        }
        
        return response.data
      }
    } catch (error) {
      console.error('Error obteniendo estado del scanner PAXG Mainnet:', error)
      throw error
    }
  }
  
  const refreshLogs = async (force = false) => {
    if (refreshingLogs.value && !force) return
    
    try {
      refreshingLogs.value = true
      
      const params = new URLSearchParams()
      if (force) {
        params.append('force', 'true')
        params.append('ts', Date.now())
      }
      
      const url = `/trading/scanner/paxg-mainnet/logs${params.toString() ? '?' + params.toString() : ''}`
      console.log('[usePaxgMainnetScanner] GET', url)
      
      const response = await apiClient.get(url)
      
      if (response.data.success) {
        const logsData = response.data.data
        
        // Crear firma de logs para detectar cambios
        const logsSignature = JSON.stringify(logsData.logs?.slice(-5) || [])
        
        if (logsSignature !== lastLogsSignature || force) {
          scannerLogs.value = logsData.logs || []
          lastLogsSignature = logsSignature
          lastLogsRefresh.value = Date.now()
          
          console.log('[usePaxgMainnetScanner] Logs actualizados:', {
            total_logs: logsData.total_logs,
            latest_log: logsData.latest_log?.message || 'No hay logs disponibles',
            count_old: scannerLogs.value.length,
            count_new: logsData.logs?.length || 0,
            latest_old_ts: lastLogsRefresh.value,
            latest_new_ts: logsData.latest_log?.timestamp
          })
        }
      }
    } catch (error) {
      console.error('Error obteniendo logs del scanner PAXG Mainnet:', error)
    } finally {
      refreshingLogs.value = false
    }
  }
  
  const startScanner = async () => {
    try {
      console.log('[usePaxgMainnetScanner] Iniciando scanner...')
      const response = await apiClient.post('/trading/scanner/paxg-mainnet/start')
      
      if (response.data.success) {
        console.log('Scanner PAXG Mainnet iniciado exitosamente')
        await refreshStatus()
        return response.data
      } else {
        throw new Error(response.data.message || 'Error iniciando scanner')
      }
    } catch (error) {
      console.error('Error iniciando scanner PAXG Mainnet:', error)
      throw error
    }
  }
  
  const stopScanner = async () => {
    try {
      console.log('[usePaxgMainnetScanner] Deteniendo scanner...')
      const response = await apiClient.post('/trading/scanner/paxg-mainnet/stop')
      
      if (response.data.success) {
        console.log('Scanner PAXG Mainnet detenido exitosamente')
        await refreshStatus()
        return response.data
      } else {
        throw new Error(response.data.message || 'Error deteniendo scanner')
      }
    } catch (error) {
      console.error('Error deteniendo scanner PAXG Mainnet:', error)
      throw error
    }
  }
  
  const forceBuySignal = async () => {
    try {
      console.log('[usePaxgMainnetScanner] Forzando compra simulada MAINNET...')
      const response = await apiClient.post('/trading/scanner/paxg-mainnet/force-buy')
      
      console.log('[usePaxgMainnetScanner] Respuesta force-buy:', response.data)
      
      // Refrescar estado después de forzar compra
      await refreshStatus()
      
      return response.data
    } catch (error) {
      console.error('Error forzando compra PAXG Mainnet:', error)
      throw error
    }
  }
  
  const getCurrentPrice = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/paxg-mainnet/current-price')
      if (response.data.success) {
        return response.data.price
      }
    } catch (error) {
      console.error('Error obteniendo precio PAXG:', error)
      return null
    }
  }
  
  // Polling automático
  const startPolling = (intervalMs = 30000) => {
    if (pollingInterval) return
    
    pollingInterval = setInterval(async () => {
      try {
        await refreshStatus()
      } catch (error) {
        console.error('Error en polling de status PAXG:', error)
      }
    }, intervalMs)
    
    // Polling de logs más frecuente
    logsPollingInterval = setInterval(async () => {
      try {
        await refreshLogs()
      } catch (error) {
        console.error('Error en polling de logs PAXG:', error)
      }
    }, 10000) // Cada 10 segundos
  }
  
  const stopPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
    if (logsPollingInterval) {
      clearInterval(logsPollingInterval)
      logsPollingInterval = null
    }
  }
  
  // Cleanup al destruir el componente
  const cleanup = () => {
    stopPolling()
  }
  
  return {
    // Estado reactivo
    scannerStatus,
    scannerLogs,
    refreshingLogs,
    
    // Métodos
    initializeScanner,
    refreshStatus,
    refreshLogs,
    startScanner,
    stopScanner,
    forceBuySignal,
    getCurrentPrice,
    startPolling,
    stopPolling,
    cleanup
  }
}
