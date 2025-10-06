import { ref, reactive } from 'vue'
import apiClient from '@/config/api'

export function useBitcoin30mMainnetScanner() {
  // Estado reactivo
  const scannerStatus = ref({
    is_running: false,
    config: {},
    last_scan_time: null,
    alerts_count: 0,
    next_scan_in_seconds: null,
    cooldown_remaining: null,
    timeframe: '30m',
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
    console.log('[useBitcoin30mMainnetScanner] Inicializando scanner 30m Mainnet...')
    try {
      await refreshStatus()
      await refreshLogs()
    } catch (error) {
      console.error('Error inicializando scanner 30m Mainnet:', error)
    }
  }
  
  const refreshStatus = async () => {
    try {
      console.log('[useBitcoin30mMainnetScanner] GET /trading/scanner/bitcoin-30m-mainnet/status')
      const response = await apiClient.get('/trading/scanner/bitcoin-30m-mainnet/status')
      
      if (response.data && response.data.success && response.data.data) {
        const previousScanTime = scannerStatus.value?.last_scan_time || null
        scannerStatus.value = {
          ...response.data.data,
          timeframe: '30m',
          environment: 'mainnet'
        }
        lastScan.value = response.data.data.last_scan_time
        
        // Solo loguear si cambió el last_scan_time o cada >60s
        const now = Date.now()
        if (previousScanTime !== lastScan.value || (now - lastStatusLoggedAt) > 60000) {
          console.log('[useBitcoin30mMainnetScanner] Status actualizado:', {
            is_running: scannerStatus.value.is_running,
            alerts_count: scannerStatus.value.alerts_count,
            last_scan_old: previousScanTime,
            last_scan_new: lastScan.value,
            btc_price: scannerStatus.value.btc_price
          })
          lastStatusLoggedAt = now
        }
        
        // Si cambió el last_scan_time, refrescar logs inmediatamente
        if (previousScanTime !== lastScan.value) {
          console.log('[useBitcoin30mMainnetScanner] 🔄 Detectado nuevo escaneo. Refrescando logs...')
          lastSeenScanTime.value = lastScan.value
          await refreshLogs(true)
        }
      } else {
        console.warn('[useBitcoin30mMainnetScanner] Respuesta inesperada del servidor:', response.data)
      }
    } catch (error) {
      console.error('Error obteniendo estado del scanner 30m Mainnet:', error)
    }
  }
  
  const refreshLogs = async (force = false) => {
    if (refreshingLogs.value) return
    
    try {
      refreshingLogs.value = true
      // cache-busting y telemetry
      const ts = Date.now()
      if (force) {
        console.log('[useBitcoin30mMainnetScanner] GET /trading/scanner/bitcoin-30m-mainnet/logs', { force, ts })
      }
      
      const response = await apiClient.get(`/trading/scanner/bitcoin-30m-mainnet/logs?_ts=${ts}`)
      
      if (response.data && response.data.success && response.data.data) {
        const prevCount = scannerLogs.value.length
        const prevLatest = scannerLogs.value[scannerLogs.value.length - 1]?.timestamp
        scannerLogs.value = response.data.data.logs || []
        lastLogsRefresh.value = new Date().toISOString()
        const newLatest = scannerLogs.value[scannerLogs.value.length - 1]?.timestamp
        const signature = `${response.data.data.total_logs}|${newLatest}`
        if (force || signature !== lastLogsSignature) {
          console.log('[useBitcoin30mMainnetScanner] Logs actualizados:', {
            total_logs: response.data.data.total_logs,
            latest_log: response.data.data.latest_log,
            count_old: prevCount,
            count_new: scannerLogs.value.length,
            latest_old_ts: prevLatest,
            latest_new_ts: newLatest
          })
          lastLogsSignature = signature
        }
      }
    } catch (error) {
      console.error('Error obteniendo logs del scanner 30m Mainnet:', error)
    } finally {
      refreshingLogs.value = false
    }
  }
  
  const startPolling = () => {
    if (pollingInterval) return
    
    console.log('[useBitcoin30mMainnetScanner] Iniciando polling inteligente...')
    
    // Polling inteligente basado en el estado del scanner
    pollingInterval = setInterval(async () => {
      const status = scannerStatus.value
      
      // Si el scanner está activo, verificar cada 2 minutos
      // Si está inactivo, verificar cada 5 minutos
      const interval = status.is_running ? 120000 : 300000
      
      await refreshStatus()
      
      // Reconfigurar el intervalo dinámicamente
      if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = setInterval(async () => {
          await refreshStatus()
        }, interval)
      }
    }, 30000) // Intervalo inicial de 30 segundos
    
    // Logs se actualizan: si cambia el last_scan_time o cada 3 minutos como mínimo
    logsPollingInterval = setInterval(async () => {
      const status = scannerStatus.value
      const logsCount = scannerLogs.value.length
      
      // Solo actualizar logs si hay actividad reciente o si no hay logs
      if (status.is_running || logsCount === 0) {
        await refreshLogs(false)
      }
    }, 180000) // Cada 3 minutos para reducir ruido
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
    
    console.log('[useBitcoin30mMainnetScanner] Polling detenido')
  }
  
  const startScanner = async () => {
    try {
      console.log('[useBitcoin30mMainnetScanner] Iniciando scanner...')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m-mainnet/start')
      
      if (response.data && response.data.success) {
        console.log('Scanner Bitcoin 30m Mainnet iniciado exitosamente')
        await refreshStatus()
        return true
      } else {
        console.error('Error iniciando scanner:', response.data?.message)
        return false
      }
    } catch (error) {
      console.error('Error iniciando scanner 30m Mainnet:', error)
      return false
    }
  }
  
  const stopScanner = async () => {
    try {
      console.log('[useBitcoin30mMainnetScanner] Deteniendo scanner...')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m-mainnet/stop')
      
      if (response.data && response.data.success) {
        console.log('Scanner Bitcoin 30m Mainnet detenido exitosamente')
        // Poll hasta que is_running=false o timeout ~8s
        const start = Date.now()
        while (true) {
          await refreshStatus()
          if (!scannerStatus.value.is_running) break
          if (Date.now() - start > 8000) {
            console.warn('[useBitcoin30mMainnetScanner] Stop timeout: is_running sigue en true')
            break
          }
          await new Promise(r => setTimeout(r, 500))
        }
        return true
      } else {
        console.error('Error deteniendo scanner:', response.data?.message)
        return false
      }
    } catch (error) {
      console.error('Error deteniendo scanner 30m Mainnet:', error)
      return false
    }
  }
  
  const testScan = async () => {
    try {
      console.log('[useBitcoin30mMainnetScanner] Ejecutando escaneo de prueba...')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m-mainnet/test-scan')
      
      if (response.data && response.data.success) {
        console.log('Escaneo de prueba completado exitosamente')
        await refreshStatus()
        await refreshLogs()
        return true
      } else {
        console.error('Error en escaneo de prueba:', response.data?.message)
        return false
      }
    } catch (error) {
      console.error('Error ejecutando escaneo de prueba 30m Mainnet:', error)
      return false
    }
  }

  const forceBuy = async () => {
    try {
      console.log('[useBitcoin30mMainnetScanner] Forzando compra simulada MAINNET...')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m-mainnet/force-buy')
      console.log('[useBitcoin30mMainnetScanner] Respuesta force-buy:', response.data)
      await refreshStatus()
      await refreshLogs(true)
      return !!(response.data && response.data.success)
    } catch (error) {
      console.error('Error forzando compra simulada MAINNET:', error)
      return false
    }
  }
  
  const getConfig = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/bitcoin-30m-mainnet/config')
      
      if (response.data && response.data.success) {
        return response.data.data
      }
      return null
    } catch (error) {
      console.error('Error obteniendo configuración del scanner 30m Mainnet:', error)
      return null
    }
  }
  
  const updateConfig = async (configUpdates) => {
    try {
      const response = await apiClient.put('/trading/scanner/bitcoin-30m-mainnet/config', configUpdates)
      
      if (response.data && response.data.success) {
        console.log('Configuración del scanner 30m Mainnet actualizada')
        await refreshStatus()
        return true
      }
      return false
    } catch (error) {
      console.error('Error actualizando configuración del scanner 30m Mainnet:', error)
      return false
    }
  }
  
  const getAlerts = async (limit = 50) => {
    try {
      const response = await apiClient.get(`/trading/scanner/bitcoin-30m-mainnet/alerts?limit=${limit}`)
      
      if (response.data && response.data.success) {
        return response.data.data
      }
      return null
    } catch (error) {
      console.error('Error obteniendo alertas del scanner 30m Mainnet:', error)
      return null
    }
  }
  
  const getPerformance = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/bitcoin-30m-mainnet/performance')
      
      if (response.data && response.data.success) {
        return response.data.data
      }
      return null
    } catch (error) {
      console.error('Error obteniendo rendimiento del scanner 30m Mainnet:', error)
      return null
    }
  }
  
  const getOpenPositions = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/bitcoin-30m-mainnet/positions')
      
      if (response.data && response.data.success) {
        return response.data.data
      }
      return null
    } catch (error) {
      console.error('Error obteniendo posiciones abiertas 30m Mainnet:', error)
      return null
    }
  }
  
  // Cleanup al desmontar
  const cleanup = () => {
    stopPolling()
  }
  
  return {
    // Estado
    scannerStatus,
    scannerLogs,
    lastScan,
    refreshingLogs,
    lastLogsRefresh,
    
    // Métodos
    initializeScanner,
    refreshStatus,
    refreshLogs,
    startPolling,
    stopPolling,
    startScanner,
    stopScanner,
    testScan,
    forceBuy,
    getConfig,
    updateConfig,
    getAlerts,
    getPerformance,
    getOpenPositions,
    cleanup
  }
}
