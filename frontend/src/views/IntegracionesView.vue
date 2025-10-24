<template>
  <div class="integraciones-view">
    <!-- Mobile Header -->
    <div class="md:hidden bg-gradient-to-r from-slate-900 to-slate-800 text-white p-4 sticky top-0 z-40">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold">🔗 Integraciones</h1>
          <p class="text-slate-300 text-sm">Conexiones y alertas</p>
        </div>
        <button
          @click="refreshStatus"
          :disabled="refreshing"
          class="text-slate-300 hover:text-white disabled:opacity-50"
        >
          <svg class="w-6 h-6" :class="{ 'animate-spin': refreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Desktop Header -->
    <div class="hidden md:block container mx-auto px-4 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">🔗 Integraciones</h1>
        <p class="text-gray-600">Gestiona tus conexiones de Telegram y alertas de trading</p>
      </div>
    </div>

    <!-- Content -->
    <div class="container mx-auto px-4 py-4 md:py-8">
      <!-- Estado de Conexión -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 mb-6 md:mb-8">
        <!-- Telegram Connection Card -->
        <div class="bg-white rounded-lg shadow-md p-4 md:p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg md:text-xl font-semibold text-gray-900">📱 Telegram</h2>
            <div class="flex items-center space-x-2">
              <div :class="[
                'w-3 h-3 rounded-full',
                telegramStatus.connected ? 'bg-green-500' : 'bg-red-500'
              ]"></div>
              <span class="text-xs md:text-sm font-medium">
                {{ telegramStatus.connected ? 'Conectado' : 'Desconectado' }}
              </span>
            </div>
          </div>

          <div v-if="telegramStatus.connected" class="space-y-4">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
              <div class="flex items-center">
                <div class="text-green-600 mr-3">✅</div>
                <div>
                  <p class="text-green-800 font-medium">Conexión activa</p>
                  <p class="text-green-600 text-sm">Chat ID: {{ telegramStatus.chat_id }}</p>
                  <p v-if="telegramStatus.token_expires_at" class="text-green-600 text-sm">
                    Token expira: {{ formatDate(telegramStatus.token_expires_at) }}
                  </p>
                </div>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                @click="disconnectTelegram"
                :disabled="disconnecting"
                class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {{ disconnecting ? 'Desconectando...' : 'Desconectar' }}
              </button>
              <button
                @click="sendTestAlert"
                :disabled="sendingTest"
                class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {{ sendingTest ? 'Enviando...' : 'Probar Alerta' }}
              </button>
            </div>
          </div>

          <div v-else class="space-y-4">
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div class="flex items-center">
                <div class="text-gray-500 mr-3">❌</div>
                <div>
                  <p class="text-gray-700 font-medium">No conectado</p>
                  <p class="text-gray-500 text-sm">Conecta tu cuenta para recibir alertas</p>
                </div>
              </div>
            </div>

            <button
              @click="connectTelegram"
              :disabled="connecting"
              class="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {{ connecting ? 'Conectando...' : 'Conectar Telegram' }}
            </button>
          </div>
        </div>

        <!-- Alert Sender Status Card -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold text-gray-900">📊 Estado del Sistema</h2>
            <button
              @click="refreshStatus"
              :disabled="refreshing"
              class="text-blue-600 hover:text-blue-800 disabled:opacity-50"
            >
              <svg class="w-5 h-5" :class="{ 'animate-spin': refreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div class="grid grid-cols-3 gap-4">
              <div class="bg-blue-50 rounded-lg p-3">
                <div class="text-2xl font-bold text-blue-600">{{ alertSenderStatus.pending_events || 0 }}</div>
                <div class="text-sm text-blue-600">Eventos Pendientes</div>
              </div>
              <div class="bg-green-50 rounded-lg p-3">
                <div class="text-2xl font-bold text-green-600">{{ alertSenderStatus.sent_today || 0 }}</div>
                <div class="text-sm text-green-600">Enviados Hoy</div>
              </div>
              <div class="bg-purple-50 rounded-lg p-3">
                <div class="text-2xl font-bold text-purple-600">{{ alertSenderStatus.connected_users || 0 }}</div>
                <div class="text-sm text-purple-600">Usuarios Conectados</div>
              </div>
            </div>

            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Estado:</span>
                <span :class="[
                  'font-medium',
                  alertSenderStatus.is_running ? 'text-green-600' : 'text-red-600'
                ]">
                  {{ alertSenderStatus.is_running ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Última verificación:</span>
                <span class="text-gray-900">
                  {{ alertSenderStatus.last_check ? formatTime(alertSenderStatus.last_check) : 'Nunca' }}
                </span>
              </div>
            </div>

            <div v-if="alertSenderStatus.errors && alertSenderStatus.errors.length > 0" class="bg-red-50 border border-red-200 rounded-lg p-3">
              <div class="text-red-800 font-medium text-sm mb-2">Últimos errores:</div>
              <div class="space-y-1">
                <div v-for="error in alertSenderStatus.errors.slice(0, 3)" :key="error.id" class="text-red-600 text-xs">
                  {{ error.message }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- QR Modal -->
      <TelegramQRModal
        v-if="showQRModal"
        :show="showQRModal"
        :connection="qrConnection"
        :time-left="tokenTimeLeft"
        :regenerating-token="regeneratingToken"
        crypto-name="Trading"
        @close="closeQRModal"
        @regenerate="regenerateToken"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/config/api'
import TelegramQRModal from '@/components/TelegramQRModal.vue'

// Store
const authStore = useAuthStore()

// Estado reactivo
const telegramStatus = ref({
  connected: false,
  chat_id: null,
  bot_configured: false,
  connection_id: null,
  token_expires_at: null
})

const alertSenderStatus = ref({
  is_running: false,
  last_check: null,
  pending_events: 0,
  sent_today: 0,
  errors: []
})

const showQRModal = ref(false)
const qrConnection = ref(null)
const connecting = ref(false)
const disconnecting = ref(false)
const sendingTest = ref(false)
const refreshing = ref(false)
const regeneratingToken = ref(false)
const tokenTimeLeft = ref(0)

// Intervalos
let statusInterval = null
let tokenCountdownInterval = null

// Lifecycle
onMounted(async () => {
  await refreshStatus()
  await loadAlertSenderStatus()
  
  // Actualizar estado cada 30 segundos
  statusInterval = setInterval(async () => {
    await refreshStatus()
    await loadAlertSenderStatus()
  }, 30000)
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
  if (tokenCountdownInterval) clearInterval(tokenCountdownInterval)
})

// Métodos
const refreshStatus = async () => {
  try {
    refreshing.value = true
    const response = await apiClient.get('/telegram/status-main', {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    telegramStatus.value = response.data
  } catch (error) {
    console.error('Error obteniendo estado:', error)
  } finally {
    refreshing.value = false
  }
}

const loadAlertSenderStatus = async () => {
  try {
    const response = await apiClient.get('/telegram/alert-sender-status', {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    alertSenderStatus.value = response.data
  } catch (error) {
    console.error('Error obteniendo estado AlertSender:', error)
  }
}

const connectTelegram = async () => {
  try {
    connecting.value = true
    const response = await apiClient.post('/telegram/connect-main', {}, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    qrConnection.value = response.data
    showQRModal.value = true
    tokenTimeLeft.value = response.data.expires_in_seconds
    
    // Iniciar countdown
    startTokenCountdown()
    
    // Verificar conexión cada 5 segundos mientras el modal está abierto
    const checkInterval = setInterval(async () => {
      await refreshStatus()
      if (telegramStatus.value.connected) {
        clearInterval(checkInterval)
        showQRModal.value = false
      }
    }, 5000)
    
  } catch (error) {
    console.error('Error conectando Telegram:', error)
    alert('Error conectando Telegram. Intenta nuevamente.')
  } finally {
    connecting.value = false
  }
}

const disconnectTelegram = async () => {
  if (!confirm('¿Estás seguro de que quieres desconectar Telegram?')) return
  
  try {
    disconnecting.value = true
    await apiClient.post('/telegram/disconnect-main', {}, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    await refreshStatus()
  } catch (error) {
    console.error('Error desconectando Telegram:', error)
    alert('Error desconectando Telegram. Intenta nuevamente.')
  } finally {
    disconnecting.value = false
  }
}

const sendTestAlert = async () => {
  try {
    sendingTest.value = true
    await apiClient.post('/telegram/send-test-alert', {
      type: 'INFO',
      symbol: 'BTCUSDT',
      price: 45000,
      message: '🧪 Esta es una alerta de prueba del sistema de notificaciones.'
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    alert('✅ Alerta de prueba enviada correctamente')
  } catch (error) {
    console.error('Error enviando alerta de prueba:', error)
    alert('Error enviando alerta de prueba. Intenta nuevamente.')
  } finally {
    sendingTest.value = false
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  qrConnection.value = null
  if (tokenCountdownInterval) {
    clearInterval(tokenCountdownInterval)
    tokenCountdownInterval = null
  }
}

const regenerateToken = async () => {
  try {
    regeneratingToken.value = true
    const response = await apiClient.post('/telegram/connect-main', {}, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    qrConnection.value = response.data
    tokenTimeLeft.value = response.data.expires_in_seconds
    startTokenCountdown()
  } catch (error) {
    console.error('Error regenerando token:', error)
    alert('Error regenerando token. Intenta nuevamente.')
  } finally {
    regeneratingToken.value = false
  }
}

const startTokenCountdown = () => {
  if (tokenCountdownInterval) clearInterval(tokenCountdownInterval)
  
  tokenCountdownInterval = setInterval(() => {
    if (tokenTimeLeft.value > 0) {
      tokenTimeLeft.value--
    } else {
      clearInterval(tokenCountdownInterval)
      tokenCountdownInterval = null
    }
  }, 1000)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

const formatTime = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleTimeString()
}
</script>

<style scoped>
.integraciones-view {
  min-height: 100vh;
  background-color: #f8fafc;
}
</style>
