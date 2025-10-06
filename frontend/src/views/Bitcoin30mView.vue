<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
              <span class="text-4xl mr-3">⚡</span>
              Bitcoin 30m Trading
            </h1>
            <p class="text-slate-600">Trading automático de alta frecuencia usando intervalos de 30 minutos (4% TP, 1.5% SL)</p>
          </div>
          
          <!-- Environment Toggle -->
          <div class="mt-4 lg:mt-0">
            <ToggleTestnetMainnet 
              v-model="environment.environment.value"
              @change="handleEnvironmentChange"
            />
          </div>
        </div>
        
        <!-- Strategy Info Banner -->
        <div class="bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div class="flex">
            <div class="flex-shrink-0">
              <span class="text-2xl">⚡</span>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-yellow-800">
                Estrategia Bitcoin 30 Minutos - Alta Frecuencia
              </h3>
              <div class="mt-2 text-sm text-yellow-700">
                <p><strong>Configuración probada:</strong> 4% Take Profit | 1.5% Stop Loss | Max 24h holding | Escaneo cada 30min</p>
                <p><strong>Retorno 2024:</strong> +2,605% vs +120% Buy & Hold | 565 trades | 64.8% win rate</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Warning Banner for Mainnet -->
        <div v-if="environment.isMainnet.value" class="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div class="flex">
            <div class="flex-shrink-0">
              <span class="text-2xl">⚠️</span>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                ADVERTENCIA: Modo MAINNET Activo - Trading 30m
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>Estás operando con <strong>DINERO REAL</strong> en alta frecuencia. El trading de 30m genera más operaciones diarias. Asegúrate de usar solo cantidades que puedas permitirte perder.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bitcoin 30m Status Cards -->
      <Bitcoin30mStatusCards 
        :scanner-status="bitcoin30mScanner.scannerStatus.value"
        :scanner-logs="bitcoin30mScanner.scannerLogs.value"
        :last-scan="bitcoin30mScanner.lastScan.value"
        :environment="environment.getCurrentEnvironment()"
        @start-scanner="handleStartScanner"
        @stop-scanner="handleStopScanner"
        @refresh-status="bitcoin30mScanner.refreshStatus"
      />

      <!-- Scanner Control Panel -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center">
            <span class="text-2xl mr-3">🎛️</span>
            <div>
              <h3 class="text-lg font-semibold text-slate-900">Control del Scanner Bitcoin 30m</h3>
              <p class="text-sm text-slate-600">Gestiona el funcionamiento del scanner automático</p>
            </div>
          </div>
          
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full" :class="bitcoin30mScanner.scannerStatus.value.is_running ? 'bg-green-500' : 'bg-red-500'"></div>
              <span class="text-sm font-medium" :class="bitcoin30mScanner.scannerStatus.value.is_running ? 'text-green-600' : 'text-red-600'">
                {{ bitcoin30mScanner.scannerStatus.value.is_running ? 'Scanner Activo' : 'Scanner Inactivo' }}
              </span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Control Buttons -->
          <div class="space-y-3">
            <h4 class="text-sm font-medium text-slate-700">Acciones</h4>
            <div class="space-y-2">
              <button 
                v-if="!bitcoin30mScanner.scannerStatus.value.is_running"
                @click="handleStartScanner"
                :disabled="startingScanner"
                class="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
              >
                <span v-if="startingScanner" class="animate-spin mr-2">🔄</span>
                <span v-else class="mr-2">▶️</span>
                {{ startingScanner ? 'Iniciando...' : 'Iniciar Scanner' }}
              </button>
              
              <button 
                v-if="bitcoin30mScanner.scannerStatus.value.is_running"
                @click="handleStopScanner"
                :disabled="stoppingScanner"
                class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
              >
                <span v-if="stoppingScanner" class="animate-spin mr-2">🔄</span>
                <span v-else class="mr-2">⏹️</span>
                {{ stoppingScanner ? 'Deteniendo...' : 'Detener Scanner' }}
              </button>
              
              <button 
                @click="bitcoin30mScanner.refreshStatus"
                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
              >
                <span class="mr-2">🔄</span>
                Actualizar Estado
              </button>
            </div>
          </div>

          <!-- Scanner Info -->
          <div class="space-y-3">
            <h4 class="text-sm font-medium text-slate-700">Información</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-slate-500">Alertas enviadas:</span>
                <span class="font-medium">{{ bitcoin30mScanner.scannerStatus.value.alerts_count || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Próximo escaneo:</span>
                <span class="font-medium text-blue-600">{{ nextScanText }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Cooldown:</span>
                <span class="font-medium text-purple-600">{{ cooldownText || 'Listo' }}</span>
              </div>
            </div>
          </div>

          <!-- Configuration -->
          <div class="space-y-3">
            <h4 class="text-sm font-medium text-slate-700">Configuración</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-slate-500">Timeframe:</span>
                <span class="font-medium text-orange-600">30 minutos</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Take Profit:</span>
                <span class="font-medium text-green-600">+4.0%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Stop Loss:</span>
                <span class="font-medium text-red-600">-1.5%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-500">Max Hold:</span>
                <span class="font-medium text-blue-600">24 horas</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Portfolio Balance Section -->
      <Bitcoin30mPortfolio 
        ref="portfolioRef"
        :api-keys="filteredApiKeys"
        :environment="environment.getCurrentEnvironment()"
        @refresh="loadData"
      />

      <!-- Manual Trading Panel removido: sólo automático -->

      <!-- API Keys Section -->
      <ApiKeysSection 
        :api-keys="filteredApiKeys"
        :testing-connection="apiKeys.testingConnection.value"
        :loading-balances="apiKeys.loadingBalances.value"
        :environment="environment.getCurrentEnvironment()"
        @show-help="showApiHelpModal = true"
        @show-add-modal="showAddApiKey = true"
        @test-connection="apiKeys.testConnection"
        @check-balances="apiKeys.checkBalances"
        @edit-api-key="apiKeys.editApiKey"
        @delete-api-key="apiKeys.deleteApiKey"
        @toggle-crypto="apiKeys.toggleCrypto"
      />

      <!-- Trading Orders History (30m specific) -->
      <OrdersHistory 
        :orders="filtered30mOrders"
        :format-date="orders.formatDate"
        :get-status-color="orders.getStatusColor"
        :get-status-text="orders.getStatusText"
        :environment="environment.getCurrentEnvironment()"
        @refresh="orders.loadOrders"
        title="Historial de Órdenes Bitcoin 30m"
      />

      <!-- Scanner Logs Panel (30m specific) -->
      <Bitcoin30mScannerLogs 
        :logs="bitcoin30mScanner.scannerLogs.value"
        :refreshing="bitcoin30mScanner.refreshingLogs.value"
        :last-refresh="bitcoin30mScanner.lastLogsRefresh.value"
        :scanner-status="bitcoin30mScanner.scannerStatus.value"
        :current-btc-price="currentBtcPrice"
        @refresh="bitcoin30mScanner.refreshLogs"
      />
    </div>

    <!-- Add API Key Modal -->
    <ApiKeyModal 
      :show="showAddApiKey"
      :api-key-form="apiKeys.apiKeyForm"
      :submitting-api-key="apiKeys.submittingApiKey.value"
      @close="closeAddApiKeyModal"
      @submit="handleSubmitApiKey"
    />

    <!-- API Help Modal -->
    <ApiHelpModal 
      :show="showApiHelpModal"
      @close="showApiHelpModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../stores/authStore'

// Composables
import { useTradingApiKeys } from '@/composables/useTradingApiKeys'
import { useTradingOrders } from '@/composables/useTradingOrders'  
import { useTradingEnvironment } from '@/composables/useTradingEnvironment'
import { useBitcoin30mScanner } from '@/composables/useBitcoin30mScanner'
import apiClient from '@/config/api'

// Components
import ApiKeysSection from '@/components/trading/ApiKeysSection.vue'
import ApiKeyModal from '@/components/trading/ApiKeyModal.vue'
import ApiHelpModal from '@/components/trading/ApiHelpModal.vue'
import OrdersHistory from '@/components/trading/OrdersHistory.vue'
import ToggleTestnetMainnet from '@/components/trading/ToggleTestnetMainnet.vue'
import Bitcoin30mStatusCards from '@/components/trading/Bitcoin30mStatusCards.vue'
import Bitcoin30mScannerLogs from '@/components/trading/Bitcoin30mScannerLogs.vue'
import Bitcoin30mPortfolio from '@/components/trading/Bitcoin30mPortfolio.vue'
import Bitcoin30mManualTrading from '@/components/trading/Bitcoin30mManualTrading.vue'

// Auth store
const authStore = useAuthStore()

// Composables initialization
const environment = useTradingEnvironment()
const apiKeys = useTradingApiKeys()
const orders = useTradingOrders()
const bitcoin30mScanner = useBitcoin30mScanner()

// Local state
const showAddApiKey = ref(false)
const showApiHelpModal = ref(false)
const startingScanner = ref(false)
const stoppingScanner = ref(false)
const portfolioRef = ref(null)
const currentBtcPrice = ref(122000) // Precio por defecto

// Computed properties para datos filtrados
const filteredApiKeys = computed(() => {
  return environment.filterApiKeysByEnvironment(apiKeys.apiKeys.value)
})

const filtered30mOrders = computed(() => {
  const envFiltered = environment.filterOrdersByEnvironment(orders.orders.value)
  // Filtrar solo órdenes de Bitcoin 30m
  return envFiltered.filter(order => 
    order.crypto_symbol === 'BTC_30m' || 
    (order.ticker === 'BTCUSDT' && order.bot_mode?.includes('30m')) ||
    (order.symbol === 'BTCUSDT' && order.reason === 'MANUAL_TRADE')
  )
})

// Funciones locales
const loadCurrentBtcPrice = async () => {
  try {
    const response = await apiClient.get('/trading/scanner/bitcoin-30m/current-price')
    if (response.data.success) {
      currentBtcPrice.value = response.data.price
      console.log('[Bitcoin30m] Precio BTC actualizado:', currentBtcPrice.value)
    }
  } catch (error) {
    console.error('Error obteniendo precio BTC:', error)
    // Mantener precio por defecto si falla
  }
}

const loadData = async () => {
  console.log('[Bitcoin30m] loadData() inicio')
  try {
    await Promise.all([
      apiKeys.loadApiKeys(),
      orders.loadOrders(),
      bitcoin30mScanner.initializeScanner(),
      loadCurrentBtcPrice()
    ])
    
    // Refresh portfolio balances if component is mounted
    if (portfolioRef.value && portfolioRef.value.refreshBalances) {
      console.log('[Bitcoin30m] Refreshing portfolio balances after trade')
      await portfolioRef.value.refreshBalances()
    } else {
      console.log('[Bitcoin30m] Portfolio ref not ready yet, skipping refresh')
    }
    
    console.log('[Bitcoin30m] loadData() completado')
  } catch (error) {
    console.error('Error cargando datos Bitcoin 30m:', error)
  }
}

const handleEnvironmentChange = (newEnvironment) => {
  console.log('[Bitcoin30m] 🔄 handleEnvironmentChange ejecutado:', newEnvironment)
  console.log('[Bitcoin30m] Ambiente anterior:', environment.environment.value)
  // Los datos se filtran automáticamente por los computed properties
  // Actualizar el formulario de API key para que coincida con el ambiente
  const isTestnet = newEnvironment === 'testnet'
  apiKeys.apiKeyForm.is_testnet = isTestnet
  console.log('[Bitcoin30m] Formulario actualizado - is_testnet:', isTestnet)
  console.log('[Bitcoin30m] Formulario completo:', { ...apiKeys.apiKeyForm })
}

const closeAddApiKeyModal = () => {
  showAddApiKey.value = false
  // Mantener el ambiente seleccionado al cerrar el modal
  apiKeys.resetApiKeyForm()
  apiKeys.apiKeyForm.is_testnet = environment.environment.value === 'testnet'
}

const handleSubmitApiKey = async () => {
  await apiKeys.submitApiKey()
  closeAddApiKeyModal()
}

// Scanner control functions
const handleStartScanner = async () => {
  startingScanner.value = true
  try {
    await bitcoin30mScanner.startScanner()
    // Refresh status after starting
    await bitcoin30mScanner.refreshStatus()
  } catch (error) {
    console.error('Error starting scanner:', error)
  } finally {
    startingScanner.value = false
  }
}

const handleStopScanner = async () => {
  stoppingScanner.value = true
  try {
    await bitcoin30mScanner.stopScanner()
    // Refresh status after stopping
    await bitcoin30mScanner.refreshStatus()
  } catch (error) {
    console.error('Error stopping scanner:', error)
  } finally {
    stoppingScanner.value = false
  }
}

const handleOrderExecuted = (orderInfo) => {
  console.log('[Bitcoin30m] Manual order executed:', orderInfo)
  // Refresh orders and portfolio data after trade execution
  loadData()
}

// Computed properties for scanner info
const nextScanText = computed(() => {
  if (!bitcoin30mScanner.scannerStatus.value.is_running) return 'Scanner inactivo'
  
  const nextScan = bitcoin30mScanner.scannerStatus.value.next_scan_in_seconds
  if (!nextScan) return 'Calculando...'
  
  const minutes = Math.floor(nextScan / 60)
  const seconds = nextScan % 60
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  } else {
    return `${seconds}s`
  }
})

const cooldownText = computed(() => {
  const cooldown = bitcoin30mScanner.scannerStatus.value.cooldown_remaining
  if (!cooldown || cooldown <= 0) return null
  
  const minutes = Math.floor(cooldown / 60)
  const seconds = Math.floor(cooldown % 60)
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  } else {
    return `${seconds}s`
  }
})

// Watcher para sincronizar formulario cuando cambia el ambiente
watch(() => environment.environment.value, (newEnvironment) => {
  console.log('[Bitcoin30m] 🔄 Watcher detectó cambio de ambiente:', newEnvironment)
  const isTestnet = newEnvironment === 'testnet'
  apiKeys.apiKeyForm.is_testnet = isTestnet
  console.log('[Bitcoin30m] Formulario sincronizado - is_testnet:', isTestnet)
}, { immediate: true })

// Lifecycle
onMounted(async () => {
  console.log('[Bitcoin30m] onMounted - usuario:', authStore.user)
  environment.loadEnvironment()
  
  // Sincronizar formulario de API key con el ambiente
  apiKeys.apiKeyForm.is_testnet = environment.environment.value === 'testnet'
  
  // Listener para cambios de ambiente desde el toggle
  window.addEventListener('environmentChanged', (event) => {
    console.log('[Bitcoin30m] 🌐 Evento environmentChanged recibido:', event.detail)
    const { isTestnet } = event.detail
    apiKeys.apiKeyForm.is_testnet = isTestnet
    console.log('[Bitcoin30m] Formulario sincronizado via evento - is_testnet:', isTestnet)
  })
  
  await loadData()
  bitcoin30mScanner.startPolling()
})

onUnmounted(() => {
  bitcoin30mScanner.stopPolling()
})
</script>