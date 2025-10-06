<!-- views/BitcoinTestnetView.vue -->
<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Header -->
    <div class="bg-white shadow-sm border-b border-emerald-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between py-4">
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">🧪</span>
              </div>
              <div>
                <h1 class="text-xl font-bold text-slate-900">Bitcoin 30m Scanner</h1>
                <p class="text-sm text-emerald-600 font-medium">TESTNET - Entorno de Pruebas</p>
              </div>
            </div>
          </div>
          
          <div class="mt-4 lg:mt-0">
            <div class="flex items-center space-x-4">
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <span class="text-sm font-medium text-green-600">
                  {{ bitcoin30mScanner.scannerStatus.value.is_running ? 'Scanner Activo' : 'Scanner Inactivo' }}
                </span>
              </div>
              
              <div class="text-sm text-slate-500">
                Precio BTC: ${{ currentBtcPrice.toLocaleString() }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
        
        <!-- API Keys Section -->
        <div class="bg-white rounded-lg shadow-sm border border-emerald-200">
          <div class="p-6 border-b border-emerald-100">
            <h3 class="text-xl font-semibold text-slate-900 flex items-center">
              <span class="text-emerald-500 mr-3">🧪</span>
              API Keys Testnet
            </h3>
            <p class="text-sm text-slate-600 mt-2">Configura tu API key de Binance Testnet para trading automático</p>
          </div>
          
          <div class="p-6">
            <div v-if="testnetApiKeys.length === 0" class="text-center py-8">
              <div class="text-6xl text-slate-300 mb-4">🔑</div>
              <h4 class="text-lg font-medium text-slate-700 mb-2">No tienes API keys de Testnet configuradas</h4>
              <p class="text-slate-600 mb-6">Agrega tu API key de Binance Testnet para comenzar con el trading automático</p>
              <button
                @click="showAddApiKey = true"
                class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Agregar API Key Testnet
              </button>
            </div>
            
            <div v-else class="space-y-6">
              <div 
                v-for="apiKey in testnetApiKeys" 
                :key="apiKey.id"
                class="border border-emerald-200 rounded-lg p-6 bg-emerald-50/30"
              >
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center space-x-3">
                    <span class="text-2xl text-emerald-500">🧪</span>
                    <div>
                      <h4 class="font-semibold text-slate-900">Testnet API Key</h4>
                      <p class="text-sm text-slate-600">ID: {{ apiKey.id }}</p>
                    </div>
                  </div>
                  <span :class="[
                    'px-3 py-1 rounded-full text-sm font-medium',
                    apiKey.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'
                  ]">
                    {{ apiKey.is_active ? 'ACTIVA' : 'INACTIVA' }}
                  </span>
                </div>
                
                <!-- Bitcoin 30m Configuration -->
                <div class="bg-white rounded-lg p-4 border border-orange-200">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-orange-500 text-lg">₿</span>
                      <span class="font-semibold text-slate-800">Bitcoin 30m Scanner</span>
                    </div>
                    <button
                      @click="toggleBitcoin30m(apiKey)"
                      :class="[
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        apiKey.btc_30m_testnet_enabled 
                          ? 'bg-orange-500 text-white hover:bg-orange-600' 
                          : 'bg-slate-300 text-slate-600 hover:bg-slate-400'
                      ]"
                    >
                      {{ apiKey.btc_30m_testnet_enabled ? 'ACTIVO' : 'INACTIVO' }}
                    </button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-slate-700 mb-2">Cantidad asignada (USDT)</label>
                      <input
                        type="number"
                        :value="apiKey.btc_30m_testnet_allocated_usdt || 0"
                        @change="updateBitcoin30mAllocation(apiKey, $event.target.value)"
                        min="0"
                        step="0.01"
                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                        placeholder="Ej: 50.00"
                      />
                    </div>
                    <div class="flex items-end">
                      <div class="text-sm text-slate-600">
                        <div class="font-medium">Estado actual:</div>
                        <div class="text-orange-600">
                          ${{ (apiKey.btc_30m_testnet_allocated_usdt || 0).toFixed(2) }} USDT asignados
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="flex space-x-3 mt-4">
                  <button
                    @click="testConnection(apiKey)"
                    :disabled="testingConnection === apiKey.id"
                    class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2 px-4 rounded-lg transition-colors font-medium"
                  >
                    {{ testingConnection === apiKey.id ? 'Probando...' : 'Probar Conexión' }}
                  </button>
                  <button
                    @click="deleteApiKey(apiKey.id)"
                    class="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg transition-colors font-medium"
                  >
                    Eliminar API Key
                  </button>
                </div>
              </div>
              
              <div class="text-center pt-4">
                <button
                  @click="showAddApiKey = true"
                  class="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                >
                  + Agregar otra API Key
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Manual Trading -->
        <Bitcoin30mManualTrading
          ref="manualTradingRef"
          :api-keys="testnetApiKeys"
          environment="testnet"
          :current-btc-price="currentBtcPrice"
          @order-executed="handleOrderExecuted"
        />
        
        <!-- Portfolio -->
        <Bitcoin30mPortfolio
          ref="portfolioRef"
          :api-keys="testnetApiKeys"
          environment="testnet"
          :current-btc-price="currentBtcPrice"
        />
        
        <!-- Orders History -->
        <OrdersHistory
          :orders="testnetOrders"
          environment="testnet"
          @refresh="loadData"
        />
        
        <!-- Scanner Logs -->
        <Bitcoin30mScannerLogs
          :logs="bitcoin30mScanner.scannerLogs.value"
          :is-refreshing="bitcoin30mScanner.refreshingLogs.value"
          @refresh="bitcoin30mScanner.refreshLogs"
        />
      </div>
    </div>

    <!-- Add API Key Modal -->
    <ApiKeyModal
      v-if="showAddApiKey"
      :show="showAddApiKey"
      :api-key-form="apiKeyForm"
      :is-submitting="submittingApiKey"
      environment="testnet"
      @close="closeAddApiKeyModal"
      @submit="handleSubmitApiKey"
    />

    <ApiHelpModal
      v-if="showApiHelpModal"
      :show="showApiHelpModal"
      @close="showApiHelpModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useAuthStore } from '../stores/authStore'

// Composables
import { useTradingApiKeys } from '@/composables/useTradingApiKeys'
import { useTradingOrders } from '@/composables/useTradingOrders'  
import { useBitcoin30mScanner } from '@/composables/useBitcoin30mScanner'
import apiClient from '@/config/api'

// Components
import ApiKeyModal from '@/components/trading/ApiKeyModal.vue'
import ApiHelpModal from '@/components/trading/ApiHelpModal.vue'
import OrdersHistory from '@/components/trading/OrdersHistory.vue'
import Bitcoin30mScannerLogs from '@/components/trading/Bitcoin30mScannerLogs.vue'
import Bitcoin30mPortfolio from '@/components/trading/Bitcoin30mPortfolio.vue'
import Bitcoin30mManualTrading from '@/components/trading/Bitcoin30mManualTrading.vue'

// Stores
const authStore = useAuthStore()

// Composables
const apiKeys = useTradingApiKeys()
const orders = useTradingOrders()
const bitcoin30mScanner = useBitcoin30mScanner()

// Local state
const showAddApiKey = ref(false)
const showApiHelpModal = ref(false)
const portfolioRef = ref(null)
const manualTradingRef = ref(null)
const currentBtcPrice = ref(122000)

// Formulario específico para testnet
const apiKeyForm = reactive({
  api_key: '',
  secret_key: '',
  is_testnet: true, // Siempre true para esta vista
  max_position_size_usdt: 50,
  max_concurrent_positions: 3,
  auto_trading_enabled: false
})

// Computed properties
const testnetApiKeys = computed(() => {
  return apiKeys.apiKeys.value.filter(key => key.is_testnet === true)
})

const testnetOrders = computed(() => {
  const envFiltered = orders.orders.value.filter(order => order.is_testnet === true)
  return envFiltered.filter(order => 
    order.crypto_symbol === 'BTC_30m' || 
    (order.ticker === 'BTCUSDT' && order.bot_mode?.includes('30m')) ||
    (order.symbol === 'BTCUSDT' && order.reason === 'MANUAL_TRADE')
  )
})

// Methods
const loadCurrentBtcPrice = async () => {
  try {
    const response = await apiClient.get('/trading/scanner/bitcoin-30m/current-price')
    if (response.data.success) {
      currentBtcPrice.value = response.data.price
      console.log('[BitcoinTestnet] Precio BTC actualizado:', currentBtcPrice.value)
    }
  } catch (error) {
    console.error('Error obteniendo precio BTC:', error)
  }
}

const loadData = async () => {
  console.log('[BitcoinTestnet] loadData() inicio')
  try {
    await Promise.all([
      apiKeys.loadApiKeys(),
      orders.loadOrders(),
      bitcoin30mScanner.initializeScanner(),
      loadCurrentBtcPrice()
    ])
    
    if (portfolioRef.value && portfolioRef.value.refreshBalances) {
      await portfolioRef.value.refreshBalances()
    }
    
    console.log('[BitcoinTestnet] loadData() completado')
  } catch (error) {
    console.error('Error cargando datos Bitcoin Testnet:', error)
  }
}

const toggleBitcoin30m = async (apiKey) => {
  const enabled = !apiKey.btc_30m_testnet_enabled
  await updateBitcoin30mAllocation(apiKey, apiKey.btc_30m_testnet_allocated_usdt || 0, enabled)
}

const updateBitcoin30mAllocation = async (apiKey, amount, enabled = null) => {
  try {
    const updateData = {
      crypto: 'btc_30m_testnet',
      enabled: enabled !== null ? enabled : apiKey.btc_30m_testnet_enabled,
      allocated_usdt: parseFloat(amount) || 0
    }
    
    await apiClient.put(`/trading/crypto-allocation/${apiKey.id}`, updateData)
    await apiKeys.loadApiKeys()
    
    console.log('[BitcoinTestnet] Bitcoin 30m allocation actualizada')
  } catch (error) {
    console.error('Error actualizando Bitcoin 30m allocation:', error)
    alert('Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
  }
}

const closeAddApiKeyModal = () => {
  showAddApiKey.value = false
  resetApiKeyForm()
}

const handleSubmitApiKey = async () => {
  console.log('[BitcoinTestnet] Enviando API key testnet:', { ...apiKeyForm })
  try {
    await apiClient.post('/trading/api-keys', apiKeyForm)
    resetApiKeyForm()
    await apiKeys.loadApiKeys()
    closeAddApiKeyModal()
    alert('✅ API Key Testnet agregada exitosamente')
  } catch (error) {
    console.error('Error guardando API key testnet:', error)
    alert('❌ Error guardando API key: ' + (error.response?.data?.detail || error.message))
  }
}

const resetApiKeyForm = () => {
  Object.assign(apiKeyForm, {
    api_key: '',
    secret_key: '',
    is_testnet: true,
    max_position_size_usdt: 50,
    max_concurrent_positions: 3,
    auto_trading_enabled: false
  })
}

const handleOrderExecuted = (orderInfo) => {
  console.log('[BitcoinTestnet] Manual order executed:', orderInfo)
  loadData()
}

// Proxy methods
const testConnection = apiKeys.testConnection
const deleteApiKey = apiKeys.deleteApiKey
const testingConnection = computed(() => apiKeys.testingConnection.value)
const submittingApiKey = computed(() => apiKeys.submittingApiKey.value)

// Lifecycle
onMounted(async () => {
  console.log('[BitcoinTestnet] onMounted - usuario:', authStore.user)
  await loadData()
  bitcoin30mScanner.startPolling()
})

onUnmounted(() => {
  bitcoin30mScanner.stopPolling()
})
</script>
