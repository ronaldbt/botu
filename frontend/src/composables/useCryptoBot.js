// useCryptoBot.js - Composable centralizado para toda la lógica de crypto bots
import { ref, reactive, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '@/stores/authStore'

export function useCryptoBot(crypto = 'btc') {
  // Store
  const authStore = useAuthStore()
  
  // Configuración dinámica por crypto
  const cryptoConfigs = {
    btc: {
      name: 'Bitcoin',
      displayName: 'Bitcoin ₿',
      symbol: '₿',
      apiBase: '/bitcoin-bot',
      telegramCrypto: 'btc',
      defaultSymbol: 'BTCUSDT',
      colors: {
        primary: 'yellow-600',
        secondary: 'orange-600',
        gradient: 'from-orange-50 to-yellow-50',
        border: 'border-orange-200',
        bg: 'bg-orange-50',
        text: 'text-orange-900'
      },
      emoji: '₿',
      achievements: [
        { label: '2022: +28% vs BTC -65%', bg: 'bg-emerald-100', text: 'text-emerald-800' },
        { label: '2024: +6,530% vs BTC +123%', bg: 'bg-blue-100', text: 'text-blue-800' }
      ]
    },
    eth: {
      name: 'Ethereum',
      displayName: 'Ethereum Ξ',
      symbol: 'Ξ',
      apiBase: '/eth-bot',
      telegramCrypto: 'eth',
      defaultSymbol: 'ETHUSDT',
      colors: {
        primary: 'purple-600',
        secondary: 'blue-600',
        gradient: 'from-blue-50 to-indigo-50',
        border: 'border-blue-200',
        bg: 'bg-purple-50',
        text: 'text-purple-900'
      },
      emoji: '💎',
      achievements: [
        { label: 'ETH Pattern Detection', bg: 'bg-emerald-100', text: 'text-emerald-800' },
        { label: 'ETHUSDT Trading', bg: 'bg-blue-100', text: 'text-blue-800' }
      ]
    },
    bnb: {
      name: 'BNB',
      displayName: 'BNB 🟡',
      symbol: '🟡',
      apiBase: '/bnb-bot',
      telegramCrypto: 'bnb',
      defaultSymbol: 'BNBUSDT',
      colors: {
        primary: 'yellow-600',
        secondary: 'amber-600',
        gradient: 'from-yellow-50 to-amber-50',
        border: 'border-yellow-200',
        bg: 'bg-yellow-50',
        text: 'text-yellow-900'
      },
      emoji: '🪙',
      achievements: [
        { label: 'BNB Smart Chain', bg: 'bg-emerald-100', text: 'text-emerald-800' },
        { label: 'BNBUSDT Trading', bg: 'bg-blue-100', text: 'text-blue-800' }
      ]
    }
  }

  // Obtener configuración actual
  const config = cryptoConfigs[crypto] || cryptoConfigs.btc

  // Estado reactivo
  const selectedMode = ref('manual')
  const loading = ref(false)
  const currentAnalysis = ref(null)
  const alerts = ref([])
  const statistics = ref(null)
  const scannerLogs = ref([])
  
  const botStatus = reactive({
    isRunning: false,
    lastCheck: null,
    mode: null,
    alerts_count: 0
  })

  const botConfig = reactive({
    timeframe: '4h',
    takeProfit: 12.0,
    stopLoss: 5.0,
    tradeAmount: 50,
    maxConcurrentTrades: 1,
    environment: 'testnet',
    apiKey: '',
    secretKey: '',
    symbol: config.defaultSymbol
  })

  const apiStatus = ref(null)
  const testingConnection = ref(false)

  // Intervalos para limpiar
  let statusInterval = null

  // Funciones principales del bot
  const startBot = async () => {
    loading.value = true
    try {
      const response = await apiClient.post(`${config.apiBase}/start`, {
        mode: selectedMode.value,
        config: botConfig
      }, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      botStatus.isRunning = true
      botStatus.mode = selectedMode.value
      botStatus.lastCheck = new Date().toLocaleString()
      
      startPolling()
      
      console.log(`${config.name} Bot iniciado:`, response.data)
      return response.data
    } catch (error) {
      console.error(`Error iniciando ${config.name} Bot:`, error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const stopBot = async () => {
    loading.value = true
    try {
      await apiClient.post(`${config.apiBase}/stop`, {}, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      botStatus.isRunning = false
      botStatus.mode = null
      stopPolling()
      
    } catch (error) {
      console.error(`Error deteniendo ${config.name} Bot:`, error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const refreshStatus = async () => {
    loading.value = true
    try {
      await Promise.all([
        fetchStatus(),
        fetchCurrentAnalysis(),
        fetchAlerts(),
        fetchStatistics(),
        fetchLogs()
      ])
    } catch (error) {
      console.error('Error actualizando estado:', error)
    } finally {
      loading.value = false
    }
  }

  const fetchStatus = async () => {
    try {
      const response = await apiClient.get(`${config.apiBase}/status`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      Object.assign(botStatus, response.data)
    } catch (error) {
      console.error('Error obteniendo estado:', error)
    }
  }

  const fetchCurrentAnalysis = async () => {
    try {
      const response = await apiClient.get(`${config.apiBase}/analysis`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      currentAnalysis.value = response.data
    } catch (error) {
      console.error('Error obteniendo análisis actual:', error)
    }
  }

  const fetchAlerts = async () => {
    try {
      const response = await apiClient.get(`${config.apiBase}/alerts`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      alerts.value = response.data.alerts || []
    } catch (error) {
      console.error('Error obteniendo alertas:', error)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await apiClient.get(`${config.apiBase}/statistics`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      statistics.value = response.data
    } catch (error) {
      console.error('Error obteniendo estadísticas:', error)
    }
  }

  const fetchLogs = async () => {
    try {
      const response = await apiClient.get(`${config.apiBase}/logs`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (response.data.logs) {
        scannerLogs.value = response.data.logs.slice(-50) // Últimos 50 logs
      }
    } catch (error) {
      console.error('Error obteniendo logs del scanner:', error)
    }
  }

  const testApiConnection = async () => {
    testingConnection.value = true
    try {
      const response = await apiClient.post(`${config.apiBase}/test-api`, {
        apiKey: botConfig.apiKey,
        secretKey: botConfig.secretKey,
        environment: botConfig.environment
      }, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      apiStatus.value = response.data
      return response.data
    } catch (error) {
      console.error('Error probando conexión API:', error)
      throw error
    } finally {
      testingConnection.value = false
    }
  }

  // Funciones de polling
  const startPolling = () => {
    stopPolling() // Limpiar cualquier polling previo
    
    statusInterval = setInterval(async () => {
      await refreshStatus()
    }, 30000) // Cada 30 segundos
  }

  const stopPolling = () => {
    if (statusInterval) {
      clearInterval(statusInterval)
      statusInterval = null
    }
  }

  // Funciones de utilidad
  const getStatusText = () => {
    if (botStatus.isRunning) {
      return `${config.name} Bot Activo`
    } else {
      return `${config.name} Bot Detenido`
    }
  }

  const getPatternStateClass = (state) => {
    switch (state?.toLowerCase()) {
      case 'bajando': return 'text-red-600 bg-red-50'
      case 'subiendo': return 'text-emerald-600 bg-emerald-50'
      case 'comprado': return 'text-blue-600 bg-blue-50'
      case 'vendido': return 'text-purple-600 bg-purple-50'
      default: return 'text-slate-600 bg-slate-50'
    }
  }

  const formatLogTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString()
    } catch {
      return timestamp
    }
  }

  const getLogClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'info': return 'bg-blue-50 border-blue-200'
      case 'warning': return 'bg-yellow-50 border-yellow-200'
      case 'error': return 'bg-red-50 border-red-200'
      case 'success': return 'bg-emerald-50 border-emerald-200'
      default: return 'bg-slate-50 border-slate-200'
    }
  }

  const getLogTextClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'info': return 'text-blue-800'
      case 'warning': return 'text-yellow-800'
      case 'error': return 'text-red-800'
      case 'success': return 'text-emerald-800'
      default: return 'text-slate-800'
    }
  }

  const getLogIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'info': return 'ℹ️'
      case 'warning': return '⚠️'
      case 'error': return '❌'
      case 'success': return '✅'
      default: return '📋'
    }
  }

  const formatPrice = (price) => {
    if (!price) return '$0.00'
    return `$${parseFloat(price).toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`
  }

  // Limpiar intervalos al desmontar
  onUnmounted(() => {
    stopPolling()
  })

  // API pública del composable
  return {
    // Configuración
    config,
    
    // Estado reactivo
    selectedMode,
    loading,
    currentAnalysis,
    alerts,
    statistics,
    scannerLogs,
    botStatus,
    botConfig,
    apiStatus,
    testingConnection,
    
    // Métodos principales
    startBot,
    stopBot,
    refreshStatus,
    fetchStatus,
    fetchCurrentAnalysis,
    fetchAlerts,
    fetchStatistics,
    fetchLogs,
    testApiConnection,
    
    // Utilidades
    getStatusText,
    getPatternStateClass,
    formatLogTime,
    getLogClass,
    getLogTextClass,
    getLogIcon,
    formatPrice,
    
    // Control de polling
    startPolling,
    stopPolling
  }
}