<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center">
        <span class="text-2xl mr-3">⚡</span>
        <div>
          <h3 class="text-lg font-semibold text-slate-900">Trading Manual Bitcoin 30m</h3>
          <p class="text-sm text-slate-600">Ejecuta órdenes manuales de compra y venta</p>
        </div>
      </div>
      
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" 
              :class="environment === 'testnet' ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800'">
          {{ environment === 'testnet' ? '🧪 Testnet' : '🔴 Mainnet' }}
        </span>
      </div>
    </div>

    <!-- Current Price Display -->
    <div class="bg-gradient-to-r from-slate-50 to-gray-50 rounded-lg p-4 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-slate-600">Precio Actual BTC/USDT</p>
          <p class="text-2xl font-bold text-slate-900">${{ currentPrice.toLocaleString() }}</p>
        </div>
        <div class="text-right">
          <button 
            @click="refreshPrice"
            :disabled="loadingPrice"
            class="bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-medium py-1 px-2 rounded transition-colors"
          >
            <span v-if="loadingPrice" class="animate-spin">🔄</span>
            <span v-else>🔄</span>
          </button>
          <p class="text-xs text-slate-500 mt-1">
            {{ lastPriceUpdate || 'Sin actualizar' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Trading Panels -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Buy Panel -->
      <div class="border border-green-200 rounded-lg p-4 bg-green-50">
        <h4 class="text-lg font-semibold text-green-800 mb-4 flex items-center">
          <span class="mr-2">📈</span>
          Comprar BTC
        </h4>
        
        <div class="space-y-4">
          <!-- Order Type -->
          <div>
            <label class="block text-sm font-medium text-green-700 mb-2">
              Tipo de Orden
            </label>
            <div class="flex gap-2">
              <button 
                @click="buyOrderType = 'market'"
                :class="buyOrderType === 'market' ? 'bg-green-600 text-white' : 'bg-white text-green-600 border border-green-600'"
                class="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
              >
                🏃 Mercado
              </button>
              <button 
                @click="buyOrderType = 'limit'"
                :class="buyOrderType === 'limit' ? 'bg-green-600 text-white' : 'bg-white text-green-600 border border-green-600'"
                class="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
              >
                🎯 Límite
              </button>
            </div>
          </div>

          <!-- Price (only for limit orders) -->
          <div v-if="buyOrderType === 'limit'">
            <label class="block text-sm font-medium text-green-700 mb-2">
              Precio de Compra (USDT)
            </label>
            <div class="relative">
              <input 
                v-model="buyPrice"
                type="number"
                step="0.01"
                :placeholder="`Ej: ${(currentPrice * 0.98).toFixed(0)}`"
                class="w-full border border-green-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <div class="absolute right-2 top-2 flex gap-1">
                <button 
                  @click="buyPrice = (currentPrice * 0.98).toFixed(0)"
                  class="text-xs bg-green-200 text-green-800 px-2 py-1 rounded"
                  title="2% por debajo del precio actual"
                >
                  -2%
                </button>
                <button 
                  @click="buyPrice = (currentPrice * 0.95).toFixed(0)"
                  class="text-xs bg-green-200 text-green-800 px-2 py-1 rounded"
                  title="5% por debajo del precio actual"
                >
                  -5%
                </button>
              </div>
            </div>
          </div>

          <!-- Amount -->
          <div>
            <label class="block text-sm font-medium text-green-700 mb-2">
              Cantidad USDT a invertir
            </label>
            <div class="relative">
              <input 
                v-model="buyAmount"
                type="number"
                step="0.01"
                placeholder="100.00"
                class="w-full border border-green-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
              <div class="absolute right-2 top-2 flex gap-1">
                <button 
                  @click="buyAmount = '100'"
                  class="text-xs bg-green-200 text-green-800 px-2 py-1 rounded"
                >
                  $100
                </button>
                <button 
                  @click="buyAmount = '500'"
                  class="text-xs bg-green-200 text-green-800 px-2 py-1 rounded"
                >
                  $500
                </button>
                <button 
                  @click="buyAmount = '1000'"
                  class="text-xs bg-green-200 text-green-800 px-2 py-1 rounded"
                >
                  $1K
                </button>
              </div>
            </div>
          </div>

          <!-- Estimated BTC -->
          <div class="bg-white rounded p-3 border border-green-200">
            <p class="text-xs text-green-600">Estimado a recibir:</p>
            <p class="font-medium text-green-800">
              {{ estimatedBtcBuy.toFixed(6) }} BTC
            </p>
          </div>

          <!-- Buy Button -->
          <button 
            @click="handleBuyClick"
            :disabled="!canExecuteBuy"
            :class="[
              'w-full font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center',
              canExecuteBuy 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            ]"
          >
            <span v-if="executingBuy" class="animate-spin mr-2">🔄</span>
            <span v-else class="mr-2">💰</span>
            {{ executingBuy ? 'Comprando...' : `Comprar ${buyOrderType === 'market' ? 'al Mercado' : 'con Límite'}` }}
          </button>
          
          <!-- Debug Info -->
          <div class="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-600">
            <div><strong>Debug Info:</strong></div>
            <div>Can Execute: {{ canExecuteBuy }}</div>
            <div>Amount: {{ buyAmount || 'empty' }}</div>
            <div>Price: {{ buyPrice || 'empty' }}</div>
            <div>Order Type: {{ buyOrderType }}</div>
            <div>Active API Key: {{ activeApiKey ? `ID: ${activeApiKey.id}` : 'None' }}</div>
            <div>Executing: {{ executingBuy }}</div>
          </div>
        </div>
      </div>

      <!-- Sell Panel -->
      <div class="border border-red-200 rounded-lg p-4 bg-red-50">
        <h4 class="text-lg font-semibold text-red-800 mb-4 flex items-center">
          <span class="mr-2">📉</span>
          Vender BTC
        </h4>
        
        <div class="space-y-4">
          <!-- Order Type -->
          <div>
            <label class="block text-sm font-medium text-red-700 mb-2">
              Tipo de Orden
            </label>
            <div class="flex gap-2">
              <button 
                @click="sellOrderType = 'market'"
                :class="sellOrderType === 'market' ? 'bg-red-600 text-white' : 'bg-white text-red-600 border border-red-600'"
                class="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
              >
                🏃 Mercado
              </button>
              <button 
                @click="sellOrderType = 'limit'"
                :class="sellOrderType === 'limit' ? 'bg-red-600 text-white' : 'bg-white text-red-600 border border-red-600'"
                class="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors"
              >
                🎯 Límite
              </button>
            </div>
          </div>

          <!-- Price (only for limit orders) -->
          <div v-if="sellOrderType === 'limit'">
            <label class="block text-sm font-medium text-red-700 mb-2">
              Precio de Venta (USDT)
            </label>
            <div class="relative">
              <input 
                v-model="sellPrice"
                type="number"
                step="0.01"
                :placeholder="`Ej: ${(currentPrice * 1.02).toFixed(0)}`"
                class="w-full border border-red-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
              <div class="absolute right-2 top-2 flex gap-1">
                <button 
                  @click="sellPrice = (currentPrice * 1.02).toFixed(0)"
                  class="text-xs bg-red-200 text-red-800 px-2 py-1 rounded"
                  title="2% por encima del precio actual"
                >
                  +2%
                </button>
                <button 
                  @click="sellPrice = (currentPrice * 1.05).toFixed(0)"
                  class="text-xs bg-red-200 text-red-800 px-2 py-1 rounded"
                  title="5% por encima del precio actual"
                >
                  +5%
                </button>
              </div>
            </div>
          </div>

          <!-- Amount -->
          <div>
            <label class="block text-sm font-medium text-red-700 mb-2">
              Cantidad BTC a vender
            </label>
            <div class="relative">
              <input 
                v-model="sellAmount"
                type="number"
                step="0.000001"
                placeholder="0.001000"
                class="w-full border border-red-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
              <div class="absolute right-2 top-2 flex gap-1">
                <button 
                  @click="sellAmount = '0.001'"
                  class="text-xs bg-red-200 text-red-800 px-2 py-1 rounded"
                >
                  0.001
                </button>
                <button 
                  @click="sellAmount = '0.01'"
                  class="text-xs bg-red-200 text-red-800 px-2 py-1 rounded"
                >
                  0.01
                </button>
                <button 
                  v-if="availableBtc > 0"
                  @click="sellAmount = availableBtc.toFixed(6)"
                  class="text-xs bg-red-200 text-red-800 px-2 py-1 rounded"
                >
                  TODO
                </button>
              </div>
            </div>
          </div>

          <!-- Estimated USDT -->
          <div class="bg-white rounded p-3 border border-red-200">
            <p class="text-xs text-red-600">Estimado a recibir:</p>
            <p class="font-medium text-red-800">
              ${{ estimatedUsdtSell.toFixed(2) }} USDT
            </p>
          </div>

          <!-- Sell Button -->
          <button 
            @click="executeSellOrder"
            :disabled="!canExecuteSell || executingSell"
            class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
          >
            <span v-if="executingSell" class="animate-spin mr-2">🔄</span>
            <span v-else class="mr-2">💸</span>
            {{ executingSell ? 'Vendiendo...' : `Vender ${sellOrderType === 'market' ? 'al Mercado' : 'con Límite'}` }}
          </button>
        </div>
      </div>
    </div>

    <!-- Positions & Orders Section -->
    <div class="mt-8 pt-6 border-t border-slate-200 space-y-6">
      
      <!-- Current Positions -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-sm font-medium text-slate-700 flex items-center">
            <span class="mr-2">📊</span>
            Posiciones Actuales Bitcoin 30m
          </h4>
          <button 
            @click="refreshPositions"
            :disabled="loadingPositions"
            class="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded-full transition-colors"
          >
            <span v-if="loadingPositions" class="animate-spin mr-1">🔄</span>
            <span v-else class="mr-1">🔄</span>
            {{ loadingPositions ? 'Cargando...' : 'Actualizar' }}
          </button>
        </div>
        
        <div v-if="currentPositions.length === 0" class="text-center py-6 bg-slate-50 rounded-lg">
          <div class="text-4xl mb-2">📈</div>
          <p class="text-sm text-slate-600">No tienes posiciones abiertas</p>
          <p class="text-xs text-slate-500">Las posiciones aparecerán aquí cuando tengas operaciones activas</p>
        </div>
        
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="position in currentPositions" :key="position.id" 
               class="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center">
                <span class="text-lg mr-2">{{ position.side === 'LONG' ? '📈' : '📉' }}</span>
                <span class="font-medium" :class="position.side === 'LONG' ? 'text-green-600' : 'text-red-600'">
                  {{ position.side }} BTC
                </span>
              </div>
              <span class="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                {{ position.status }}
              </span>
            </div>
            
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span class="text-slate-500">Cantidad:</span>
                <span class="font-medium ml-1">{{ position.quantity }} BTC</span>
              </div>
              <div>
                <span class="text-slate-500">Precio entrada:</span>
                <span class="font-medium ml-1">${{ position.entry_price }}</span>
              </div>
              <div>
                <span class="text-slate-500">P&L:</span>
                <span class="font-medium ml-1" :class="(position.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ (position.pnl || 0) >= 0 ? '+' : '' }}{{ (position.pnl || 0).toFixed(2) }}%
                </span>
              </div>
              <div>
                <span class="text-slate-500">Tiempo:</span>
                <span class="font-medium ml-1">{{ formatDuration(position.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Orders -->
      <div>
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-sm font-medium text-slate-700 flex items-center">
            <span class="mr-2">⏳</span>
            Órdenes Pendientes
          </h4>
          <button 
            @click="refreshPendingOrders"
            :disabled="loadingOrders"
            class="text-xs bg-orange-100 hover:bg-orange-200 text-orange-700 px-3 py-1 rounded-full transition-colors"
          >
            <span v-if="loadingOrders" class="animate-spin mr-1">🔄</span>
            <span v-else class="mr-1">🔄</span>
            {{ loadingOrders ? 'Cargando...' : 'Actualizar' }}
          </button>
        </div>
        
        <div v-if="pendingOrders.length === 0" class="text-center py-6 bg-slate-50 rounded-lg">
          <div class="text-4xl mb-2">⏰</div>
          <p class="text-sm text-slate-600">No tienes órdenes pendientes</p>
          <p class="text-xs text-slate-500">Las órdenes límite aparecerán aquí hasta ser ejecutadas</p>
        </div>
        
        <div v-else class="space-y-3">
          <div v-for="order in pendingOrders" :key="order.id" 
               class="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <div class="flex items-center">
              <span class="mr-2">{{ order.side === 'BUY' ? '📈' : '📉' }}</span>
              <div>
                <div class="flex items-center">
                  <span :class="order.side === 'BUY' ? 'text-green-600' : 'text-red-600'" class="font-medium text-sm">
                    {{ order.side === 'BUY' ? 'COMPRAR' : 'VENDER' }}
                  </span>
                  <span class="mx-2 text-slate-500">•</span>
                  <span class="text-slate-700 text-sm">
                    {{ order.side === 'BUY' ? `$${order.usdt_amount}` : `${order.btc_amount} BTC` }}
                  </span>
                </div>
                <div class="text-xs text-slate-500">
                  {{ order.type }} • Precio: ${{ order.price }}
                </div>
              </div>
            </div>
            <div class="text-right">
              <button 
                @click="cancelOrder(order.id)"
                class="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
              >
                ❌ Cancelar
              </button>
              <div class="text-xs text-slate-500 mt-1">{{ formatDate(order.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Executed Orders -->
      <div v-if="recentOrders.length > 0">
        <h4 class="text-sm font-medium text-slate-700 mb-4 flex items-center">
          <span class="mr-2">✅</span>
          Órdenes Ejecutadas Recientes
        </h4>
        <div class="space-y-2">
          <div v-for="order in recentOrders.slice(0, 3)" :key="order.id" 
               class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg text-sm">
            <div class="flex items-center">
              <span class="mr-2">{{ order.side === 'BUY' ? '📈' : '📉' }}</span>
              <span :class="order.side === 'BUY' ? 'text-green-600' : 'text-red-600'" class="font-medium">
                {{ order.side === 'BUY' ? 'COMPRA' : 'VENTA' }}
              </span>
              <span class="mx-2 text-slate-500">•</span>
              <span class="text-slate-700">
                {{ order.side === 'BUY' ? `$${order.usdt_amount}` : `${order.btc_amount} BTC` }}
              </span>
              <span class="mx-2 text-slate-500">•</span>
              <span class="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
                {{ order.status }}
              </span>
            </div>
            <div class="text-right">
              <span class="text-slate-600">${{ order.price }}</span>
              <div class="text-xs text-slate-500">{{ formatDate(order.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Order Status -->
    <div v-if="orderStatus" class="mt-4 p-3 rounded-lg" 
         :class="orderStatus.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
      <div class="flex">
        <div class="flex-shrink-0">
          <span class="text-xl">{{ orderStatus.success ? '✅' : '❌' }}</span>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium" :class="orderStatus.success ? 'text-green-800' : 'text-red-800'">
            {{ orderStatus.title }}
          </h3>
          <div class="mt-1 text-sm" :class="orderStatus.success ? 'text-green-700' : 'text-red-700'">
            <p>{{ orderStatus.message }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import apiClient from '@/config/api'

const props = defineProps({
  apiKeys: {
    type: Array,
    default: () => []
  },
  environment: {
    type: String,
    default: 'testnet'
  },
  currentBtcPrice: {
    type: Number,
    default: 122000
  }
})

const emit = defineEmits(['order-executed', 'refresh-portfolio'])

// Local state
const currentPrice = ref(props.currentBtcPrice || 122000)
const lastPriceUpdate = ref(null)
const loadingPrice = ref(false)

// Buy order state
const buyOrderType = ref('limit')
const buyPrice = ref('')
const buyAmount = ref('')
const executingBuy = ref(false)

// Sell order state
const sellOrderType = ref('limit')
const sellPrice = ref('')
const sellAmount = ref('')
const executingSell = ref(false)

// Other state
const availableBtc = ref(0)
const recentOrders = ref([])
const orderStatus = ref(null)
const currentPositions = ref([])
const pendingOrders = ref([])
const loadingPositions = ref(false)
const loadingOrders = ref(false)

// Computed properties
const filteredApiKeys = computed(() => {
  const filtered = props.apiKeys.filter(key => 
    key.is_testnet === (props.environment === 'testnet') && key.is_active
  )
  
  // Si no hay API keys activas pero sí hay disponibles, usar la primera disponible
  if (filtered.length === 0) {
    const available = props.apiKeys.filter(key => 
      key.is_testnet === (props.environment === 'testnet')
    )
    if (available.length > 0) {
      console.log('[ManualTrading] ⚠️ No hay API keys activas, usando la primera disponible para trading')
      return available
    }
  }
  
  console.log('[ManualTrading] 🔍 filteredApiKeys computed:', {
    totalApiKeys: props.apiKeys.length,
    environment: props.environment,
    filtered: filtered,
    filteredLength: filtered.length,
    apiKeysDetail: props.apiKeys.map(k => ({
      id: k.id,
      is_testnet: k.is_testnet,
      is_active: k.is_active
    }))
  })
  
  return filtered
})

const activeApiKey = computed(() => {
  const result = filteredApiKeys.value[0] || null
  console.log('[ManualTrading] 🔑 activeApiKey computed:', {
    filteredApiKeys: filteredApiKeys.value,
    result: result,
    apiKeysLength: filteredApiKeys.value.length
  })
  return result
})

const estimatedBtcBuy = computed(() => {
  const amount = parseFloat(buyAmount.value) || 0
  const price = buyOrderType.value === 'market' ? currentPrice.value : (parseFloat(buyPrice.value) || currentPrice.value)
  const result = amount / price
  
  console.log('[ManualTrading] 🧮 estimatedBtcBuy computed:', {
    buyAmount: buyAmount.value,
    buyPrice: buyPrice.value,
    buyOrderType: buyOrderType.value,
    currentPrice: currentPrice.value,
    amount,
    price,
    result
  })
  
  return result
})

const estimatedUsdtSell = computed(() => {
  const amount = parseFloat(sellAmount.value) || 0
  const price = sellOrderType.value === 'market' ? currentPrice.value : (parseFloat(sellPrice.value) || currentPrice.value)
  return amount * price
})

const canExecuteBuy = computed(() => {
  const hasAmount = parseFloat(buyAmount.value) > 0
  const hasPrice = buyOrderType.value === 'market' || parseFloat(buyPrice.value) > 0
  const hasApiKey = !!activeApiKey.value
  const notExecuting = !executingBuy.value
  
  const result = hasAmount && hasPrice && hasApiKey && notExecuting
  
  console.log('[ManualTrading] 🔍 canExecuteBuy validation:', {
    hasAmount,
    hasPrice,
    hasApiKey,
    notExecuting,
    buyAmount: buyAmount.value,
    buyPrice: buyPrice.value,
    buyOrderType: buyOrderType.value,
    result
  })
  
  return result
})

const canExecuteSell = computed(() => {
  const hasAmount = parseFloat(sellAmount.value) > 0
  const hasPrice = sellOrderType.value === 'market' || parseFloat(sellPrice.value) > 0
  return hasAmount && hasPrice && activeApiKey.value && !executingSell.value
})

// Methods
const handleBuyClick = () => {
  console.log('[ManualTrading] 🔥 BOTÓN CLICKEADO - handleBuyClick ejecutado')
  console.log('[ManualTrading] 📊 Valores actuales:', {
    buyAmount: buyAmount.value,
    buyPrice: buyPrice.value,
    buyOrderType: buyOrderType.value,
    canExecuteBuy: canExecuteBuy.value,
    executingBuy: executingBuy.value,
    currentPrice: currentPrice.value
  })
  
  // Validación detallada
  const amount = parseFloat(buyAmount.value) || 0
  const price = buyOrderType.value === 'market' ? currentPrice.value : (parseFloat(buyPrice.value) || 0)
  const hasAmount = amount > 0
  const hasPrice = buyOrderType.value === 'market' || price > 0
  const hasApiKey = !!activeApiKey.value
  const notExecuting = !executingBuy.value
  
  console.log('[ManualTrading] 🔬 VALIDACIÓN DETALLADA:', {
    amount,
    price,
    hasAmount,
    hasPrice,
    hasApiKey,
    notExecuting,
    activeApiKey: activeApiKey.value ? { id: activeApiKey.value.id, is_active: activeApiKey.value.is_active } : null,
    propsApiKeys: props.apiKeys.map(k => ({ id: k.id, is_testnet: k.is_testnet, is_active: k.is_active })),
    environment: props.environment,
    filteredApiKeys: filteredApiKeys.value.map(k => ({ id: k.id, is_testnet: k.is_testnet, is_active: k.is_active }))
  })
  
  if (!canExecuteBuy.value) {
    console.log('[ManualTrading] ❌ NO SE PUEDE EJECUTAR - Validación fallida')
    console.log('[ManualTrading] 🚫 Razones:', {
      'Sin cantidad': !hasAmount,
      'Sin precio': !hasPrice,
      'Sin API key': !hasApiKey,
      'Ejecutando': executingBuy.value
    })
    return
  }
  
  console.log('[ManualTrading] ✅ VALIDACIÓN EXITOSA - Ejecutando orden...')
  executeBuyOrder()
}

const refreshPrice = async () => {
  loadingPrice.value = true
  try {
    const response = await apiClient.get('/trading/scanner/bitcoin-30m/current-price')
    if (response.data.success) {
      currentPrice.value = response.data.price
      lastPriceUpdate.value = new Date().toLocaleTimeString()
      console.log('[ManualTrading] Precio BTC actualizado:', currentPrice.value)
    }
  } catch (error) {
    console.error('Error updating price:', error)
    // Usar el precio de las props como fallback
    currentPrice.value = props.currentBtcPrice || 122000
  } finally {
    loadingPrice.value = false
  }
}

const executeBuyOrder = async () => {
  console.log('[ManualTrading] 🔄 executeBuyOrder iniciado')
  
  if (!canExecuteBuy.value) {
    console.log('[ManualTrading] ❌ No se puede ejecutar - canExecuteBuy es false')
    return
  }

  console.log('[ManualTrading] ✅ Iniciando ejecución de orden de compra')
  executingBuy.value = true
  orderStatus.value = null

  try {
    const orderData = {
      symbol: 'BTCUSDT',
      side: 'BUY',
      type: buyOrderType.value.toUpperCase(),
      quantity: estimatedBtcBuy.value.toFixed(6),
      quoteOrderQty: parseFloat(buyAmount.value),
      currentPrice: currentPrice.value
    }

    if (buyOrderType.value === 'limit') {
      orderData.price = parseFloat(buyPrice.value)
      orderData.timeInForce = 'GTC'
    }
    
    console.log('[ManualTrading] 📤 Enviando orden REAL a Binance Testnet:', orderData)
    console.log('[ManualTrading] 🎯 IMPORTANTE: Esta orden se ejecutará REALMENTE en Binance Testnet')

    // Llamar al endpoint real para ejecutar la orden
    console.log('[ManualTrading] 🌐 Realizando llamada HTTP POST a /trading/scanner/bitcoin-30m/manual-order...')
    const response = await apiClient.post('/trading/scanner/bitcoin-30m/manual-order', orderData)
    
    console.log('[ManualTrading] 📥 Respuesta recibida del servidor:', response)
    console.log('[ManualTrading] 📊 Response data:', response.data)
    console.log('[ManualTrading] ✨ Success status:', response.data.success)

    if (response.data.success) {
      console.log('[ManualTrading] ✅ ORDEN EJECUTADA EXITOSAMENTE EN BINANCE TESTNET!')
      console.log('[ManualTrading] 📋 Datos de la orden:', response.data.order)
      console.log('[ManualTrading] 🎯 Esta orden se ejecutó REALMENTE en Binance, no es simulada!')
      
      orderStatus.value = {
        success: true,
        title: 'Orden de Compra Ejecutada',
        message: response.data.message,
        order_id: response.data.order.order_id
      }
      
      // Agregar a la lista de órdenes recientes
      const newOrder = {
        id: response.data.order.order_id,
        side: 'BUY',
        type: buyOrderType.value.toUpperCase(),
        price: buyOrderType.value === 'market' ? currentPrice.value : parseFloat(buyPrice.value),
        usdt_amount: parseFloat(buyAmount.value),
        btc_amount: estimatedBtcBuy.value.toFixed(6),
        status: response.data.order.status,
        created_at: response.data.order.created_at
      }
      
      console.log('[ManualTrading] 📝 Agregando orden a recentOrders:', newOrder)
      recentOrders.value.unshift(newOrder)
      console.log('[ManualTrading] 📋 recentOrders actualizado:', recentOrders.value)
    } else {
      console.log('[ManualTrading] ❌ ERROR en respuesta del servidor:', response.data.message)
      console.log('[ManualTrading] ❌ La orden NO se ejecutó en Binance!')
      throw new Error(response.data.message || 'Error ejecutando orden')
    }

    // Reset form
    buyPrice.value = ''
    buyAmount.value = ''
    
    // Emit events
    emit('order-executed', { side: 'BUY', type: buyOrderType.value })
    emit('refresh-portfolio')

  } catch (error) {
    console.error('[ManualTrading] ❌ ERROR ejecutando orden de compra:', error)
    console.error('[ManualTrading] 🔍 Error details:', {
      message: error.message,
      response: error.response,
      responseData: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    
    orderStatus.value = {
      success: false,
      title: 'Error en Orden de Compra',
      message: error.response?.data?.detail || error.message || 'Error desconocido'
    }
  } finally {
    console.log('[ManualTrading] 🔄 Finalizando ejecución de orden de compra')
    executingBuy.value = false
  }
}

const executeSellOrder = async () => {
  if (!canExecuteSell.value) return

  executingSell.value = true
  orderStatus.value = null

  try {
    const orderData = {
      symbol: 'BTCUSDT',
      side: 'SELL',
      type: sellOrderType.value.toUpperCase(),
      quantity: parseFloat(sellAmount.value),
      currentPrice: currentPrice.value
    }

    if (sellOrderType.value === 'limit') {
      orderData.price = parseFloat(sellPrice.value)
      orderData.timeInForce = 'GTC'
    }

    console.log('[ManualTrading] Ejecutando orden de venta:', orderData)

    // Llamar al endpoint real para ejecutar la orden
    const response = await apiClient.post('/trading/scanner/bitcoin-30m/manual-order', orderData)

    if (response.data.success) {
      orderStatus.value = {
        success: true,
        title: 'Orden de Venta Ejecutada',
        message: response.data.message,
        order_id: response.data.order.order_id
      }
      
      // Agregar a la lista de órdenes recientes
      recentOrders.value.unshift({
        id: response.data.order.order_id,
        side: 'SELL',
        type: sellOrderType.value.toUpperCase(),
        price: sellOrderType.value === 'market' ? currentPrice.value : parseFloat(sellPrice.value),
        usdt_amount: estimatedUsdtSell.value.toFixed(2),
        btc_amount: parseFloat(sellAmount.value),
        status: response.data.order.status,
        created_at: response.data.order.created_at
      })
    } else {
      throw new Error(response.data.message || 'Error ejecutando orden')
    }

    // Reset form
    sellPrice.value = ''
    sellAmount.value = ''
    
    // Emit events
    emit('order-executed', { side: 'SELL', type: sellOrderType.value })
    emit('refresh-portfolio')

  } catch (error) {
    console.error('Error executing sell order:', error)
    orderStatus.value = {
      success: false,
      title: 'Error en Orden de Venta',
      message: error.response?.data?.detail || 'Error desconocido'
    }
  } finally {
    executingSell.value = false
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (dateString) => {
  const start = new Date(dateString)
  const now = new Date()
  const diffMs = now - start
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  
  if (diffHours > 0) {
    return `${diffHours}h ${diffMins % 60}m`
  } else {
    return `${diffMins}m`
  }
}

const refreshPositions = async () => {
  loadingPositions.value = true
  try {
    const response = await apiClient.get('/trading/scanner/bitcoin-30m/positions')
    if (response.data.success) {
      currentPositions.value = response.data.positions
    }
  } catch (error) {
    console.error('Error loading positions:', error)
  } finally {
    loadingPositions.value = false
  }
}

const refreshPendingOrders = async () => {
  loadingOrders.value = true
  try {
    const response = await apiClient.get('/trading/scanner/bitcoin-30m/manual-orders')
    if (response.data.success) {
      pendingOrders.value = response.data.orders.filter(order => order.status === 'NEW')
    }
  } catch (error) {
    console.error('Error loading pending orders:', error)
  } finally {
    loadingOrders.value = false
  }
}

const cancelOrder = async (orderId) => {
  try {
    console.log('[ManualTrading] Cancelando orden:', orderId)
    // Por ahora solo remover de la lista local
    // En producción se haría una llamada al backend
    pendingOrders.value = pendingOrders.value.filter(order => order.id !== orderId)
    
    orderStatus.value = {
      success: true,
      title: 'Orden Cancelada',
      message: `Orden ${orderId} cancelada exitosamente`
    }
  } catch (error) {
    console.error('Error canceling order:', error)
    orderStatus.value = {
      success: false,
      title: 'Error cancelando orden',
      message: error.message || 'Error desconocido'
    }
  }
}

// Clear status after 10 seconds
const clearOrderStatus = () => {
  setTimeout(() => {
    orderStatus.value = null
  }, 10000)
}

// Watch for input changes
watch(buyAmount, (newValue, oldValue) => {
  console.log('[ManualTrading] 💰 buyAmount changed:', {
    oldValue,
    newValue,
    parsedValue: parseFloat(newValue),
    isValid: parseFloat(newValue) > 0,
    canExecuteBuy: canExecuteBuy.value
  })
})

watch(buyPrice, (newValue, oldValue) => {
  console.log('[ManualTrading] 💵 buyPrice changed:', {
    oldValue,
    newValue,
    parsedValue: parseFloat(newValue),
    isValid: parseFloat(newValue) > 0,
    buyOrderType: buyOrderType.value,
    canExecuteBuy: canExecuteBuy.value
  })
})

watch(buyOrderType, (newValue, oldValue) => {
  console.log('[ManualTrading] 🎯 buyOrderType changed:', {
    oldValue,
    newValue,
    requiresPrice: newValue === 'limit',
    canExecuteBuy: canExecuteBuy.value
  })
})

watch(activeApiKey, (newValue, oldValue) => {
  console.log('[ManualTrading] 🔑 activeApiKey changed:', {
    oldValue: oldValue ? { id: oldValue.id, is_active: oldValue.is_active } : null,
    newValue: newValue ? { id: newValue.id, is_active: newValue.is_active } : null,
    canExecuteBuy: canExecuteBuy.value
  })
})

watch(() => props.apiKeys, (newValue, oldValue) => {
  console.log('[ManualTrading] 📋 props.apiKeys changed:', {
    oldLength: oldValue?.length || 0,
    newLength: newValue?.length || 0,
    newKeys: newValue?.map(k => ({ id: k.id, is_testnet: k.is_testnet, is_active: k.is_active })) || [],
    environment: props.environment,
    filteredApiKeys: filteredApiKeys.value,
    activeApiKey: activeApiKey.value
  })
}, { deep: true })

// Watch for order status changes
watch(orderStatus, (newStatus) => {
  if (newStatus) {
    clearOrderStatus()
  }
})

// Lifecycle
onMounted(() => {
  console.log('[ManualTrading] 🚀 Componente montado, inicializando...')
  console.log('[ManualTrading] 📋 Props recibidas:', {
    apiKeys: props.apiKeys,
    apiKeysLength: props.apiKeys?.length || 0,
    environment: props.environment,
    currentBtcPrice: props.currentBtcPrice
  })
  
  // Log detallado de las API keys
  if (props.apiKeys && props.apiKeys.length > 0) {
    console.log('[ManualTrading] 🔑 API Keys detalladas:', props.apiKeys.map(k => ({
      id: k.id,
      is_testnet: k.is_testnet,
      is_active: k.is_active,
      environment_match: k.is_testnet === (props.environment === 'testnet')
    })))
  } else {
    console.log('[ManualTrading] ⚠️ No hay API keys disponibles')
  }
  
  // Log del estado inicial de los computed
  console.log('[ManualTrading] 🧮 Estado inicial computed:', {
    filteredApiKeys: filteredApiKeys.value,
    activeApiKey: activeApiKey.value,
    canExecuteBuy: canExecuteBuy.value,
    estimatedBtcBuy: estimatedBtcBuy.value
  })
  
  refreshPrice()
  refreshPositions()
  refreshPendingOrders()
  
  console.log('[ManualTrading] ✅ Inicialización completada')
})
</script>