<template>
  <div v-if="statistics" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-6 flex items-center">
      <span class="text-2xl mr-2">📈</span>
      Estadísticas de Sesión - {{ config.name }}
    </h3>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
      <div class="text-center">
        <div class="text-3xl font-bold text-blue-600">{{ statistics.totalAlerts || 0 }}</div>
        <div class="text-sm text-gray-600">Total Alertas</div>
      </div>
      
      <div class="text-center">
        <div class="text-3xl font-bold text-green-600">{{ statistics.buySignals || 0 }}</div>
        <div class="text-sm text-gray-600">Señales Compra</div>
      </div>
      
      <div class="text-center">
        <div class="text-3xl font-bold text-red-600">{{ statistics.sellSignals || 0 }}</div>
        <div class="text-sm text-gray-600">Señales Venta</div>
      </div>
      
      <div class="text-center">
        <div class="text-3xl font-bold text-orange-600">{{ statistics.accuracy || 0 }}%</div>
        <div class="text-sm text-gray-600">Precisión</div>
      </div>
    </div>

    <!-- Portfolio section for automatic mode -->
    <div v-if="selectedMode === 'automatic' && statistics.portfolio" class="mt-6 pt-6 border-t border-gray-200">
      <h4 class="font-semibold text-gray-900 mb-4">Portfolio Testnet</h4>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-gray-50 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">
            ${{ (statistics.portfolio.balance || 0).toLocaleString() }}
          </div>
          <div class="text-sm text-gray-600">Balance USDT</div>
        </div>
        
        <div :class="`${config.colors.bg} rounded-lg p-4 text-center`">
          <div :class="`text-2xl font-bold ${config.colors.text}`">
            {{ getCryptoBalance() }}
          </div>
          <div :class="`text-sm ${config.colors.text} opacity-75`">{{ config.name }}</div>
        </div>
        
        <div class="bg-green-50 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold" :class="getPnLClass()">
            {{ getPnLText() }}
          </div>
          <div class="text-sm text-gray-600">P&L Total</div>
        </div>
      </div>
    </div>

    <!-- Performance metrics -->
    <div v-if="statistics.performance" class="mt-6 pt-6 border-t border-gray-200">
      <h4 class="font-semibold text-gray-900 mb-4">Rendimiento</h4>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="text-center">
          <div class="text-xl font-bold text-emerald-600">{{ statistics.performance.winRate || 0 }}%</div>
          <div class="text-xs text-gray-600">Tasa de Acierto</div>
        </div>
        
        <div class="text-center">
          <div class="text-xl font-bold text-blue-600">{{ statistics.performance.avgProfit || 0 }}%</div>
          <div class="text-xs text-gray-600">Ganancia Promedio</div>
        </div>
        
        <div class="text-center">
          <div class="text-xl font-bold text-purple-600">{{ statistics.performance.maxDrawdown || 0 }}%</div>
          <div class="text-xs text-gray-600">Max Drawdown</div>
        </div>
        
        <div class="text-center">
          <div class="text-xl font-bold text-orange-600">{{ statistics.performance.totalTrades || 0 }}</div>
          <div class="text-xs text-gray-600">Trades Totales</div>
        </div>
      </div>
    </div>

    <!-- Session info -->
    <div class="mt-6 pt-4 border-t border-gray-200">
      <div class="flex items-center justify-between text-xs text-gray-500">
        <span>Sesión iniciada: {{ statistics.sessionStart || 'N/A' }}</span>
        <span>Última actualización: {{ new Date().toLocaleTimeString() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  statistics: {
    type: Object,
    required: true
  },
  config: {
    type: Object,
    required: true
  },
  selectedMode: {
    type: String,
    required: true
  }
})

const getCryptoBalance = () => {
  const portfolio = props.statistics.portfolio
  if (!portfolio) return '0'
  
  // Get crypto balance based on crypto type
  switch (props.config.name.toLowerCase()) {
    case 'bitcoin':
      return (portfolio.btc || 0).toFixed(6)
    case 'ethereum':
      return (portfolio.eth || 0).toFixed(4)
    case 'bnb':
      return (portfolio.bnb || 0).toFixed(2)
    default:
      return '0'
  }
}

const getPnLClass = () => {
  const pnl = props.statistics.portfolio?.pnl || 0
  return pnl >= 0 ? 'text-green-900' : 'text-red-900'
}

const getPnLText = () => {
  const pnl = props.statistics.portfolio?.pnl || 0
  const sign = pnl >= 0 ? '+' : ''
  return `${sign}$${pnl.toLocaleString()}`
}
</script>