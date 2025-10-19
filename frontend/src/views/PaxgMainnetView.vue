<!-- views/PaxgMainnetView.vue -->
<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Header -->
    <div class="bg-white shadow-sm border-b border-yellow-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between py-4">
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                <span class="text-2xl">🥇</span>
              </div>
              <div>
                <h1 class="text-xl font-bold text-slate-900">PAXG 4h Scanner</h1>
                <p class="text-sm text-yellow-600 font-medium">MAINNET - DINERO REAL</p>
              </div>
            </div>
          </div>
          
          <div class="mt-4 lg:mt-0">
            <div class="flex items-center space-x-4">
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <span class="text-sm font-medium text-green-600">
                  {{ paxgScanner.scannerStatus.value.is_running ? 'Scanner Activo' : 'Scanner Inactivo' }}
                </span>
              </div>
              
              <div class="text-sm text-slate-500">
                Precio PAXG: ${{ currentPaxgPrice.toLocaleString() }}
              </div>
              <div class="text-xs text-slate-400">
                Último escaneo: {{ paxgScanner.scannerStatus.value.last_scan_time || '—' }}
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
        <div class="bg-white rounded-lg shadow-sm border border-yellow-200">
          <div class="p-6 border-b border-yellow-100">
            <h3 class="text-xl font-semibold text-slate-900 flex items-center">
              <span class="text-yellow-500 mr-3">💰</span>
              API Keys Mainnet
            </h3>
            <p class="text-sm text-slate-600 mt-2">⚠️ Configuración para trading con dinero real</p>
          </div>
          
          <div class="p-6">
            <div v-if="mainnetApiKeys.length === 0" class="text-center py-8">
              <div class="text-6xl text-slate-300 mb-4">🔑</div>
              <h4 class="text-lg font-medium text-slate-700 mb-2">No tienes API keys de Mainnet configuradas</h4>
              <p class="text-slate-600 mb-6">Agrega tu API key de Binance Mainnet para comenzar con el trading real</p>
              <button
                @click="showAddApiKey = true"
                class="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                Agregar API Key Mainnet
              </button>
            </div>
            
            <div v-else class="space-y-6">
              <div 
                v-for="apiKey in mainnetApiKeys" 
                :key="apiKey.id"
                class="border border-yellow-200 rounded-lg p-6 bg-yellow-50/30"
              >
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center space-x-3">
                    <span class="text-2xl text-yellow-500">💰</span>
                    <div>
                      <h4 class="font-semibold text-slate-900">Mainnet API Key</h4>
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
                
                <!-- PAXG 4h Mainnet Configuration -->
                <div class="bg-white rounded-lg p-4 border border-yellow-200">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-yellow-500 text-lg">🥇</span>
                      <span class="font-semibold text-slate-800">PAXG 4h Scanner</span>
                    </div>
                    <button
                      @click="togglePaxg(apiKey)"
                      :class="[
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        apiKey.paxg_4h_mainnet_enabled 
                          ? 'bg-green-500 text-white hover:bg-green-600' 
                          : 'bg-slate-400 text-white hover:bg-slate-500'
                      ]"
                    >
                      {{ apiKey.paxg_4h_mainnet_enabled ? '✓ Activado' : 'Activar Scanner' }}
                    </button>
                  </div>
                  <div class="flex items-center gap-3 mb-3">
                    <button
                      @click="handleForceBuy"
                      :disabled="!paxgScanner.scannerStatus.value?.auto_trading_readiness?.auto_ready"
                      class="px-3 py-2 text-white text-xs rounded"
                      :class="paxgScanner.scannerStatus.value?.auto_trading_readiness?.auto_ready ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-slate-400'"
                    >
                      Forzar compra (simulación)
                    </button>
                    <span class="text-xs" :class="paxgScanner.scannerStatus.value?.auto_trading_readiness?.auto_ready ? 'text-slate-500' : 'text-red-500'">
                      {{ paxgScanner.scannerStatus.value?.auto_trading_readiness?.auto_ready ? 'Prueba en MAINNET con asignación actual' : 'Auto-trading NO LISTO: ' + (paxgScanner.scannerStatus.value?.auto_trading_readiness?.reasons?.join(', ') || '') }}
                    </span>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-slate-700 mb-2">Cantidad asignada (USDT)</label>
                      <input
                        type="number"
                        :value="apiKey.paxg_4h_mainnet_allocated_usdt || 0"
                        @change="updatePaxgAllocation(apiKey, $event.target.value)"
                        min="0"
                        step="0.01"
                        class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                        placeholder="Ej: 100.00"
                      />
                    </div>
                    <div class="flex items-end">
                      <div class="text-sm text-slate-600">
                        <div class="font-medium">Estado actual:</div>
                        <div class="text-yellow-600">
                          ${{ (apiKey.paxg_4h_mainnet_allocated_usdt || 0).toFixed(2) }} USDT asignados
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
                  class="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
                >
                  + Agregar otra API Key
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Scanner Status Cards -->
        <CryptoStatusCards
          :scanner-status="paxgScanner.scannerStatus.value"
          :current-price="currentPaxgPrice"
          crypto-name="PAXG"
          crypto-symbol="PAXG"
          crypto-emoji="🥇"
          timeframe="4h"
          scan-interval-text="Escaneo cada 1 hora"
          :profit-target="0.08"
          :stop-loss="0.03"
          max-hold-text="13 días"
          cooldown-period-text="1 hora"
          color-theme="yellow"
          @start-scanner="handleStartScanner"
          @stop-scanner="handleStopScanner"
          @refresh-status="handleRefreshStatus"
        />
        
        <!-- Open Positions -->
        <OpenPositionsCard
          environment="mainnet"
          @refresh="loadData"
        />
        
        <!-- Portfolio (reutilizando componente de Bitcoin, funciona para todos) -->
        <Bitcoin30mPortfolio
          ref="portfolioRef"
          :api-keys="mainnetApiKeys"
          environment="mainnet"
          :current-btc-price="currentPaxgPrice"
        />
        
        <!-- Orders History -->
        <MainnetHistory />
        
        <!-- Scanner Logs -->
        <CryptoScannerLogs
          :logs="paxgScanner.scannerLogs.value"
          :refreshing="paxgScanner.refreshingLogs.value"
          :scanner-status="paxgScanner.scannerStatus.value"
          :current-price="currentPaxgPrice"
          crypto-name="PAXG"
          crypto-symbol="PAXG"
          crypto-slug="paxg-mainnet"
          timeframe="4h"
          @refresh="paxgScanner.refreshLogs"
        />
      </div>
    </div>
    
    <!-- Add API Key Modal -->
    <ApiKeyModal
      v-if="showAddApiKey"
      :show="showAddApiKey"
      :api-key-form="apiKeyForm"
      :is-submitting="submittingApiKey"
      environment="mainnet"
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
import { ref, computed, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useAuthStore } from '../stores/authStore'

// Composables
import { useTradingApiKeys } from '@/composables/useTradingApiKeys'
import { useTradingOrders } from '@/composables/useTradingOrders'  
import { usePaxgMainnetScanner } from '@/composables/usePaxgMainnetScanner'
import apiClient from '@/config/api'

// Components
import ApiKeyModal from '@/components/trading/ApiKeyModal.vue'
import ApiHelpModal from '@/components/trading/ApiHelpModal.vue'
import MainnetHistory from '@/components/trading/MainnetHistory.vue'
import CryptoScannerLogs from '@/components/trading/CryptoScannerLogs.vue'
import CryptoStatusCards from '@/components/trading/CryptoStatusCards.vue'
import OpenPositionsCard from '@/components/trading/OpenPositionsCard.vue'
import Bitcoin30mPortfolio from '@/components/trading/Bitcoin30mPortfolio.vue'

// Stores
const authStore = useAuthStore()

// Composables
const apiKeys = useTradingApiKeys()
const orders = useTradingOrders()
const paxgScanner = usePaxgMainnetScanner()

// Local state
const showAddApiKey = ref(false)
const showApiHelpModal = ref(false)
const portfolioRef = ref(null)
const currentPaxgPrice = ref(2500)

// Formulario específico para mainnet
const apiKeyForm = reactive({
  api_key: '',
  secret_key: '',
  is_testnet: false, // Siempre false para esta vista
  max_position_size_usdt: 50,
  max_concurrent_positions: 3,
  auto_trading_enabled: false
})

// Computed properties
const mainnetApiKeys = computed(() => {
  return apiKeys.apiKeys.value.filter(key => key.is_testnet === false)
})

const mainnetOrders = computed(() => {
  const envFiltered = orders.orders.value.filter(order => order.is_testnet === false)
  return envFiltered.filter(order => 
    order.crypto_symbol === 'PAXG' || 
    (order.ticker === 'PAXGUSDT') ||
    (order.symbol === 'PAXGUSDT')
  )
})

// Methods
const loadCurrentPaxgPrice = async () => {
  try {
    // Preferimos el precio del último escaneo desde el status
    await paxgScanner.refreshStatus()
    const statusPrice = paxgScanner.scannerStatus.value?.paxg_price
    if (statusPrice) {
      currentPaxgPrice.value = statusPrice
      console.log('[PaxgMainnet] Precio PAXG (status/last_scan):', currentPaxgPrice.value)
    } else {
      const response = await apiClient.get('/trading/scanner/paxg-mainnet/current-price')
      if (response.data.success) {
        currentPaxgPrice.value = response.data.price
        console.log('[PaxgMainnet] Precio PAXG (endpoint directo):', currentPaxgPrice.value)
      }
    }
  } catch (error) {
    console.error('Error obteniendo precio PAXG:', error)
  }
}

const loadData = async () => {
  console.log('[PaxgMainnet] loadData() inicio')
  try {
    await Promise.all([
      apiKeys.loadApiKeys(),
      orders.loadOrders(),
      paxgScanner.initializeScanner(),
      loadCurrentPaxgPrice()
    ])
    
    // Log detallado de las API keys después de cargar
    console.log('[PaxgMainnet] 🔑 API Keys cargadas:', {
      totalKeys: apiKeys.apiKeys.value.length,
      mainnetKeys: mainnetApiKeys.value.length,
      mainnetKeysDetail: mainnetApiKeys.value.map(k => ({
        id: k.id,
        is_active: k.is_active,
        paxg_4h_mainnet_enabled: k.paxg_4h_mainnet_enabled,
        paxg_4h_mainnet_allocated_usdt: k.paxg_4h_mainnet_allocated_usdt
      }))
    })
    
    if (portfolioRef.value && portfolioRef.value.refreshBalances) {
      await portfolioRef.value.refreshBalances()
    }
    
    console.log('[PaxgMainnet] loadData() completado')
  } catch (error) {
    console.error('Error cargando datos PAXG Mainnet:', error)
  }
}

const togglePaxg = async (apiKey) => {
  const enabled = !apiKey.paxg_4h_mainnet_enabled
  await updatePaxgAllocation(apiKey, apiKey.paxg_4h_mainnet_allocated_usdt || 0, enabled)
}

const updatePaxgAllocation = async (apiKey, amount, enabled = null) => {
  try {
    const updateData = {
      crypto: 'paxg_4h_mainnet',
      enabled: enabled !== null ? enabled : apiKey.paxg_4h_mainnet_enabled,
      allocated_usdt: parseFloat(amount) || 0
    }
    
    console.log('[PaxgMainnet] 🔧 Actualizando PAXG allocation:', {
      apiKeyId: apiKey.id,
      currentEnabled: apiKey.paxg_4h_mainnet_enabled,
      currentAllocated: apiKey.paxg_4h_mainnet_allocated_usdt,
      newAmount: amount,
      newEnabled: enabled,
      updateData: updateData
    })
    
    const response = await apiClient.put(`/trading/crypto-allocation/${apiKey.id}`, updateData)
    console.log('[PaxgMainnet] ✅ Respuesta del servidor:', response.data)
    
    await apiKeys.loadApiKeys()
    
    console.log('[PaxgMainnet] PAXG allocation actualizada exitosamente')
  } catch (error) {
    console.error('[PaxgMainnet] ❌ Error actualizando PAXG allocation:', {
      error: error,
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })
    alert('Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
  }
}

const closeAddApiKeyModal = () => {
  showAddApiKey.value = false
  resetApiKeyForm()
}

const handleSubmitApiKey = async () => {
  console.log('[PaxgMainnet] Enviando API key mainnet:', { ...apiKeyForm })
  try {
    await apiClient.post('/trading/api-keys', apiKeyForm)
    resetApiKeyForm()
    await apiKeys.loadApiKeys()
    closeAddApiKeyModal()
    alert('✅ API Key Mainnet agregada exitosamente')
  } catch (error) {
    console.error('Error guardando API key mainnet:', error)
    alert('❌ Error guardando API key: ' + (error.response?.data?.detail || error.message))
  }
}

const resetApiKeyForm = () => {
  Object.assign(apiKeyForm, {
    api_key: '',
    secret_key: '',
    is_testnet: false,
    max_position_size_usdt: 50,
    max_concurrent_positions: 3,
    auto_trading_enabled: false
  })
}

// Scanner control methods
const handleStartScanner = async () => {
  console.log('[PaxgMainnet] Iniciando scanner...')
  const success = await paxgScanner.startScanner()
  if (success) {
    alert('✅ Scanner PAXG 4h Mainnet iniciado exitosamente')
  } else {
    alert('❌ Error iniciando scanner PAXG 4h Mainnet')
  }
}

const handleStopScanner = async () => {
  console.log('[PaxgMainnet] Deteniendo scanner...')
  const success = await paxgScanner.stopScanner()
  if (success) {
    alert('⏹️ Scanner PAXG 4h Mainnet detenido exitosamente')
  } else {
    alert('❌ Error deteniendo scanner PAXG 4h Mainnet')
  }
}

const handleRefreshStatus = async () => {
  console.log('[PaxgMainnet] Actualizando estado del scanner...')
  await paxgScanner.refreshStatus()
}

const handleForceBuy = async () => {
  const confirmed = confirm('¿Forzar compra simulada en MAINNET con la asignación actual?')
  if (!confirmed) return
  const ok = await paxgScanner.forceBuySignal()
  alert(ok ? '✅ Compra simulada disparada' : '❌ Error forzando compra')
  await loadData()
}

// Proxy methods
const testConnection = apiKeys.testConnection
const deleteApiKey = apiKeys.deleteApiKey
const testingConnection = computed(() => apiKeys.testingConnection.value)
const submittingApiKey = computed(() => apiKeys.submittingApiKey.value)

// Watchers
watch(mainnetApiKeys, (newKeys, oldKeys) => {
  console.log('[PaxgMainnet] 🔄 mainnetApiKeys changed:', {
    oldLength: oldKeys?.length || 0,
    newLength: newKeys?.length || 0,
    newKeys: newKeys.map(k => ({
      id: k.id,
      is_active: k.is_active,
      paxg_4h_mainnet_enabled: k.paxg_4h_mainnet_enabled,
      paxg_4h_mainnet_allocated_usdt: k.paxg_4h_mainnet_allocated_usdt
    }))
  })
}, { deep: true })

// Lifecycle
onMounted(async () => {
  console.log('[PaxgMainnet] onMounted - usuario:', authStore.user)
  await loadData()
  paxgScanner.startPolling()
  // Sincronizar precio cada 45s
  const syncFromStatus = async () => {
    const p = paxgScanner.scannerStatus.value?.paxg_price
    if (p) {
      currentPaxgPrice.value = p
      console.log('[PaxgMainnet] Sync precio desde status (nuevo escaneo):', p)
    }
  }
  setInterval(syncFromStatus, 45000)
})

onUnmounted(() => {
  paxgScanner.stopPolling()
})
</script>
