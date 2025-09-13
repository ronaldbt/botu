// useTelegram.js - Composable centralizado para toda la lógica de Telegram
import { ref, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '@/stores/authStore'

export function useTelegram(crypto = 'btc') {
  // Store
  const authStore = useAuthStore()
  
  // Estado reactivo
  const telegramStatus = ref(null)
  const showQRModal = ref(false)
  const qrConnection = ref(null)
  const generatingQR = ref(false)
  const regeneratingToken = ref(false)
  const tokenTimeLeft = ref(0)
  
  // Asegurar que el modal no se muestre automáticamente
  const initializeTelegramState = () => {
    showQRModal.value = false
    qrConnection.value = null
    generatingQR.value = false
    regeneratingToken.value = false
    tokenTimeLeft.value = 0
  }

  // Intervalos para limpiar al unmount
  let tokenCountdownInterval = null
  let statusCheckInterval = null
  let statusCheckTimeout = null

  // Mapeo de configuración por crypto
  const cryptoConfig = {
    btc: {
      name: 'Bitcoin',
      symbol: '₿',
      displayName: 'Bitcoin ₿',
      testSymbol: 'BTCUSDT',
      testPrice: 45000
    },
    eth: {
      name: 'Ethereum',
      symbol: 'Ξ',
      displayName: 'Ethereum Ξ',
      testSymbol: 'ETHUSDT',
      testPrice: 2500
    },
    bnb: {
      name: 'BNB',
      symbol: '🟡',
      displayName: 'BNB 🟡',
      testSymbol: 'BNBUSDT',
      testPrice: 300
    }
  }

  // Obtener configuración actual
  const config = cryptoConfig[crypto] || cryptoConfig.btc

  // Funciones principales
  const fetchTelegramStatus = async () => {
    // Asegurar que el modal no se muestre automáticamente
    initializeTelegramState()
    
    try {
      const response = await apiClient.get(`/telegram/status?crypto=${crypto}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      telegramStatus.value = response.data
      return response.data
    } catch (error) {
      console.error(`Error obteniendo estado de Telegram ${crypto}:`, error)
      telegramStatus.value = {
        connected: false,
        bot_configured: false,
        subscription_status: 'inactive'
      }
      return null
    }
  }

  const generateTelegramConnection = async () => {
    generatingQR.value = true
    try {
      const response = await apiClient.post(`/telegram/connect?crypto=${crypto}`, {}, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      qrConnection.value = response.data
      showQRModal.value = true
      
      // Inicializar contador si tenemos expires_in_seconds
      if (response.data.expires_in_seconds) {
        tokenTimeLeft.value = response.data.expires_in_seconds
        startTokenCountdown()
      }
      
      // Actualizar estado cada 5 segundos mientras está abierto el modal
      statusCheckInterval = setInterval(async () => {
        await fetchTelegramStatus()
        if (telegramStatus.value?.connected) {
          clearInterval(statusCheckInterval)
          closeQRModal()
        }
      }, 5000)
      
      // Limpiar interval después de 10 minutos
      statusCheckTimeout = setTimeout(() => {
        if (statusCheckInterval) {
          clearInterval(statusCheckInterval)
          statusCheckInterval = null
        }
      }, 600000)
      
      return response.data
    } catch (error) {
      console.error(`Error generando conexión de Telegram ${crypto}:`, error)
      throw error
    } finally {
      generatingQR.value = false
    }
  }

  const regenerateToken = async () => {
    regeneratingToken.value = true
    try {
      const response = await apiClient.post(`/telegram/regenerate-token?crypto=${crypto}`, {}, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      qrConnection.value = response.data
      
      // Reiniciar contador con el nuevo token
      if (response.data.expires_in_seconds) {
        tokenTimeLeft.value = response.data.expires_in_seconds
        startTokenCountdown()
      }
      
      return response.data
    } catch (error) {
      console.error(`Error regenerando token de Telegram ${crypto}:`, error)
      throw error
    } finally {
      regeneratingToken.value = false
    }
  }

  const disconnectTelegram = async () => {
    try {
      await apiClient.post('/telegram/disconnect', {}, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      await fetchTelegramStatus()
      return true
    } catch (error) {
      console.error(`Error desconectando de Telegram ${crypto}:`, error)
      throw error
    }
  }

  const sendTestAlert = async () => {
    try {
      await apiClient.post('/telegram/send-alert', {
        type: 'INFO',
        symbol: config.testSymbol,
        price: config.testPrice,
        message: `🧪 Esta es una alerta de prueba desde BotU ${config.name}. Si recibes este mensaje, tu conexión funciona correctamente!`
      }, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      return true
    } catch (error) {
      console.error(`Error enviando alerta de prueba ${crypto}:`, error)
      throw error
    }
  }

  const closeQRModal = () => {
    showQRModal.value = false
    qrConnection.value = null
    stopTokenCountdown()
    
    // Limpiar intervalos de status check
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
      statusCheckInterval = null
    }
    if (statusCheckTimeout) {
      clearTimeout(statusCheckTimeout)
      statusCheckTimeout = null
    }
  }

  // Funciones de utilidad para el countdown
  const startTokenCountdown = () => {
    // Limpiar cualquier contador previo
    if (tokenCountdownInterval) {
      clearInterval(tokenCountdownInterval)
    }
    
    tokenCountdownInterval = setInterval(() => {
      if (tokenTimeLeft.value > 0) {
        tokenTimeLeft.value--
      } else {
        clearInterval(tokenCountdownInterval)
        tokenCountdownInterval = null
      }
    }, 1000)
  }

  const stopTokenCountdown = () => {
    if (tokenCountdownInterval) {
      clearInterval(tokenCountdownInterval)
      tokenCountdownInterval = null
    }
    tokenTimeLeft.value = 0
  }

  const formatTimeLeft = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  // Propiedades computadas/helpers
  const isConnected = () => telegramStatus.value?.connected || false
  const isExpired = () => tokenTimeLeft.value <= 0
  const isBotConfigured = () => telegramStatus.value?.bot_configured || false

  // Limpiar intervalos al desmontar
  onUnmounted(() => {
    stopTokenCountdown()
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval)
    }
    if (statusCheckTimeout) {
      clearTimeout(statusCheckTimeout)
    }
  })

  // API pública del composable
  return {
    // Estado reactivo
    telegramStatus,
    showQRModal,
    qrConnection,
    generatingQR,
    regeneratingToken,
    tokenTimeLeft,
    
    // Configuración
    config,
    
    // Métodos principales
    fetchTelegramStatus,
    generateTelegramConnection,
    regenerateToken,
    disconnectTelegram,
    sendTestAlert,
    closeQRModal,
    initializeTelegramState,
    
    // Utilidades
    formatTimeLeft,
    isConnected,
    isExpired,
    isBotConfigured,
    
    // Control de countdown (para casos especiales)
    startTokenCountdown,
    stopTokenCountdown
  }
}