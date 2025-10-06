<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center">
        <h2 class="text-xl font-semibold text-slate-900 flex items-center">
          <span class="text-2xl mr-2">🔑</span>
          API Keys de Binance
          <span v-if="environment === 'testnet'" class="ml-3 text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full font-medium">🧪 TESTNET</span>
          <span v-else class="ml-3 text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full font-medium">💰 MAINNET</span>
        </h2>
        <button
          @click="$emit('show-help')"
          class="ml-3 flex items-center justify-center w-6 h-6 bg-blue-500 hover:bg-blue-600 text-white rounded-full transition-colors duration-200 text-sm font-bold"
          title="¿Cómo obtener API Keys?"
        >
          ?
        </button>
      </div>
      <button 
        @click="$emit('show-add-modal')"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center text-sm font-medium transition-colors">
        <span class="mr-1">➕</span>
        Agregar API Key
      </button>
    </div>

    <!-- API Keys List -->
    <div class="space-y-4">
      <div v-if="apiKeys.length === 0" class="text-center py-8 text-slate-500">
        <span class="text-6xl">🔐</span>
        <p class="text-lg mt-4">No tienes API keys de {{ environment === 'testnet' ? 'Testnet' : 'Mainnet' }} configuradas</p>
        <p class="text-sm">Agrega tus API keys de Binance {{ environment === 'testnet' ? 'Testnet' : 'Mainnet' }} para habilitar el trading automático</p>
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
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
              <div class="bg-slate-50 p-3 rounded-lg">
                <span class="text-slate-600 font-medium">API Key:</span>
                <div class="font-mono text-xs mt-1 break-all text-slate-700">
                  {{ apiKey.api_key_masked || 'No disponible' }}
                </div>
              </div>
              <div class="bg-slate-50 p-3 rounded-lg">
                <span class="text-slate-600 font-medium">Max Posición:</span>
                <div class="font-semibold mt-1 text-slate-800">
                  ${{ (apiKey.max_position_size_usdt || 0).toLocaleString() }}
                </div>
              </div>
              <div class="bg-slate-50 p-3 rounded-lg">
                <span class="text-slate-600 font-medium">Max Posiciones:</span>
                <div class="font-semibold mt-1 text-slate-800">
                  {{ apiKey.max_concurrent_positions || 0 }}
                </div>
              </div>
              <div class="bg-slate-50 p-3 rounded-lg">
                <span class="text-slate-600 font-medium">Trading:</span>
                <div class="mt-1">
                  <span :class="apiKey.auto_trading_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                        class="px-2 py-1 rounded text-xs font-medium">
                    {{ apiKey.auto_trading_enabled ? '✅ Habilitado' : '❌ Deshabilitado' }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Controles por Crypto -->
            <div class="mt-6 p-5 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl border border-slate-200">
              <h4 class="text-sm font-semibold text-slate-800 mb-4 flex items-center">
                <span class="text-lg mr-2">🎛️</span>
                Control por Criptomoneda
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <!-- Bitcoin -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-orange-500 text-lg">₿</span>
                      <span class="font-semibold text-slate-800">Bitcoin</span>
                    </div>
                    <button 
                      @click="$emit('toggle-crypto', apiKey, 'btc')" 
                      :class="apiKey.btc_enabled ? 'bg-orange-500 hover:bg-orange-600 text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-600'"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200">
                      {{ apiKey.btc_enabled ? 'ACTIVO' : 'INACTIVO' }}
                    </button>
                  </div>
                  <div class="space-y-1">
                    <div class="flex justify-between text-xs">
                      <span class="text-slate-500">Asignado:</span>
                      <span class="font-semibold text-slate-700">
                        ${{ (apiKey.btc_allocated_usdt || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </span>
                    </div>
                    <div v-if="apiKey.btc_enabled" class="text-xs text-green-600 font-medium">
                      ✓ Trading habilitado
                    </div>
                    <div v-else class="text-xs text-slate-400">
                      ⏸️ Sin asignación
                    </div>
                  </div>
                </div>

                <!-- Bitcoin 30m -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-orange-400 text-lg">₿</span>
                      <span class="font-semibold text-slate-800">Bitcoin 30m</span>
                    </div>
                    <button 
                      @click="$emit('toggle-crypto', apiKey, 'btc_30m')" 
                      :class="apiKey.btc_30m_enabled ? 'bg-orange-400 hover:bg-orange-500 text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-600'"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200">
                      {{ apiKey.btc_30m_enabled ? 'ACTIVO' : 'INACTIVO' }}
                    </button>
                  </div>
                  <div class="space-y-1">
                    <div class="flex justify-between text-xs">
                      <span class="text-slate-500">Asignado:</span>
                      <span class="font-semibold text-slate-700">
                        ${{ (apiKey.btc_30m_allocated_usdt || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </span>
                    </div>
                    <div v-if="apiKey.btc_30m_enabled" class="text-xs text-green-600 font-medium">
                      ✓ Trading habilitado
                    </div>
                    <div v-else class="text-xs text-slate-400">
                      ⏸️ Sin asignación
                    </div>
                  </div>
                </div>

                <!-- Ethereum -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-blue-500 text-lg">Ξ</span>
                      <span class="font-semibold text-slate-800">Ethereum</span>
                    </div>
                    <button 
                      @click="$emit('toggle-crypto', apiKey, 'eth')" 
                      :class="apiKey.eth_enabled ? 'bg-blue-500 hover:bg-blue-600 text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-600'"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200">
                      {{ apiKey.eth_enabled ? 'ACTIVO' : 'INACTIVO' }}
                    </button>
                  </div>
                  <div class="space-y-1">
                    <div class="flex justify-between text-xs">
                      <span class="text-slate-500">Asignado:</span>
                      <span class="font-semibold text-slate-700">
                        ${{ (apiKey.eth_allocated_usdt || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </span>
                    </div>
                    <div v-if="apiKey.eth_enabled" class="text-xs text-green-600 font-medium">
                      ✓ Trading habilitado
                    </div>
                    <div v-else class="text-xs text-slate-400">
                      ⏸️ Sin asignación
                    </div>
                  </div>
                </div>

                <!-- BNB -->
                <div class="bg-white p-4 rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2">
                      <span class="text-yellow-500 text-lg">🟡</span>
                      <span class="font-semibold text-slate-800">BNB</span>
                    </div>
                    <button 
                      @click="$emit('toggle-crypto', apiKey, 'bnb')" 
                      :class="apiKey.bnb_enabled ? 'bg-yellow-500 hover:bg-yellow-600 text-white' : 'bg-slate-200 hover:bg-slate-300 text-slate-600'"
                      class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200">
                      {{ apiKey.bnb_enabled ? 'ACTIVO' : 'INACTIVO' }}
                    </button>
                  </div>
                  <div class="space-y-1">
                    <div class="flex justify-between text-xs">
                      <span class="text-slate-500">Asignado:</span>
                      <span class="font-semibold text-slate-700">
                        ${{ (apiKey.bnb_allocated_usdt || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                      </span>
                    </div>
                    <div v-if="apiKey.bnb_enabled" class="text-xs text-green-600 font-medium">
                      ✓ Trading habilitado
                    </div>
                    <div v-else class="text-xs text-slate-400">
                      ⏸️ Sin asignación
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 ml-4">
            <button @click="$emit('test-connection', apiKey)" 
                    :disabled="testingConnection === apiKey.id"
                    class="bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center space-x-1">
              <span>{{ testingConnection === apiKey.id ? '⏳' : '🔌' }}</span>
              <span>{{ testingConnection === apiKey.id ? 'Probando...' : 'Test' }}</span>
            </button>
            <button @click="$emit('check-balances', apiKey)" 
                    :disabled="loadingBalances === apiKey.id"
                    class="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center space-x-1">
              <span>{{ loadingBalances === apiKey.id ? '⏳' : '💰' }}</span>
              <span>{{ loadingBalances === apiKey.id ? 'Cargando...' : 'Balances' }}</span>
            </button>
            <button @click="$emit('edit-api-key', apiKey)"
                    class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center space-x-1">
              <span>⚙️</span>
              <span>Config</span>
            </button>
            <button @click="$emit('delete-api-key', apiKey.id)"
                    class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center space-x-1">
              <span>🗑️</span>
              <span>Eliminar</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  apiKeys: {
    type: Array,
    required: true
  },
  testingConnection: {
    type: [String, Number],
    default: null
  },
  loadingBalances: {
    type: [String, Number],
    default: null
  },
  environment: {
    type: String,
    required: true,
    validator: (value) => ['testnet', 'mainnet'].includes(value)
  }
})

defineEmits([
  'show-help',
  'show-add-modal',
  'test-connection',
  'check-balances',
  'edit-api-key',
  'delete-api-key',
  'toggle-crypto'
])
</script>