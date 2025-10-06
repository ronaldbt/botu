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
            <span :class="getCurrentApiKey()?.auto_trading_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  class="px-3 py-1 rounded-full text-sm font-medium">
              {{ getCurrentApiKey()?.auto_trading_enabled ? '🟢 Activo' : '🔴 Inactivo' }}
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
            <div v-if="getCurrentApiKey()" class="flex justify-between text-sm">
              <span class="text-slate-600">Cryptos Habilitadas:</span>
              <div class="font-medium">
                <span v-if="getCurrentApiKey()?.btc_enabled" class="text-orange-600 mr-1">₿</span>
                <span v-if="getCurrentApiKey()?.eth_enabled" class="text-blue-600 mr-1">Ξ</span>
                <span v-if="getCurrentApiKey()?.bnb_enabled" class="text-yellow-600 mr-1">🟡</span>
                <span v-if="!getCurrentApiKey()?.btc_enabled && !getCurrentApiKey()?.eth_enabled && !getCurrentApiKey()?.bnb_enabled" class="text-slate-400">Ninguna</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Balance -->
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-slate-900">Balance</h3>
            <div class="flex items-center gap-2">
              <span v-if="getCurrentApiKey()?.is_testnet" class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">🧪 TESTNET</span>
              <span v-else class="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">💰 MAINNET</span>
              <span class="text-2xl">💰</span>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">USDT Disponible:</span>
              <span class="font-medium">${{ tradingStatus?.available_balance_usdt?.toFixed(2) || '0.00' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Órdenes Hoy:</span>
              <span class="font-medium">{{ tradingStatus?.total_orders_today || 0 }}</span>
            </div>
            <div v-if="getCurrentApiKey()" class="flex justify-between text-sm">
              <span class="text-slate-600">Estado:</span>
              <span :class="getCurrentApiKey()?.connection_status === 'active' ? 'text-green-600' : 'text-red-600'" class="font-medium">
                {{ getCurrentApiKey()?.connection_status === 'active' ? '✅ Conectado' : '❌ Desconectado' }}
              </span>
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
          <div class="flex items-center">
            <h2 class="text-xl font-semibold text-slate-900 flex items-center">
              <span class="text-2xl mr-2">🔑</span>
              API Keys de Binance
            </h2>
            <button
              @click="showApiHelpModal = true"
              class="ml-3 flex items-center justify-center w-6 h-6 bg-blue-500 hover:bg-blue-600 text-white rounded-full transition-colors duration-200 text-sm font-bold"
              title="¿Cómo obtener API Keys?"
            >
              ?
            </button>
          </div>
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
                  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

                    <!-- Bitcoin 30m -->
                    <div class="bg-white p-3 rounded border">
                      <div class="flex items-center justify-between mb-2">
                        <span class="font-medium text-orange-500">₿ Bitcoin 30m</span>
                        <button 
                          @click="toggleCrypto(apiKey, 'btc_30m')" 
                          :class="apiKey.btc_30m_enabled ? 'bg-orange-500 text-white' : 'bg-slate-300 text-slate-600'"
                          class="px-3 py-1 rounded text-xs font-medium transition-colors">
                          {{ apiKey.btc_30m_enabled ? 'ON' : 'OFF' }}
                        </button>
                      </div>
                      <div class="text-xs text-slate-600">
                        Asignado: ${{ (apiKey.btc_30m_allocated_usdt || 0).toFixed(2) }}
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
                <button @click="checkBalances(apiKey)" 
                        :disabled="loadingBalances === apiKey.id"
                        class="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white px-3 py-1 rounded text-sm font-medium transition-colors">
                  {{ loadingBalances === apiKey.id ? '⏳' : '💰' }} Balances
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

    <!-- API Help Modal -->
    <div v-if="showApiHelpModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg w-full max-w-4xl max-h-screen overflow-y-auto">
        <!-- Header fijo -->
        <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
          <div class="flex items-center justify-between">
            <h3 class="text-xl font-semibold text-slate-900 flex items-center">
              🔑 Cómo obtener API Keys de Binance
            </h3>
            <button
              @click="showApiHelpModal = false"
              class="text-slate-400 hover:text-slate-600 transition-colors duration-200"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Contenido scrolleable -->
        <div class="px-6 py-6">
          <!-- Tabs -->
          <div class="mb-6">
            <div class="border-b border-gray-200">
              <nav class="-mb-px flex space-x-8">
                <button
                  @click="activeHelpTab = 'testnet'"
                  :class="[
                    'py-2 px-1 border-b-2 font-medium text-sm',
                    activeHelpTab === 'testnet'
                      ? 'border-emerald-500 text-emerald-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  ]"
                >
                  🧪 Testnet (Recomendado)
                </button>
                <button
                  @click="activeHelpTab = 'mainnet'"
                  :class="[
                    'py-2 px-1 border-b-2 font-medium text-sm',
                    activeHelpTab === 'mainnet'
                      ? 'border-red-500 text-red-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  ]"
                >
                  💰 Mainnet (Expertos)
                </button>
                <button
                  @click="activeHelpTab = 'security'"
                  :class="[
                    'py-2 px-1 border-b-2 font-medium text-sm',
                    activeHelpTab === 'security'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  ]"
                >
                  🔒 Seguridad
                </button>
              </nav>
            </div>
          </div>

          <!-- Testnet Content -->
          <div v-if="activeHelpTab === 'testnet'" class="space-y-6">
            <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <div class="flex items-center mb-2">
                <span class="text-2xl mr-2">✅</span>
                <h4 class="font-semibold text-emerald-800">Testnet - Entorno de Pruebas (RECOMENDADO)</h4>
              </div>
              <p class="text-emerald-700 text-sm">Usa dinero virtual para aprender y probar estrategias sin riesgo. Perfecto para principiantes y para probar nuevas configuraciones.</p>
            </div>

            <div class="space-y-6">
              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg flex items-center mb-4">
                  <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">1</span>
                  Crear cuenta en Binance Testnet
                </h4>
                <div class="space-y-3">
                  <p class="text-gray-700">Ve a la página oficial de Binance Testnet y crea una cuenta gratuita:</p>
                  <div class="bg-gray-50 p-4 rounded-lg">
                    <a 
                      href="https://testnet.binance.vision/" 
                      target="_blank"
                      class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                      🔗 Abrir Binance Testnet
                      <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                      </svg>
                    </a>
                  </div>
                  <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p class="text-blue-800 text-sm"><strong>Nota:</strong> La cuenta de testnet es completamente separada de tu cuenta real de Binance. No necesitas tener una cuenta real.</p>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg flex items-center mb-4">
                  <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">2</span>
                  Crear API Keys en Testnet
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-3">
                    <div class="flex items-start">
                      <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.1</span>
                      <div>
                        <p class="font-medium">Accede a API Management</p>
                        <p class="text-sm text-gray-600">Una vez logueado, ve a tu perfil (esquina superior derecha) > API Management</p>
                      </div>
                    </div>
                    <div class="flex items-start">
                      <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.2</span>
                      <div>
                        <p class="font-medium">Crear nueva API Key</p>
                        <p class="text-sm text-gray-600">Haz clic en "Create API" y elige un nombre descriptivo como "BotU-Trading"</p>
                      </div>
                    </div>
                    <div class="flex items-start">
                      <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.3</span>
                      <div>
                        <p class="font-medium">Configurar permisos</p>
                        <div class="text-sm text-gray-600 space-y-1">
                          <p>✓ <strong>Enable Spot & Margin Trading</strong> (REQUERIDO)</p>
                          <p class="text-red-600">⚠️ NO actives: Futures, Withdrawals, Internal Transfer</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="space-y-3">
                    <div class="flex items-start">
                      <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.4</span>
                      <div>
                        <p class="font-medium">Copiar las keys</p>
                        <p class="text-sm text-gray-600">Guarda tanto la API Key como la Secret Key</p>
                        <p class="text-xs text-orange-600">⚠️ La Secret Key solo se muestra UNA vez</p>
                      </div>
                    </div>
                    <div class="flex items-start">
                      <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.5</span>
                      <div>
                        <p class="font-medium">Verificación</p>
                        <p class="text-sm text-gray-600">Puedes necesitar verificar por email o 2FA</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg flex items-center mb-4">
                  <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">3</span>
                  Obtener fondos virtuales
                </h4>
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div class="flex items-start">
                    <span class="text-2xl mr-3">💰</span>
                    <div>
                      <p class="font-medium text-blue-900 mb-2">Faucet de Testnet</p>
                      <p class="text-blue-800 text-sm">En Testnet puedes obtener BTC, ETH, BNB y USDT virtuales GRATIS desde el "Faucet" en tu wallet. ¡Perfecto para probar el bot sin riesgo!</p>
                      <p class="text-xs text-blue-600 mt-2">Ubicación: Wallet > Spot > Faucet (en la barra lateral)</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Mainnet Content -->
          <div v-if="activeHelpTab === 'mainnet'" class="space-y-6">
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <div class="flex items-center mb-2">
                <span class="text-2xl mr-2">⚠️</span>
                <h4 class="font-semibold text-red-800">Mainnet - Trading con Dinero Real (SOLO EXPERTOS)</h4>
              </div>
              <p class="text-red-700 text-sm">Requiere experiencia previa y puede resultar en pérdidas reales de dinero. Usa solo si ya probaste exitosamente en Testnet.</p>
            </div>

            <div class="space-y-6">
              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg flex items-center mb-4">
                  <span class="bg-red-100 text-red-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">1</span>
                  Cuenta verificada en Binance
                </h4>
                <div class="space-y-3">
                  <p class="text-gray-700">Debes tener una cuenta completamente verificada en Binance:</p>
                  <div class="bg-gray-50 p-4 rounded-lg">
                    <a 
                      href="https://www.binance.com/" 
                      target="_blank"
                      class="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                      🔗 Binance.com
                      <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                      </svg>
                    </a>
                  </div>
                  <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <p class="text-yellow-800 text-sm"><strong>Requisitos:</strong> Verificación de identidad completa, activación de 2FA, y experiencia previa en trading.</p>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg flex items-center mb-4">
                  <span class="bg-red-100 text-red-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">2</span>
                  Crear API Keys (Con extrema precaución)
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-3">
                    <div class="flex items-start">
                      <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.1</span>
                      <div>
                        <p class="font-medium">Ve a API Management</p>
                        <p class="text-sm text-gray-600">Perfil > Seguridad > API Management</p>
                      </div>
                    </div>
                    <div class="flex items-start">
                      <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.2</span>
                      <div>
                        <p class="font-medium">Crear API Key</p>
                        <p class="text-sm text-gray-600">Usar SOLO permisos de "Spot Trading"</p>
                        <p class="text-xs text-red-600">⚠️ NUNCA actives Withdrawals o Futures</p>
                      </div>
                    </div>
                  </div>
                  <div class="space-y-3">
                    <div class="flex items-start">
                      <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.3</span>
                      <div>
                        <p class="font-medium">Restricciones IP</p>
                        <p class="text-sm text-gray-600">MUY RECOMENDADO: Restringir a tu IP actual</p>
                      </div>
                    </div>
                    <div class="flex items-start">
                      <span class="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.4</span>
                      <div>
                        <p class="font-medium">Verificación</p>
                        <p class="text-sm text-gray-600">Confirmar por email y 2FA</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="bg-red-100 border border-red-300 rounded-lg p-4">
                <h4 class="font-semibold text-red-800 mb-3 flex items-center">
                  🚨 ADVERTENCIAS CRÍTICAS
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <ul class="text-sm text-red-700 space-y-1">
                    <li>• NUNCA compartas tus API Keys con nadie</li>
                    <li>• Solo usa fondos que puedes permitirte perder</li>
                    <li>• Empieza con cantidades muy pequeñas (&lt;$50)</li>
                    <li>• Monitorea constantemente las operaciones</li>
                  </ul>
                  <ul class="text-sm text-red-700 space-y-1">
                    <li>• El trading automático SIEMPRE tiene riesgos</li>
                    <li>• Practica primero en Testnet por semanas</li>
                    <li>• Nunca dejes el bot sin supervisión</li>
                    <li>• Ten un plan de salida de emergencia</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- Security Content -->
          <div v-if="activeHelpTab === 'security'" class="space-y-6">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center mb-2">
                <span class="text-2xl mr-2">🔒</span>
                <h4 class="font-semibold text-blue-800">Mejores Prácticas de Seguridad</h4>
              </div>
              <p class="text-blue-700 text-sm">Protege tus API Keys y fondos con estas medidas de seguridad esenciales.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg mb-4 flex items-center">
                  <span class="text-2xl mr-2">🔑</span>
                  Configuración de API Keys
                </h4>
                <div class="space-y-3">
                  <div class="flex items-center">
                    <span class="text-green-600 text-lg mr-2">✓</span>
                    <span class="text-sm">Solo habilita <strong>"Spot Trading"</strong></span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-red-600 text-lg mr-2">✗</span>
                    <span class="text-sm">NUNCA habilites <strong>"Withdrawals"</strong></span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-red-600 text-lg mr-2">✗</span>
                    <span class="text-sm">NUNCA habilites <strong>"Futures"</strong></span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-green-600 text-lg mr-2">✓</span>
                    <span class="text-sm">Usar restricciones de IP</span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-green-600 text-lg mr-2">✓</span>
                    <span class="text-sm">Nombres descriptivos para las APIs</span>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg mb-4 flex items-center">
                  <span class="text-2xl mr-2">📱</span>
                  Autenticación de Dos Factores (2FA)
                </h4>
                <div class="space-y-3">
                  <p class="text-sm text-gray-700">Activar 2FA es <strong>OBLIGATORIO</strong> para:</p>
                  <ul class="text-sm text-gray-600 space-y-1 ml-4">
                    <li>• Crear API Keys</li>
                    <li>• Modificar API Keys</li>
                    <li>• Realizar withdrawals</li>
                    <li>• Acceder desde nuevos dispositivos</li>
                  </ul>
                  <div class="bg-green-50 p-3 rounded">
                    <p class="text-green-800 text-xs"><strong>Recomendación:</strong> Usa Google Authenticator o Authy como app de 2FA.</p>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg mb-4 flex items-center">
                  <span class="text-2xl mr-2">🗺️</span>
                  Restricciones de IP
                </h4>
                <div class="space-y-3">
                  <p class="text-sm text-gray-700">Limita el acceso solo desde IPs confiables:</p>
                  <div class="bg-gray-50 p-3 rounded text-sm">
                    <p><strong>Cómo obtener tu IP:</strong></p>
                    <p>1. Ve a <a href="https://whatismyipaddress.com" target="_blank" class="text-blue-600 hover:underline">whatismyipaddress.com</a></p>
                    <p>2. Copia tu "IPv4 Address"</p>
                    <p>3. Añade esa IP en Binance API Management</p>
                  </div>
                  <div class="bg-yellow-50 p-3 rounded">
                    <p class="text-yellow-800 text-xs"><strong>Nota:</strong> Si tu IP cambia frecuentemente, puedes omitir esta restricción, pero es menos seguro.</p>
                  </div>
                </div>
              </div>

              <div class="bg-white border border-slate-200 rounded-lg p-6">
                <h4 class="font-semibold text-lg mb-4 flex items-center">
                  <span class="text-2xl mr-2">🔐</span>
                  Almacenamiento Seguro
                </h4>
                <div class="space-y-3">
                  <div class="space-y-2">
                    <div class="flex items-center">
                      <span class="text-green-600 text-lg mr-2">✓</span>
                      <span class="text-sm">Guarda las keys en un gestor de contraseñas</span>
                    </div>
                    <div class="flex items-center">
                      <span class="text-green-600 text-lg mr-2">✓</span>
                      <span class="text-sm">Haz respaldo en lugar seguro offline</span>
                    </div>
                    <div class="flex items-center">
                      <span class="text-red-600 text-lg mr-2">✗</span>
                      <span class="text-sm">NUNCA las compartas por WhatsApp/Telegram</span>
                    </div>
                    <div class="flex items-center">
                      <span class="text-red-600 text-lg mr-2">✗</span>
                      <span class="text-sm">NUNCA las guardes en archivos de texto sin cifrar</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 class="font-semibold text-red-800 mb-3">🚨 ¿Qué hacer si sospechas que tu API Key está comprometida?</h4>
              <ol class="text-sm text-red-700 space-y-1">
                <li><strong>1.</strong> Ve INMEDIATAMENTE a Binance y elimina la API Key</li>
                <li><strong>2.</strong> Revisa tu historial de trades y balance</li>
                <li><strong>3.</strong> Cambia tu contraseña de Binance</li>
                <li><strong>4.</strong> Revisa y actualiza tu 2FA</li>
                <li><strong>5.</strong> Contacta al soporte de Binance si detectas actividad sospechosa</li>
              </ol>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-lg">
          <div class="flex justify-between items-center">
            <div class="text-sm text-gray-600">
              📚 <strong>Recomendación:</strong> Siempre prueba primero en Testnet durante al menos 1-2 semanas
            </div>
            <button
              @click="showApiHelpModal = false"
              class="px-6 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Scanner Logs Panel (BTC / ETH / BNB) -->
    <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mt-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-semibold text-slate-900 flex items-center">
          <span class="text-2xl mr-2">📟</span>
          Logs de Scanners (Tiempo real)
        </h2>
        <div class="flex items-center gap-2">
          <button @click="refreshAllScannerLogs" 
                  :disabled="refreshingLogs"
                  :class="refreshingLogs ? 'text-slate-400 cursor-not-allowed' : 'text-blue-600 hover:text-blue-700'"
                  class="text-sm font-medium transition-colors">
            {{ refreshingLogs ? '⏳ Actualizando...' : '🔄 Actualizar' }}
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-slate-200 mb-4">
        <nav class="-mb-px flex space-x-6">
          <button @click="activeScannerTab = 'btc'" :class="activeScannerTab === 'btc' ? 'border-orange-500 text-orange-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" class="py-2 px-1 border-b-2 font-medium text-sm">₿ BTC</button>
          <button @click="activeScannerTab = 'eth'" :class="activeScannerTab === 'eth' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" class="py-2 px-1 border-b-2 font-medium text-sm">Ξ ETH</button>
          <button @click="activeScannerTab = 'bnb'" :class="activeScannerTab === 'bnb' ? 'border-yellow-500 text-yellow-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" class="py-2 px-1 border-b-2 font-medium text-sm">🟡 BNB</button>
        </nav>
      </div>

      <!-- Log console -->
      <div class="bg-slate-900 rounded-lg p-4 font-mono text-xs max-h-96 overflow-y-auto">
        <div v-if="refreshingLogs" class="text-blue-300 text-center py-8">
          ⏳ Cargando logs de scanners...
        </div>
        <div v-else-if="getActiveLogs().length === 0" class="text-slate-400 text-center py-8">
          <div class="mb-2">📝 No hay logs de {{ activeScannerTab.toUpperCase() }} disponibles</div>
          <div class="text-xs">Los logs aparecerán cuando los scanners estén activos</div>
          <div class="text-xs mt-2">Última actualización: {{ lastLogsRefresh ? new Date(lastLogsRefresh).toLocaleTimeString() : 'Nunca' }}</div>
        </div>
        <div v-else>
          <div v-for="(log, idx) in getActiveLogs()" :key="idx" class="mb-2">
            <span class="text-slate-400 mr-2">{{ formatLogTime(log.timestamp) }}</span>
            <span :class="getScannerLogTextClass(log.level)">{{ getScannerLogIcon(log.level) }}</span>
            <span class="text-slate-200 ml-2">{{ log.message }}</span>
            <span v-if="log.details" class="text-slate-400 ml-3">{{ JSON.stringify(log.details) }}</span>
          </div>
        </div>
      </div>

      <div class="mt-3 text-slate-600 text-xs">
        Última actualización: {{ lastLogsRefresh ? new Date(lastLogsRefresh).toLocaleTimeString() : '-' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

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
const showApiHelpModal = ref(false)
const activeHelpTab = ref('testnet')
const testingConnection = ref(null)
const submittingApiKey = ref(false)
const loadingBalances = ref(null)

// Logs de scanners
const activeScannerTab = ref('btc')
const btcLogs = ref([])
const ethLogs = ref([])
const bnbLogs = ref([])
const lastLogsRefresh = ref(null)
const refreshingLogs = ref(false)
let logsInterval = null

// Formulario para agregar API Key

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
  console.log('[TradingAutomatico] loadData() inicio')
  try {
    await Promise.all([
      loadApiKeys(),
      loadTradingStatus(),
      loadOrders()
    ])
    console.log('[TradingAutomatico] loadData() completado', {
      apiKeysCount: apiKeys.value.length,
      tradingStatus: tradingStatus.value,
      ordersCount: orders.value.length
    })
  } catch (error) {
    console.error('Error cargando datos:', error)
  }
}

const loadApiKeys = async () => {
  console.log('[TradingAutomatico] loadApiKeys() -> GET /trading/api-keys')
  try {
    const response = await apiClient.get('/trading/api-keys')
    apiKeys.value = response.data
    console.log('[TradingAutomatico] API keys recibidas:', {
      total: apiKeys.value.length,
      ids: apiKeys.value.map(k => k.id),
      testnets: apiKeys.value.map(k => ({ id: k.id, is_testnet: k.is_testnet, status: k.connection_status }))
    })
  } catch (error) {
    console.error('Error cargando API keys:', error)
  }
}

const loadTradingStatus = async () => {
  console.log('[TradingAutomatico] loadTradingStatus() -> GET /trading/status')
  try {
    const response = await apiClient.get('/trading/status')
    tradingStatus.value = response.data
    console.log('[TradingAutomatico] Estado de trading:', tradingStatus.value)
  } catch (error) {
    console.error('Error cargando estado de trading:', error)
  }
}

const loadOrders = async () => {
  console.log('[TradingAutomatico] loadOrders() -> GET /trading/orders?limit=20')
  try {
    const response = await apiClient.get('/trading/orders?limit=20')
    orders.value = response.data.trades || []
    console.log('[TradingAutomatico] Órdenes recibidas:', orders.value.length)
  } catch (error) {
    console.error('Error cargando órdenes:', error)
  }
}

const submitApiKey = async () => {
  console.log('[TradingAutomatico] submitApiKey() payload:', { ...apiKeyForm })
  submittingApiKey.value = true
  try {
    await apiClient.post('/trading/api-keys', apiKeyForm)
    closeAddApiKeyModal()
    await loadApiKeys()
    alert('✅ API Key agregada exitosamente')
  } catch (error) {
    console.error('Error guardando API key:', error)
    alert('❌ Error guardando API key: ' + (error.response?.data?.detail || error.message))
  } finally {
    submittingApiKey.value = false
    console.log('[TradingAutomatico] submitApiKey() finalizado')
  }
}

const testConnection = async (apiKey) => {
  console.log('[TradingAutomatico] testConnection() para API Key:', apiKey?.id)
  testingConnection.value = apiKey.id
  try {
    const response = await apiClient.post(`/trading/test-connection/${apiKey.id}`, {})
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
    console.log('[TradingAutomatico] testConnection() finalizado para', apiKey?.id)
  }
}

const checkBalances = async (apiKey) => {
  console.log('[TradingAutomatico] checkBalances() para API Key:', apiKey?.id)
  loadingBalances.value = apiKey.id
  try {
    const response = await apiClient.get(`/trading/balances/${apiKey.id}`)
    
    if (response.data.success) {
      const balances = response.data.balances
      let balanceText = `💰 Balances en ${response.data.testnet ? 'Testnet' : 'Mainnet'}:\n\n`
      
      // Mostrar las principales criptos
      const mainCryptos = ['USDT', 'BTC', 'ETH', 'BNB']
      let hasBalances = false
      
      for (const crypto of mainCryptos) {
        const balance = balances.find(b => b.asset === crypto)
        if (balance && parseFloat(balance.free) > 0) {
          balanceText += `${crypto}: ${parseFloat(balance.free).toFixed(8)} (Bloqueado: ${parseFloat(balance.locked).toFixed(8)})\n`
          hasBalances = true
        }
      }
      
      if (!hasBalances) {
        balanceText += `❌ No tienes fondos en las principales criptos (USDT, BTC, ETH, BNB)\n\n`
        if (response.data.testnet) {
          balanceText += `💡 TESTNET: Para obtener fondos ficticios:\n`
          balanceText += `1. Ve a testnet.binance.vision\n`
          balanceText += `2. Wallet > Spot > Faucet\n`
          balanceText += `3. Solicita USDT, BTC, ETH gratis`
        }
      }
      
      alert(balanceText)
    } else {
      alert(`❌ Error consultando balances: ${response.data.message}`)
    }
  } catch (error) {
    console.error('Error consultando balances:', error)
    alert('❌ Error consultando balances: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingBalances.value = null
    console.log('[TradingAutomatico] checkBalances() finalizado para', apiKey?.id)
  }
}

const editApiKey = (apiKey) => {
  console.log('[TradingAutomatico] editApiKey() clic:', apiKey?.id)
  // TODO: Implementar modal de edición
  alert('🚧 Función de edición en desarrollo')
}

const deleteApiKey = async (apiKeyId) => {
  console.log('[TradingAutomatico] deleteApiKey() solicitada para', apiKeyId)
  if (!confirm('¿Estás seguro de que quieres eliminar esta API key?')) return
  
  try {
    await apiClient.delete(`/trading/api-keys/${apiKeyId}`)
    await loadApiKeys()
    alert('✅ API Key eliminada exitosamente')
  } catch (error) {
    console.error('Error eliminando API key:', error)
    alert('❌ Error eliminando API key: ' + (error.response?.data?.detail || error.message))
  }
}

const toggleCrypto = (apiKey, crypto) => {
  console.log('[TradingAutomatico] toggleCrypto() clic', { apiKeyId: apiKey?.id, crypto })
  const cryptoNames = { btc: 'Bitcoin', btc_30m: 'Bitcoin 30m', eth: 'Ethereum', bnb: 'BNB' }
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
  console.log('[TradingAutomatico] updateCryptoAllocation() PUT /trading/crypto-allocation', { apiKeyId, crypto, enabled, allocatedUsdt })
  try {
    const response = await apiClient.put(`/trading/crypto-allocation/${apiKeyId}`, {
      crypto: crypto,
      enabled: enabled,
      allocated_usdt: allocatedUsdt
    })
    
    await loadApiKeys()
    console.log('[TradingAutomatico] updateCryptoAllocation() respuesta:', response.data)
    alert(`✅ ${response.data.message}`)
    
  } catch (error) {
    console.error('Error actualizando crypto allocation:', error)
    alert('❌ Error actualizando configuración: ' + (error.response?.data?.detail || error.message))
  }
}

const closeAddApiKeyModal = () => {
  console.log('[TradingAutomatico] closeAddApiKeyModal()')
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
onMounted(() => {
  console.log('[TradingAutomatico] onMounted - usuario:', authStore.user)
  loadData()
  // Primer fetch de logs y polling cada 30s
  refreshAllScannerLogs()
  logsInterval = setInterval(refreshAllScannerLogs, 30000)
})

// Desmontaje: limpiar intervalos
onUnmounted(() => {
  if (logsInterval) clearInterval(logsInterval)
})

// ----- Funciones de Logs de Scanners -----
const refreshAllScannerLogs = async () => {
  console.log('[TradingAutomatico] refreshAllScannerLogs() iniciando...')
  refreshingLogs.value = true
  
  try {
    console.log('[TradingAutomatico] Llamando a endpoints de logs...')
    
    const [btcRes, ethRes, bnbRes] = await Promise.all([
      apiClient.get('/bitcoin-bot/logs').catch((err) => {
        console.error('[TradingAutomatico] Error en bitcoin-bot/logs:', err)
        return { data: { logs: [] } }
      }),
      apiClient.get('/eth-bot/logs').catch((err) => {
        console.error('[TradingAutomatico] Error en eth-bot/logs:', err)
        return { data: { logs: [] } }
      }),
      apiClient.get('/bnb-bot/logs').catch((err) => {
        console.error('[TradingAutomatico] Error en bnb-bot/logs:', err)
        return { data: { logs: [] } }
      }),
    ])
    
    console.log('[TradingAutomatico] Respuestas recibidas:', {
      btc: btcRes.data,
      eth: ethRes.data, 
      bnb: bnbRes.data
    })
    
    btcLogs.value = btcRes.data?.logs || []
    ethLogs.value = ethRes.data?.logs || []
    bnbLogs.value = bnbRes.data?.logs || []
    lastLogsRefresh.value = Date.now()
    
    console.log('[TradingAutomatico] Logs actualizados:', { 
      btc: btcLogs.value.length, 
      eth: ethLogs.value.length, 
      bnb: bnbLogs.value.length,
      timestamp: new Date(lastLogsRefresh.value).toLocaleTimeString()
    })
    
  } catch (e) {
    console.error('[TradingAutomatico] Error refrescando logs de scanners:', e)
  } finally {
    refreshingLogs.value = false
    console.log('[TradingAutomatico] refreshAllScannerLogs() completado')
  }
}

const getActiveLogs = () => {
  if (activeScannerTab.value === 'eth') return ethLogs.value
  if (activeScannerTab.value === 'bnb') return bnbLogs.value
  return btcLogs.value
}

const formatLogTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', { hour12: false })
}

const getScannerLogTextClass = (level) => {
  switch ((level || '').toLowerCase()) {
    case 'warning': return 'text-yellow-300'
    case 'error': return 'text-red-300'
    case 'success': return 'text-green-300'
    case 'alert': return 'text-purple-300'
    default: return 'text-blue-300'
  }
}

const getScannerLogIcon = (level) => {
  switch ((level || '').toLowerCase()) {
    case 'warning': return '⚠️'
    case 'error': return '❌'
    case 'success': return '✅'
    case 'alert': return '🚨'
    default: return 'ℹ️'
  }
}

const getCurrentApiKey = () => {
  console.log('[TradingAutomatico] getCurrentApiKey() - apiKeys:', apiKeys.value.length)
  // Devolver la primera API key activa, o la primera disponible
  return apiKeys.value.find(key => key.is_active) || apiKeys.value[0] || null
}
</script>