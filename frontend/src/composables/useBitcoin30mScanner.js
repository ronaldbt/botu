import { ref, reactive } from 'vue'
import apiClient from '@/config/api'

export function useBitcoin30mScanner() {
  // Estado reactivo
  const scannerStatus = ref({
    is_running: false,
    config: {},
    last_scan_time: null,
    alerts_count: 0,
    next_scan_in_seconds: null,
    cooldown_remaining: null,
    timeframe: '30m'
  })
  
  const scannerLogs = ref([])
  const lastScan = ref(null)
  const refreshingLogs = ref(false)
  const lastLogsRefresh = ref(null)
  
  // Polling para updates en tiempo real
  let pollingInterval = null
  let logsPollingInterval = null
  
  // Funciones
  const initializeScanner = async () => {
    console.log('[useBitcoin30mScanner] Inicializando scanner 30m...')
    try {
      await refreshStatus()
      await refreshLogs()
    } catch (error) {
      console.error('Error inicializando scanner 30m:', error)
    }
  }
  
  const refreshStatus = async () => {
    try {
      console.log('[useBitcoin30mScanner] GET /trading/scanner/bitcoin-30m/status')
      const response = await apiClient.get('/trading/scanner/bitcoin-30m/status')
      
      if (response.data && response.data.success && response.data.data) {
        scannerStatus.value = {
          ...response.data.data,
          timeframe: '30m'
        }
        lastScan.value = response.data.data.last_scan_time
        
        console.log('[useBitcoin30mScanner] Status actualizado:', {
          is_running: scannerStatus.value.is_running,
          alerts_count: scannerStatus.value.alerts_count,
          last_scan: lastScan.value
        })
      } else {
        console.warn('[useBitcoin30mScanner] Respuesta inválida del servidor:', response.data)
        // En caso de respuesta inválida, mantener estado offline
        scannerStatus.value.is_running = false
      }
    } catch (error) {
      console.error('Error obteniendo status scanner 30m:', error)
      // En caso de error, mantener estado offline
      scannerStatus.value.is_running = false
    }
  }
  
  const refreshLogs = async () => {
    if (refreshingLogs.value) return
    
    refreshingLogs.value = true
    try {
      console.log('[useBitcoin30mScanner] GET /trading/scanner/bitcoin-30m/logs')
      const response = await apiClient.get('/trading/scanner/bitcoin-30m/logs')
      
      if (response.data && Array.isArray(response.data)) {
        scannerLogs.value = response.data.slice(-50) // Últimos 50 logs
        lastLogsRefresh.value = new Date()
        
        console.log('[useBitcoin30mScanner] Logs actualizados:', {
          total_logs: scannerLogs.value.length,
          latest_log: scannerLogs.value[scannerLogs.value.length - 1]?.message
        })
      }
    } catch (error) {
      console.error('Error obteniendo logs scanner 30m:', error)
    } finally {
      refreshingLogs.value = false
    }
  }
  
  const startScanner = async () => {
    try {
      console.log('[useBitcoin30mScanner] POST /trading/scanner/bitcoin-30m/start')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m/start')
      
      if (response.data.success) {
        await refreshStatus()
        alert('✅ Scanner Bitcoin 30m iniciado exitosamente')
      } else {
        alert('❌ Error iniciando scanner 30m: ' + response.data.message)
      }
    } catch (error) {
      console.error('Error iniciando scanner 30m:', error)
      alert('❌ Error iniciando scanner 30m: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const stopScanner = async () => {
    try {
      console.log('[useBitcoin30mScanner] POST /trading/scanner/bitcoin-30m/stop')
      const response = await apiClient.post('/trading/scanner/bitcoin-30m/stop')
      
      if (response.data.success) {
        await refreshStatus()
        alert('⏹️ Scanner Bitcoin 30m detenido exitosamente')
      } else {
        alert('❌ Error deteniendo scanner 30m: ' + response.data.message)
      }
    } catch (error) {
      console.error('Error deteniendo scanner 30m:', error)
      alert('❌ Error deteniendo scanner 30m: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const updateConfig = async (newConfig) => {
    try {
      console.log('[useBitcoin30mScanner] PUT /trading/scanner/bitcoin-30m/config', newConfig)
      const response = await apiClient.put('/trading/scanner/bitcoin-30m/config', newConfig)
      
      if (response.data.success) {
        await refreshStatus()
        alert('✅ Configuración scanner 30m actualizada')
      } else {
        alert('❌ Error actualizando configuración: ' + response.data.message)
      }
    } catch (error) {
      console.error('Error actualizando configuración scanner 30m:', error)
      alert('❌ Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  // Polling functions
  const startPolling = () => {
    console.log('[useBitcoin30mScanner] Iniciando polling...')
    
    // Status polling cada 30 segundos
    pollingInterval = setInterval(refreshStatus, 30000)
    
    // Logs polling cada 15 segundos
    logsPollingInterval = setInterval(refreshLogs, 15000)
  }
  
  const stopPolling = () => {
    console.log('[useBitcoin30mScanner] Deteniendo polling...')
    
    if (pollingInterval) {
      clearInterval(pollingInterval)
      pollingInterval = null
    }
    
    if (logsPollingInterval) {
      clearInterval(logsPollingInterval)
      logsPollingInterval = null
    }
  }
  
  // Utilidades para logs
  const formatLogTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch (error) {
      return timestamp
    }
  }
  
  const getLogTextClass = (level) => {
    const classes = {
      'SUCCESS': 'text-green-700',
      'ERROR': 'text-red-700',
      'WARNING': 'text-yellow-700',
      'INFO': 'text-blue-700'
    }
    return classes[level] || 'text-gray-700'
  }
  
  const getLogIcon = (level) => {
    const icons = {
      'SUCCESS': '✅',
      'ERROR': '❌',
      'WARNING': '⚠️',
      'INFO': 'ℹ️'
    }
    return icons[level] || '📝'
  }
  
  const getCurrentPrice = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/bitcoin-30m/current-price')
      return response.data.price
    } catch (error) {
      console.error('Error obteniendo precio actual:', error)
      return null
    }
  }
  
  const getMarketAnalysis = async () => {
    try {
      const response = await apiClient.get('/trading/scanner/bitcoin-30m/analysis')
      return response.data
    } catch (error) {
      console.error('Error obteniendo análisis de mercado:', error)
      return null
    }
  }
  
  return {
    // Estado
    scannerStatus,
    scannerLogs,
    lastScan,
    refreshingLogs,
    lastLogsRefresh,
    
    // Funciones principales
    initializeScanner,
    refreshStatus,
    refreshLogs,
    startScanner,
    stopScanner,
    updateConfig,
    
    // Polling
    startPolling,
    stopPolling,
    
    // Utilidades
    formatLogTime,
    getLogTextClass,
    getLogIcon,
    getCurrentPrice,
    getMarketAnalysis
  }
}