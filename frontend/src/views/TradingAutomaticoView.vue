<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
          <span class="text-4xl mr-3">🤖</span>
          Trading Automático
        </h1>
        <p class="text-slate-600">Configura el trading automático usando las mismas estrategias exitosas (8% TP, 3% SL)</p>
      </div>

      <!-- Status Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- Estado General -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-slate-900">Estado General</h3>
            <span :class="tradingStatus?.auto_trading_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  class="px-3 py-1 rounded-full text-sm font-medium">
              {{ tradingStatus?.auto_trading_enabled ? '🟢 Activo' : '🔴 Inactivo' }}
            </span>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Posiciones Activas:</span>
              <span class="font-medium">{{ tradingStatus?.active_positions || 0 }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">PnL Hoy:</span>
              <span :class="(tradingStatus?.pnl_today_usdt || 0) >= 0 ? 'text-green-600' : 'text-red-600'" class="font-medium">
                ${{ tradingStatus?.pnl_today_usdt?.toFixed(2) || '0.00' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Balance -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-slate-900">Balance</h3>
            <span class="text-2xl">💰</span>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Disponible:</span>
              <span class="font-medium">${{ tradingStatus?.available_balance_usdt?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Órdenes Hoy:</span>
              <span class="font-medium">{{ tradingStatus?.total_orders_today || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Estrategia -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-slate-900">Estrategia</h3>
            <span class="text-2xl">🎯</span>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Take Profit:</span>
              <span class="font-medium text-green-600">+8%</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Stop Loss:</span>
              <span class="font-medium text-red-600">-3%</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Max Hold:</span>
              <span class="font-medium">13.3 días</span>
            </div>
          </div>
        </div>
      </div>

      <!-- API Keys Section -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-slate-900 flex items-center">
            <span class="text-2xl mr-2">🔑</span>
            API Keys de Binance
          </h2>
          <button 
            @click="showAddApiKey = true"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center text-sm font-medium transition-colors">
            <span class="mr-1">➕</span>
            Agregar API Key
          </button>
        </div>

        <!-- API Keys List -->
        <div class="space-y-4">
          <div v-if="apiKeys.length === 0" class="text-center py-8 text-slate-500">
            <span class="text-6xl">🔐</span>
            <p class="text-lg mt-4">No tienes API keys configuradas</p>
            <p class="text-sm">Agrega tus API keys de Binance para habilitar el trading automático</p>
          </div>

          <div v-for="apiKey in apiKeys" :key="apiKey.id" 
               class="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors">
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-2">
                  <span class="text-lg">{{ apiKey.is_testnet ? '🧪' : '💰' }}</span>
                  <span class="font-medium">{{ apiKey.is_testnet ? 'Testnet' : 'Mainnet' }}</span>
                  <span class="px-2 py-1 rounded text-xs font-medium bg-slate-100 text-slate-700">
                    {{ (apiKey.exchange || 'binance').toUpperCase() }}
                  </span>
                  <span :class="apiKey.connection_status === 'active' ? 'bg-green-100 text-green-800' : 
                               apiKey.connection_status === 'error' ? 'bg-red-100 text-red-800' : 
                               'bg-yellow-100 text-yellow-800'"
                        class="px-2 py-1 rounded text-xs font-medium">
                    {{ apiKey.connection_status === 'active' ? '✅ Conectado' : 
                       apiKey.connection_status === 'error' ? '❌ Error' : '⏳ No probado' }}
                  </span>
                </div>
                
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span class="text-slate-600">API Key:</span>
                    <div class="font-mono text-xs mt-1">{{ apiKey.api_key_masked }}</div>
                  </div>
                  <div>
                    <span class="text-slate-600">Max Posición:</span>
                    <div class="font-medium mt-1">${{ apiKey.max_position_size_usdt }}</div>
                  </div>
                  <div>
                    <span class="text-slate-600">Max Posiciones:</span>
                    <div class="font-medium mt-1">{{ apiKey.max_concurrent_positions }}</div>
                  </div>
                  <div>
                    <span class="text-slate-600">Trading:</span>
                    <div class="font-medium mt-1">
                      <span :class="apiKey.auto_trading_enabled ? 'text-green-600' : 'text-red-600'">
                        {{ apiKey.auto_trading_enabled ? '✅ Habilitado' : '❌ Deshabilitado' }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Controles por Crypto -->
                <div class="mt-4 p-4 bg-slate-50 rounded-lg">
                  <h4 class="text-sm font-semibold text-slate-800 mb-3">🎛️ Control por Criptomoneda</h4>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <!-- Bitcoin -->
                    <div class="bg-white p-3 rounded border">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-orange-600">₿ Bitcoin</span>
                        <button 
                          @click="toggleCrypto(apiKey, 'btc')" 
                          :class="apiKey.btc_enabled ? 'bg-orange-500 text-white' : 'bg-slate-300 text-slate-600'"
                          class="px-3 py-1 rounded text-xs font-medium transition-colors">
                          {{ apiKey.btc_enabled ? 'ON' : 'OFF' }}
                        </button>
                      </div>
                      <div class="text-xs text-slate-600">
                        Asignado: ${{ (apiKey.btc_allocated_usdt || 0).toFixed(2) }}
                      </div>
                    </div>

                    <!-- Ethereum -->
                    <div class="bg-white p-3 rounded border">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-blue-600">Ξ Ethereum</span>
                        <button 
                          @click="toggleCrypto(apiKey, 'eth')" 
                          :class="apiKey.eth_enabled ? 'bg-blue-500 text-white' : 'bg-slate-300 text-slate-600'"
                          class="px-3 py-1 rounded text-xs font-medium transition-colors">
                          {{ apiKey.eth_enabled ? 'ON' : 'OFF' }}
                        </button>
                      </div>
                      <div class="text-xs text-slate-600">
                        Asignado: ${{ (apiKey.eth_allocated_usdt || 0).toFixed(2) }}
                      </div>
                    </div>

                    <!-- BNB -->
                    <div class="bg-white p-3 rounded border">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-yellow-600">🟡 BNB</span>
                        <button 
                          @click="toggleCrypto(apiKey, 'bnb')" 
                          :class="apiKey.bnb_enabled ? 'bg-yellow-500 text-white' : 'bg-slate-300 text-slate-600'"
                          class="px-3 py-1 rounded text-xs font-medium transition-colors">
                          {{ apiKey.bnb_enabled ? 'ON' : 'OFF' }}
                        </button>
                      </div>
                      <div class="text-xs text-slate-600">
                        Asignado: ${{ (apiKey.bnb_allocated_usdt || 0).toFixed(2) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex gap-2 ml-4">
                <button @click="testConnection(apiKey)" 
                        :disabled="testingConnection === apiKey.id"
                        class="bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white px-3 py-1 rounded text-sm font-medium transition-colors">
                  {{ testingConnection === apiKey.id ? '⏳' : '🔌' }} Test
                </button>
                <button @click="editApiKey(apiKey)"
                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors">
                  ⚙️ Config
                </button>
                <button @click="deleteApiKey(apiKey.id)"
                        class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trading Orders History -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-slate-900 flex items-center">
            <span class="text-2xl mr-2">📊</span>
            Historial de Órdenes
          </h2>
          <button @click="loadOrders" class="text-blue-600 hover:text-blue-700 text-sm font-medium">
            🔄 Actualizar
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200">
                <th class="text-left py-3 px-2 font-medium text-slate-700">Fecha</th>
                <th class="text-left py-3 px-2 font-medium text-slate-700">Symbol</th>
                <th class="text-left py-3 px-2 font-medium text-slate-700">Tipo</th>
                <th class="text-right py-3 px-2 font-medium text-slate-700">Cantidad</th>
                <th class="text-right py-3 px-2 font-medium text-slate-700">Precio</th>
                <th class="text-right py-3 px-2 font-medium text-slate-700">PnL</th>
                <th class="text-left py-3 px-2 font-medium text-slate-700">Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="orders.length === 0" class="border-b border-slate-100">
                <td colspan="7" class="text-center py-8 text-slate-500">
                  <span class="text-4xl">📝</span>
                  <p class="mt-2">No hay órdenes registradas</p>
                </td>
              </tr>
              <tr v-for="order in orders" :key="order.id" class="border-b border-slate-100 hover:bg-slate-50">
                <td class="py-3 px-2">{{ formatDate(order.created_at) }}</td>
                <td class="py-3 px-2">{{ order.symbol }}</td>
                <td class="py-3 px-2">
                  <span :class="order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                        class="px-2 py-1 rounded text-xs font-medium">
                    {{ order.side === 'BUY' ? '📈 BUY' : '📉 SELL' }}
                  </span>
                </td>
                <td class="py-3 px-2 text-right font-mono">{{ order.quantity?.toFixed(6) }}</td>
                <td class="py-3 px-2 text-right font-mono">${{ order.executed_price?.toFixed(2) }}</td>
                <td class="py-3 px-2 text-right font-mono">
                  <span v-if="order.pnl_usdt !== null" 
                        :class="order.pnl_usdt >= 0 ? 'text-green-600' : 'text-red-600'">
                    ${{ order.pnl_usdt.toFixed(2) }}
                  </span>
                  <span v-else class="text-slate-400">-</span>
                </td>
                <td class="py-3 px-2">
                  <span :class="getStatusColor(order.status)" class="px-2 py-1 rounded text-xs font-medium">
                    {{ getStatusText(order.status) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add API Key Modal -->
    <div v-if="showAddApiKey" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg max-w-md w-full p-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-slate-900">Agregar API Key</h3>
          <button @click="closeAddApiKeyModal" class="text-slate-400 hover:text-slate-600">
            ✕
          </button>
        </div>

        <form @submit.prevent="submitApiKey" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">API Key *</label>
            <input 
              type="text" 
              v-model="apiKeyForm.api_key"
              placeholder="Ingresa tu API Key de Binance"
              class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Secret Key *</label>
            <input 
              type="password" 
              v-model="apiKeyForm.secret_key"
              placeholder="Ingresa tu Secret Key de Binance"
              class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
          </div>

          <div class="flex items-center">
            <input 
              type="checkbox" 
              id="testnet" 
              v-model="apiKeyForm.is_testnet"
              class="mr-2"
            >
            <label for="testnet" class="text-sm text-slate-700">
              🧪 Usar Testnet (recomendado para pruebas)
            </label>
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Tamaño máximo por posición (USDT)</label>
            <input 
              type="number" 
              v-model="apiKeyForm.max_position_size_usdt"
              min="10"
              max="10000"
              step="10"
              class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
          </div>

          <div class="flex gap-4 pt-4">
            <button 
              type="button" 
              @click="closeAddApiKeyModal"
              class="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-700 py-2 px-4 rounded-lg font-medium transition-colors">
              Cancelar
            </button>
            <button 
              type="submit" 
              :disabled="submittingApiKey"
              class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-2 px-4 rounded-lg font-medium transition-colors">
              {{ submittingApiKey ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'
import apiConfig from '../config/api'

// Auth store
const authStore = useAuthStore()

// Estado reactivo
const apiKeys = ref([])
const orders = ref([])
const tradingStatus = ref({
  auto_trading_enabled: false,
  active_positions: 0,
  total_orders_today: 0,
  pnl_today_usdt: 0,
  available_balance_usdt: 0
})

const showAddApiKey = ref(false)
const testingConnection = ref(null)
const submittingApiKey = ref(false)

// Estado para modal de crypto allocation
const showCryptoModal = ref(false)
const cryptoModalData = reactive({
  apiKey: null,
  crypto: '',
  cryptoName: '',
  currentEnabled: false,
  allocatedUsdt: 0
})

const apiKeyForm = reactive({
  api_key: '',
  secret_key: '',
  is_testnet: true,
  max_position_size_usdt: 50,
  max_concurrent_positions: 3,
  auto_trading_enabled: false
})

// Funciones
const loadData = async () => {
  try {
    await Promise.all([
      loadApiKeys(),
      loadTradingStatus(),
      loadOrders()
    ])
  } catch (error) {
    console.error('Error cargando datos:', error)
  }
}

const loadApiKeys = async () => {
  try {
    const response = await axios.get(`${apiConfig.baseURL}/trading/api-keys`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    apiKeys.value = response.data
  } catch (error) {
    console.error('Error cargando API keys:', error)
  }
}

const loadTradingStatus = async () => {
  try {
    const response = await axios.get(`${apiConfig.baseURL}/trading/status`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    tradingStatus.value = response.data
  } catch (error) {
    console.error('Error cargando estado de trading:', error)
  }
}

const loadOrders = async () => {
  try {
    const response = await axios.get(`${apiConfig.baseURL}/trading/orders?limit=20`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    orders.value = response.data.trades || []
  } catch (error) {
    console.error('Error cargando órdenes:', error)
  }
}

const submitApiKey = async () => {
  submittingApiKey.value = true
  try {
    await axios.post(`${apiConfig.baseURL}/trading/api-keys`, apiKeyForm, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    closeAddApiKeyModal()
    await loadApiKeys()
    alert('✅ API Key agregada exitosamente')
  } catch (error) {
    console.error('Error guardando API key:', error)
    alert('❌ Error guardando API key: ' + (error.response?.data?.detail || error.message))
  } finally {
    submittingApiKey.value = false
  }
}

const testConnection = async (apiKey) => {
  testingConnection.value = apiKey.id
  try {
    const response = await axios.post(`${apiConfig.baseURL}/trading/test-connection/${apiKey.id}`, {}, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (response.data.success) {
      alert(`✅ Conexión exitosa\n${response.data.testnet ? 'Testnet' : 'Mainnet'}\nBalance: $${response.data.balance_usdt?.toFixed(2) || '0.00'}`)
    } else {
      alert(`❌ Error de conexión: ${response.data.message}`)
    }
    await loadApiKeys() // Actualizar estado
  } catch (error) {
    console.error('Error probando conexión:', error)
    alert('❌ Error probando conexión: ' + (error.response?.data?.detail || error.message))
  } finally {
    testingConnection.value = null
  }
}

const editApiKey = (apiKey) => {
  // TODO: Implementar modal de edición
  alert('🚧 Función de edición en desarrollo')
}

const deleteApiKey = async (apiKeyId) => {
  if (!confirm('¿Estás seguro de que quieres eliminar esta API key?')) return
  
  try {
    await axios.delete(`${apiConfig.baseURL}/trading/api-keys/${apiKeyId}`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    await loadApiKeys()
    alert('✅ API Key eliminada exitosamente')
  } catch (error) {
    console.error('Error eliminando API key:', error)
    alert('❌ Error eliminando API key: ' + (error.response?.data?.detail || error.message))
  }
}

const toggleCrypto = (apiKey, crypto) => {
  const cryptoNames = { btc: 'Bitcoin', eth: 'Ethereum', bnb: 'BNB' }
  const currentEnabled = apiKey[`${crypto}_enabled`]
  const currentAllocated = apiKey[`${crypto}_allocated_usdt`] || 0
  
  // Si está habilitando
  if (!currentEnabled) {
    const confirmed = confirm(`⚠️ ¿Estás seguro de que quieres activar el bot automático para ${cryptoNames[crypto]}?\n\n✅ Esto iniciará trading automático usando tu estrategia probada (8% TP, 3% SL)\n💰 Necesitas asignar un balance en USDT para esta crypto`)
    
    if (confirmed) {
      const amount = prompt(`💰 ¿Cuántos USDT quieres asignar a ${cryptoNames[crypto]}?\n\nBalance actual asignado: $${currentAllocated.toFixed(2)}`, currentAllocated.toString())
      
      if (amount !== null && !isNaN(amount) && parseFloat(amount) > 0) {
        updateCryptoAllocation(apiKey.id, crypto, true, parseFloat(amount))
      }
    }
  } else {
    // Si está deshabilitando
    const confirmed = confirm(`🛑 ¿Estás seguro de que quieres desactivar el trading automático para ${cryptoNames[crypto]}?\n\n⚠️ Se cancelarán las órdenes pendientes y se detendrá el monitoreo automático`)
    
    if (confirmed) {
      updateCryptoAllocation(apiKey.id, crypto, false, currentAllocated)
    }
  }
}

const updateCryptoAllocation = async (apiKeyId, crypto, enabled, allocatedUsdt) => {
  try {
    const response = await axios.put(`${apiConfig.baseURL}/trading/crypto-allocation/${apiKeyId}`, {
      crypto: crypto,
      enabled: enabled,
      allocated_usdt: allocatedUsdt
    }, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    await loadApiKeys()
    alert(`✅ ${response.data.message}`)
    
  } catch (error) {
    console.error('Error actualizando crypto allocation:', error)
    alert('❌ Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
  }
}

const closeAddApiKeyModal = () => {
  showAddApiKey.value = false
  // Reset form
  Object.assign(apiKeyForm, {
    api_key: '',
    secret_key: '',
    is_testnet: true,
    max_position_size_usdt: 50,
    max_concurrent_positions: 3,
    auto_trading_enabled: false
  })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusColor = (status) => {
  switch (status) {
    case 'FILLED': return 'bg-green-100 text-green-800'
    case 'PENDING': return 'bg-yellow-100 text-yellow-800'
    case 'CANCELLED': return 'bg-slate-100 text-slate-800'
    case 'REJECTED': return 'bg-red-100 text-red-800'
    default: return 'bg-slate-100 text-slate-800'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'FILLED': return '✅ Ejecutada'
    case 'PENDING': return '⏳ Pendiente'
    case 'CANCELLED': return '🚫 Cancelada'
    case 'REJECTED': return '❌ Rechazada'
    default: return status
  }
}

// Cargar datos al montar el componente
onMounted(loadData)
</script>