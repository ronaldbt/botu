<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <!-- Estado General -->
    <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center space-x-3">
          <h3 class="text-lg font-semibold text-slate-900">Estado General</h3>
          <div v-if="environment === 'testnet'" class="flex items-center space-x-1 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
            <span class="text-emerald-600 text-sm">🧪</span>
            <span class="text-emerald-700 text-sm font-medium">TESTNET</span>
          </div>
          <div v-else class="flex items-center space-x-1 bg-red-50 px-3 py-1.5 rounded-lg border border-red-200">
            <span class="text-red-600 text-sm">💰</span>
            <span class="text-red-700 text-sm font-medium">MAINNET</span>
          </div>
        </div>
        <div :class="getCurrentApiKey()?.auto_trading_enabled ? 'bg-green-50 border-green-200' : 'bg-slate-50 border-slate-200'"
             class="flex items-center space-x-1 px-3 py-1.5 rounded-lg border">
          <span :class="getCurrentApiKey()?.auto_trading_enabled ? 'text-green-600' : 'text-slate-500'" class="text-sm">
            {{ getCurrentApiKey()?.auto_trading_enabled ? '●' : '○' }}
          </span>
          <span :class="getCurrentApiKey()?.auto_trading_enabled ? 'text-green-700' : 'text-slate-600'" class="text-sm font-medium">
            {{ getCurrentApiKey()?.auto_trading_enabled ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
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
          <div class="font-medium flex flex-wrap gap-1">
            <span v-if="getCurrentApiKey()?.btc_enabled" class="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs font-medium">BTC</span>
            <span v-if="getCurrentApiKey()?.eth_enabled" class="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">ETH</span>
            <span v-if="getCurrentApiKey()?.bnb_enabled" class="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded text-xs font-medium">BNB</span>
            <span v-if="!getCurrentApiKey()?.btc_enabled && !getCurrentApiKey()?.eth_enabled && !getCurrentApiKey()?.bnb_enabled" class="text-slate-400 text-xs">Ninguna</span>
          </div>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-slate-600">API Keys {{ environment === 'testnet' ? 'Testnet' : 'Mainnet' }}:</span>
          <span class="font-medium">{{ filteredApiKeys.length }}</span>
        </div>
      </div>
    </div>

    <!-- Balance -->
    <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-slate-900">Balance</h3>
        <div class="flex items-center gap-3">
          <div v-if="environment === 'testnet'" class="flex items-center space-x-1 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
            <span class="text-emerald-600 text-sm">🧪</span>
            <span class="text-emerald-700 text-sm font-medium">TESTNET</span>
          </div>
          <div v-else class="flex items-center space-x-1 bg-red-50 px-3 py-1.5 rounded-lg border border-red-200">
            <span class="text-red-600 text-sm">💰</span>
            <span class="text-red-700 text-sm font-medium">MAINNET</span>
          </div>
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
          <div :class="isConnected ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
               class="flex items-center space-x-1 px-2 py-0.5 rounded border">
            <span :class="isConnected ? 'text-green-600' : 'text-red-600'" class="text-xs">
              {{ isConnected ? '●' : '●' }}
            </span>
            <span :class="isConnected ? 'text-green-700' : 'text-red-700'" class="text-xs font-medium">
              {{ isConnected ? 'Conectado' : 'Desconectado' }}
            </span>
          </div>
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
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tradingStatus: {
    type: Object,
    required: true
  },
  getCurrentApiKey: {
    type: Function,
    required: true
  },
  environment: {
    type: String,
    required: true,
    validator: (value) => ['testnet', 'mainnet'].includes(value)
  },
  filteredApiKeys: {
    type: Array,
    required: true
  }
})

// Computed para determinar si está conectado
const isConnected = computed(() => {
  const apiKey = props.getCurrentApiKey()
  if (!apiKey) return false
  
  // Considerar conectado si:
  // 1. El connection_status es 'active', O
  // 2. El auto_trading_enabled es true (indica que está funcionando), O
  // 3. Hay cryptos habilitadas (indica configuración activa)
  return apiKey.connection_status === 'active' || 
         apiKey.auto_trading_enabled === true ||
         (apiKey.btc_enabled || apiKey.eth_enabled || apiKey.bnb_enabled)
})
</script>