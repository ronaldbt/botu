// useTelegram.js - Composable centralizado para toda la lógica de Telegram
import { ref, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '@/stores/authStore'

export function useTelegram(crypto = 'btc') {
  console.log(`[Telegram ${crypto}] useTelegram: Inicializando composable para ${crypto}`)
  
  // Store
  const authStore = useAuthStore()
  
  // Estado reactivo
  const telegramStatus = ref(null)
  const showQRModal = ref(false)
  const qrConnection = ref(null)
  const generatingQR = ref(false)
  const regeneratingToken = ref(false)
  const tokenTimeLeft = ref(0)
  
  console.log(`[Telegram ${crypto}] useTelegram: Estado inicial:`, {
    telegramStatus: telegramStatus.value,
    showQRModal: showQRModal.value,
    qrConnection: qrConnection.value,
    generatingQR: generatingQR.value,
    regeneratingToken: regeneratingToken.value,
    tokenTimeLeft: tokenTimeLeft.value
  })

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
    try {
      console.log(`[Telegram ${crypto}] fetchTelegramStatus: Haciendo petición a /telegram/status?crypto=${crypto}`)
      const response = await apiClient.get(`/telegram/status?crypto=${crypto}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      console.log(`[Telegram ${crypto}] fetchTelegramStatus: Respuesta recibida:`, response.data)
      telegramStatus.value = response.data
      console.log(`[Telegram ${crypto}] fetchTelegramStatus: Estado actualizado:`, {
        connected: response.data.connected,
        chat_id: response.data.chat_id,
        subscription_status: response.data.subscription_status,
        bot_configured: response.data.bot_configured
      })
      return response.data
    } catch (error) {
      console.error(`[Telegram ${crypto}] fetchTelegramStatus: Error obteniendo estado:`, error)
      telegramStatus.value = {
        connected: false,
        bot_configured: false,
        subscription_status: 'inactive'
      }
      return null
    }
  }

  const generateTelegramConnection = async () => {
    console.log(`[Telegram ${crypto}] generateTelegramConnection: Iniciando...`)
    console.log(`[Telegram ${crypto}] generateTelegramConnection: generatingQR.value antes:`, generatingQR.value)
    generatingQR.value = true
    console.log(`[Telegram ${crypto}] generateTelegramConnection: generatingQR.value después:`, generatingQR.value)
    
    try {
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Haciendo petición a /telegram/connect?crypto=${crypto}`)
      const response = await apiClient.post(`/telegram/connect?crypto=${crypto}`, {}, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Respuesta recibida:`, response.data)
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Datos del QR:`, {
        hasQRCode: !!response.data.qr_code_base64,
        telegramLink: response.data.telegram_link,
        expiresInSeconds: response.data.expires_in_seconds,
        token: response.data.token
      })
      
      qrConnection.value = response.data
      showQRModal.value = true
      console.log(`[Telegram ${crypto}] generateTelegramConnection: set showQRModal=true`)
      console.log(`[Telegram ${crypto}] generateTelegramConnection: qrConnection.value:`, qrConnection.value)
      console.log(`[Telegram ${crypto}] generateTelegramConnection: showQRModal.value:`, showQRModal.value)
      
      // Inicializar contador si tenemos expires_in_seconds
      if (response.data.expires_in_seconds) {
        tokenTimeLeft.value = response.data.expires_in_seconds
        console.log(`[Telegram ${crypto}] generateTelegramConnection: tokenTimeLeft.value establecido:`, tokenTimeLeft.value)
        startTokenCountdown()
      }
      
      // Actualizar estado cada 5 segundos mientras está abierto el modal
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Configurando interval de status check`)
      statusCheckInterval = setInterval(async () => {
        console.log(`[Telegram ${crypto}] generateTelegramConnection: Ejecutando status check interval`)
        const status = await fetchTelegramStatus()
        console.log(`[Telegram ${crypto}] generateTelegramConnection: Status check result:`, status)
        if (telegramStatus.value?.connected) {
          console.log(`[Telegram ${crypto}] generateTelegramConnection: Usuario conectado, cerrando modal`)
          clearInterval(statusCheckInterval)
          closeQRModal()
        }
      }, 5000)
      
      // Limpiar interval después de 10 minutos
      statusCheckTimeout = setTimeout(() => {
        console.log(`[Telegram ${crypto}] generateTelegramConnection: Timeout alcanzado, limpiando interval`)
        if (statusCheckInterval) {
          clearInterval(statusCheckInterval)
          statusCheckInterval = null
        }
      }, 600000)
      
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Función completada exitosamente`)
      return response.data
    } catch (error) {
      console.error(`[Telegram ${crypto}] generateTelegramConnection: Error generando conexión:`, error)
      console.error(`[Telegram ${crypto}] generateTelegramConnection: Error details:`, {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      throw error
    } finally {
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Finally - generatingQR.value antes:`, generatingQR.value)
      generatingQR.value = false
      console.log(`[Telegram ${crypto}] generateTelegramConnection: Finally - generatingQR.value después:`, generatingQR.value)
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
    console.log(`[Telegram ${crypto}] closeQRModal()`)
    showQRModal.value = false
    console.log(`[Telegram ${crypto}] closeQRModal -> showQRModal=`, showQRModal.value)
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