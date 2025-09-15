<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
              <span class="text-4xl mr-3">🤖</span>
              Trading Automático
            </h1>
            <p class="text-slate-600">Configura el trading automático usando las mismas estrategias exitosas (8% TP, 3% SL)</p>
          </div>
          
          <!-- Environment Toggle -->
          <div class="mt-4 lg:mt-0">
            <ToggleTestnetMainnet 
              v-model="environment.environment.value"
              @change="handleEnvironmentChange"
            />
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
                ADVERTENCIA: Modo MAINNET Activo
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>Estás operando con <strong>DINERO REAL</strong>. Asegúrate de haber probado exitosamente en Testnet y de usar solo cantidades que puedas permitirte perder.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Status Cards -->
      <TradingStatusCards 
        :trading-status="tradingStatus.tradingStatus.value"
        :get-current-api-key="() => apiKeys.getCurrentApiKey(environment.getCurrentEnvironment())"
        :environment="environment.getCurrentEnvironment()"
        :filtered-api-keys="filteredApiKeys"
      />

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

      <!-- Trading Orders History -->
      <OrdersHistory 
        :orders="filteredOrders"
        :format-date="orders.formatDate"
        :get-status-color="orders.getStatusColor"
        :get-status-text="orders.getStatusText"
        :environment="environment.getCurrentEnvironment()"
        @refresh="orders.loadOrders"
      />

      <!-- Scanner Logs Panel -->
      <ScannerLogs 
        :active-scanner-tab="scannerLogs.activeScannerTab.value"
        :refreshing-logs="scannerLogs.refreshingLogs.value"
        :last-logs-refresh="scannerLogs.lastLogsRefresh.value"
        :get-active-logs="scannerLogs.getActiveLogs"
        :format-log-time="scannerLogs.formatLogTime"
        :get-scanner-log-text-class="scannerLogs.getScannerLogTextClass"
        :get-scanner-log-icon="scannerLogs.getScannerLogIcon"
        @refresh="scannerLogs.refreshAllScannerLogs"
        @update:active-tab="scannerLogs.activeScannerTab.value = $event"
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/authStore'

// Composables
import { useTradingApiKeys } from '@/composables/useTradingApiKeys'
import { useTradingOrders } from '@/composables/useTradingOrders'  
import { useTradingStatus } from '@/composables/useTradingStatus'
import { useScannerLogs } from '@/composables/useScannerLogs'
import { useTradingEnvironment } from '@/composables/useTradingEnvironment'

// Components
import TradingStatusCards from '@/components/trading/TradingStatusCards.vue'
import ApiKeysSection from '@/components/trading/ApiKeysSection.vue'
import ApiKeyModal from '@/components/trading/ApiKeyModal.vue'
import ApiHelpModal from '@/components/trading/ApiHelpModal.vue'
import OrdersHistory from '@/components/trading/OrdersHistory.vue'
import ScannerLogs from '@/components/trading/ScannerLogs.vue'
import ToggleTestnetMainnet from '@/components/trading/ToggleTestnetMainnet.vue'

// Auth store
const authStore = useAuthStore()

// Composables initialization
const environment = useTradingEnvironment()
const apiKeys = useTradingApiKeys()
const orders = useTradingOrders()
const tradingStatus = useTradingStatus()
const scannerLogs = useScannerLogs()

// Local state
const showAddApiKey = ref(false)
const showApiHelpModal = ref(false)

// Computed properties para datos filtrados
const filteredApiKeys = computed(() => {
  return environment.filterApiKeysByEnvironment(apiKeys.apiKeys.value)
})

const filteredOrders = computed(() => {
  return environment.filterOrdersByEnvironment(orders.orders.value)
})

// Funciones locales
const loadData = async () => {
  console.log('[TradingAutomatico] loadData() inicio')
  try {
    await Promise.all([
      apiKeys.loadApiKeys(),
      tradingStatus.loadTradingStatus(),
      orders.loadOrders()
    ])
    console.log('[TradingAutomatico] loadData() completado')
  } catch (error) {
    console.error('Error cargando datos:', error)
  }
}

const handleEnvironmentChange = (newEnvironment) => {
  console.log('[TradingAutomatico] Cambio de ambiente:', newEnvironment)
  // Los datos se filtran automáticamente por los computed properties
}

const closeAddApiKeyModal = () => {
  showAddApiKey.value = false
  apiKeys.resetApiKeyForm()
}

const handleSubmitApiKey = async () => {
  await apiKeys.submitApiKey()
  closeAddApiKeyModal()
}

// Lifecycle
onMounted(async () => {
  console.log('[TradingAutomatico] onMounted - usuario:', authStore.user)
  environment.loadEnvironment()
  await loadData()
  scannerLogs.initializePolling()
})

onUnmounted(() => {
  scannerLogs.cleanupPolling()
})
</script>