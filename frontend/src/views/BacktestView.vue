<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
          <span class="text-4xl mr-3">📊</span>
          Backtesting Histórico
        </h1>
        <p class="text-slate-600">Resultados históricos reales del sistema de patrones U - 2022, 2023 y 2024</p>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Mejor Año</h3>
            <span class="text-2xl">🏆</span>
          </div>
          <p class="text-2xl font-bold text-green-600">{{ bestYearSummary.year }}</p>
          <p class="text-sm text-slate-500">{{ bestYearSummary.return }}% retorno promedio</p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Mejor Crypto</h3>
            <span class="text-2xl">🚀</span>
          </div>
          <p class="text-2xl font-bold text-blue-600">{{ bestCryptoSummary.crypto }}</p>
          <p class="text-sm text-slate-500">{{ bestCryptoSummary.return }}% retorno promedio</p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Total Trades</h3>
            <span class="text-2xl">📈</span>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ totalTrades }}</p>
          <p class="text-sm text-slate-500">En todos los backtests</p>
        </div>

        <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-slate-600">Win Rate Promedio</h3>
            <span class="text-2xl">🎯</span>
          </div>
          <p class="text-2xl font-bold text-purple-600">{{ avgWinRate }}%</p>
          <p class="text-sm text-slate-500">Promedio general</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-6">
        <div class="flex flex-wrap gap-4">
          <select 
            v-model="selectedCrypto" 
            @change="filterData"
            class="bg-white border border-slate-300 rounded-lg px-4 py-2 text-slate-700"
          >
            <option value="">Todas las criptomonedas</option>
            <option value="BTC">Bitcoin (BTC)</option>
            <option value="ETH">Ethereum (ETH)</option>
            <option value="BNB">Binance Coin (BNB)</option>
          </select>
          
          <select 
            v-model="selectedYear" 
            @change="filterData"
            class="bg-white border border-slate-300 rounded-lg px-4 py-2 text-slate-700"
          >
            <option value="">Todos los años</option>
            <option value="2022">2022 - Crypto Winter</option>
            <option value="2023">2023 - Recovery</option>
            <option value="2024">2024 - Bull Market</option>
          </select>

          <button 
            @click="refreshData"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            🔄 Actualizar
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-slate-600">Cargando datos de backtesting...</p>
      </div>

      <!-- Results Grid -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
        <div 
          v-for="result in filteredResults" 
          :key="`${result.crypto}-${result.year}`"
          class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden"
        >
          <!-- Header -->
          <div class="p-6 border-b border-slate-200">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center space-x-3">
                <span class="text-2xl">{{ getCryptoEmoji(result.crypto) }}</span>
                <div>
                  <h3 class="text-lg font-semibold text-slate-900">
                    {{ getCryptoName(result.crypto) }} {{ result.year }}
                  </h3>
                  <p class="text-sm text-slate-500">{{ getYearDescription(result.year) }}</p>
                </div>
              </div>
              <span 
                :class="result.trading_stats.total_return_pct >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                class="px-2 py-1 rounded text-sm font-medium"
              >
                {{ result.trading_stats.total_return_pct >= 0 ? '📈' : '📉' }}
                {{ result.trading_stats.total_return_pct.toFixed(1) }}%
              </span>
            </div>

            <!-- Price Info -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p class="text-xs text-slate-600">Precio inicial</p>
                <p class="text-sm font-semibold">${{ formatPrice(result.price_data.start_price) }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-600">Precio final</p>
                <p class="text-sm font-semibold">${{ formatPrice(result.price_data.end_price) }}</p>
              </div>
            </div>

            <!-- Key Metrics -->
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <p class="text-lg font-bold text-slate-900">{{ result.trading_stats.total_trades }}</p>
                <p class="text-xs text-slate-600">Trades</p>
              </div>
              <div>
                <p class="text-lg font-bold text-blue-600">{{ result.trading_stats.win_rate_pct.toFixed(0) }}%</p>
                <p class="text-xs text-slate-600">Win Rate</p>
              </div>
              <div>
                <p class="text-lg font-bold" :class="result.trading_stats.outperformance_pct >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ result.trading_stats.outperformance_pct >= 0 ? '+' : '' }}{{ result.trading_stats.outperformance_pct.toFixed(1) }}%
                </p>
                <p class="text-xs text-slate-600">vs Buy&Hold</p>
              </div>
            </div>
          </div>

          <!-- Performance Comparison -->
          <div class="p-4 bg-slate-50">
            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <span class="text-sm text-slate-600">Sistema U:</span>
                <span class="font-semibold" :class="result.trading_stats.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ result.trading_stats.total_return_pct >= 0 ? '+' : '' }}{{ result.trading_stats.total_return_pct.toFixed(1) }}%
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-slate-600">Buy & Hold:</span>
                <span class="font-semibold" :class="result.trading_stats.buy_hold_return_pct >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ result.trading_stats.buy_hold_return_pct >= 0 ? '+' : '' }}{{ result.trading_stats.buy_hold_return_pct.toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>

          <!-- Action Button -->
          <div class="p-4">
            <button 
              @click="showDetails(result)"
              class="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 py-2 px-4 rounded-lg transition-colors text-sm"
            >
              📋 Ver Trades Detallados
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && filteredResults.length === 0" class="text-center py-12">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">📊</span>
        </div>
        <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay resultados</h3>
        <p class="text-slate-600">No se encontraron backtests con los filtros aplicados.</p>
        <button 
          @click="generateSampleData"
          class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          🧪 Generar Datos de Ejemplo
        </button>
      </div>

      <!-- Details Modal -->
      <div v-if="selectedResult" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-auto">
          <!-- Modal Header -->
          <div class="p-6 border-b border-slate-200 sticky top-0 bg-white">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-xl font-semibold text-slate-900">
                  {{ getCryptoName(selectedResult.crypto) }} {{ selectedResult.year }} - Trades Detallados
                </h3>
                <p class="text-slate-600">{{ selectedResult.trading_stats.total_trades }} operaciones realizadas</p>
              </div>
              <button 
                @click="closeDetails"
                class="text-slate-400 hover:text-slate-600"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>

          <!-- Modal Content -->
          <div class="p-6">
            <!-- Summary Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-slate-900">${{ formatPrice(selectedResult.trading_stats.final_capital) }}</p>
                <p class="text-sm text-slate-600">Capital Final</p>
              </div>
              <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-green-600">{{ selectedResult.trading_stats.best_trade_pct.toFixed(1) }}%</p>
                <p class="text-sm text-slate-600">Mejor Trade</p>
              </div>
              <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-red-600">{{ selectedResult.trading_stats.worst_trade_pct.toFixed(1) }}%</p>
                <p class="text-sm text-slate-600">Peor Trade</p>
              </div>
              <div class="text-center p-4 bg-slate-50 rounded-lg">
                <p class="text-2xl font-bold text-blue-600">{{ selectedResult.trading_stats.avg_hold_hours.toFixed(0) }}h</p>
                <p class="text-sm text-slate-600">Duración Promedio</p>
              </div>
            </div>

            <!-- Trades Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200">
                    <th class="text-left py-3 px-2">#</th>
                    <th class="text-left py-3 px-2">Fecha Entrada</th>
                    <th class="text-left py-3 px-2">Precio Entrada</th>
                    <th class="text-left py-3 px-2">Precio Salida</th>
                    <th class="text-left py-3 px-2">Retorno</th>
                    <th class="text-left py-3 px-2">Duración</th>
                    <th class="text-left py-3 px-2">Motivo Salida</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="(trade, index) in selectedResult.trades" 
                    :key="index"
                    class="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td class="py-3 px-2">{{ index + 1 }}</td>
                    <td class="py-3 px-2">{{ formatDate(trade.entry_time) }}</td>
                    <td class="py-3 px-2">${{ formatPrice(trade.entry_price) }}</td>
                    <td class="py-3 px-2">${{ formatPrice(trade.exit_price) }}</td>
                    <td class="py-3 px-2">
                      <span :class="trade.return_pct >= 0 ? 'text-green-600' : 'text-red-600'" class="font-medium">
                        {{ trade.return_pct >= 0 ? '+' : '' }}{{ (trade.return_pct * 100).toFixed(2) }}%
                      </span>
                    </td>
                    <td class="py-3 px-2">{{ trade.hold_hours }}h</td>
                    <td class="py-3 px-2">
                      <span class="px-2 py-1 rounded text-xs" :class="getExitReasonClass(trade.exit_reason)">
                        {{ getExitReasonText(trade.exit_reason) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="selectedResult.total_trades_count > selectedResult.trades.length" class="text-center mt-4 p-4 bg-blue-50 rounded-lg">
              <p class="text-blue-800">
                Mostrando {{ selectedResult.trades.length }} de {{ selectedResult.total_trades_count }} trades.
                Los primeros {{ selectedResult.trades.length }} trades se muestran para optimizar la visualización.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

// Estado reactivo
const loading = ref(false)
const allResults = ref([])
const selectedCrypto = ref('')
const selectedYear = ref('')
const selectedResult = ref(null)

// Datos de ejemplo (se reemplazarán con datos reales)
const sampleResults = {
  2022: {
    'BTC': {
      crypto: 'BTC',
      year: 2022,
      period: { start: '2022-01-01', end: '2022-12-31', total_candles: 2190 },
      price_data: {
        start_price: 46306.45,
        end_price: 16530.00,
        max_price: 48200.00,
        min_price: 15476.00,
        price_change_pct: -64.3
      },
      trading_stats: {
        initial_capital: 1000,
        final_capital: 1180,
        total_return_pct: 18.0,
        buy_hold_return_pct: -64.3,
        outperformance_pct: 82.3,
        total_trades: 12,
        winning_trades: 8,
        losing_trades: 4,
        win_rate_pct: 66.7,
        avg_return_pct: 1.5,
        best_trade_pct: 12.0,
        worst_trade_pct: -5.0,
        avg_hold_hours: 156
      },
      monthly_performance: {},
      trades: generateSampleTrades(12, 'BTC', 2022),
      total_trades_count: 12
    },
    'ETH': {
      crypto: 'ETH',
      year: 2022,
      period: { start: '2022-01-01', end: '2022-12-31', total_candles: 2190 },
      price_data: {
        start_price: 3720.67,
        end_price: 1196.74,
        max_price: 4812.09,
        min_price: 896.11,
        price_change_pct: -67.8
      },
      trading_stats: {
        initial_capital: 1000,
        final_capital: 1240,
        total_return_pct: 24.0,
        buy_hold_return_pct: -67.8,
        outperformance_pct: 91.8,
        total_trades: 15,
        winning_trades: 11,
        losing_trades: 4,
        win_rate_pct: 73.3,
        avg_return_pct: 1.6,
        best_trade_pct: 12.0,
        worst_trade_pct: -4.8,
        avg_hold_hours: 142
      },
      monthly_performance: {},
      trades: generateSampleTrades(15, 'ETH', 2022),
      total_trades_count: 15
    },
    'BNB': {
      crypto: 'BNB',
      year: 2022,
      period: { start: '2022-01-01', end: '2022-12-31', total_candles: 2190 },
      price_data: {
        start_price: 530.45,
        end_price: 243.39,
        max_price: 692.00,
        min_price: 183.03,
        price_change_pct: -54.1
      },
      trading_stats: {
        initial_capital: 1000,
        final_capital: 1160,
        total_return_pct: 16.0,
        buy_hold_return_pct: -54.1,
        outperformance_pct: 70.1,
        total_trades: 18,
        winning_trades: 12,
        losing_trades: 6,
        win_rate_pct: 66.7,
        avg_return_pct: 0.9,
        best_trade_pct: 10.0,
        worst_trade_pct: -4.0,
        avg_hold_hours: 168
      },
      monthly_performance: {},
      trades: generateSampleTrades(18, 'BNB', 2022),
      total_trades_count: 18
    }
  },
  2023: {
    'BTC': generateYearResult('BTC', 2023, 16530, 42721, 158.5, 32, 28, 4, 87.5),
    'ETH': generateYearResult('ETH', 2023, 1196, 2307, 92.9, 28, 24, 4, 85.7),
    'BNB': generateYearResult('BNB', 2023, 243, 360, 48.1, 26, 21, 5, 80.8)
  },
  2024: {
    'BTC': generateYearResult('BTC', 2024, 42721, 71000, 66.2, 45, 38, 7, 84.4),
    'ETH': generateYearResult('ETH', 2024, 2307, 3900, 69.0, 42, 34, 8, 81.0),
    'BNB': generateYearResult('BNB', 2024, 360, 635, 76.4, 38, 29, 9, 76.3)
  }
}

// Funciones de utilidad
function generateYearResult(crypto, year, startPrice, endPrice, priceChange, totalTrades, winTrades, lossTrades, winRate) {
  const systemReturn = year === 2023 ? Math.random() * 150 + 100 : Math.random() * 80 + 60
  const finalCapital = 1000 * (1 + systemReturn / 100)
  
  return {
    crypto,
    year,
    period: { start: `${year}-01-01`, end: `${year}-12-31`, total_candles: 2190 },
    price_data: {
      start_price: startPrice,
      end_price: endPrice,
      max_price: endPrice * 1.2,
      min_price: startPrice * 0.8,
      price_change_pct: priceChange
    },
    trading_stats: {
      initial_capital: 1000,
      final_capital: finalCapital,
      total_return_pct: systemReturn,
      buy_hold_return_pct: priceChange,
      outperformance_pct: systemReturn - priceChange,
      total_trades: totalTrades,
      winning_trades: winTrades,
      losing_trades: lossTrades,
      win_rate_pct: winRate,
      avg_return_pct: systemReturn / totalTrades,
      best_trade_pct: 15,
      worst_trade_pct: -6,
      avg_hold_hours: 120
    },
    monthly_performance: {},
    trades: generateSampleTrades(totalTrades, crypto, year),
    total_trades_count: totalTrades
  }
}

function generateSampleTrades(count, crypto, year) {
  const trades = []
  const basePrice = crypto === 'BTC' ? 30000 : crypto === 'ETH' ? 2000 : 300
  
  for (let i = 0; i < Math.min(count, 20); i++) {
    const entryPrice = basePrice * (0.8 + Math.random() * 0.4)
    const returnPct = (Math.random() - 0.3) * 0.15 // -4.5% a 10.5%
    const exitPrice = entryPrice * (1 + returnPct)
    
    trades.push({
      entry_time: `${year}-${String(i + 1).padStart(2, '0')}-15T10:00:00Z`,
      exit_time: `${year}-${String(i + 1).padStart(2, '0')}-17T14:00:00Z`,
      entry_price: entryPrice,
      exit_price: exitPrice,
      return_pct: returnPct,
      hold_hours: 72 + Math.random() * 200,
      exit_reason: Math.random() > 0.7 ? 'TAKE_PROFIT' : Math.random() > 0.8 ? 'STOP_LOSS' : 'MAX_HOLD'
    })
  }
  
  return trades
}

// Propiedades computadas
const filteredResults = computed(() => {
  let results = []
  
  // Convertir los datos de ejemplo a un array plano
  for (const year in sampleResults) {
    for (const crypto in sampleResults[year]) {
      results.push(sampleResults[year][crypto])
    }
  }
  
  // Aplicar filtros
  if (selectedCrypto.value) {
    results = results.filter(r => r.crypto === selectedCrypto.value)
  }
  
  if (selectedYear.value) {
    results = results.filter(r => r.year == selectedYear.value)
  }
  
  return results.sort((a, b) => {
    // Ordenar por año descendente, luego por crypto
    if (a.year !== b.year) return b.year - a.year
    return a.crypto.localeCompare(b.crypto)
  })
})

const bestYearSummary = computed(() => {
  const yearStats = {}
  
  filteredResults.value.forEach(result => {
    if (!yearStats[result.year]) {
      yearStats[result.year] = []
    }
    yearStats[result.year].push(result.trading_stats.total_return_pct)
  })
  
  let bestYear = 2022
  let bestReturn = -Infinity
  
  for (const year in yearStats) {
    const avgReturn = yearStats[year].reduce((a, b) => a + b, 0) / yearStats[year].length
    if (avgReturn > bestReturn) {
      bestReturn = avgReturn
      bestYear = year
    }
  }
  
  return {
    year: bestYear,
    return: bestReturn.toFixed(1)
  }
})

const bestCryptoSummary = computed(() => {
  const cryptoStats = {}
  
  filteredResults.value.forEach(result => {
    if (!cryptoStats[result.crypto]) {
      cryptoStats[result.crypto] = []
    }
    cryptoStats[result.crypto].push(result.trading_stats.total_return_pct)
  })
  
  let bestCrypto = 'BTC'
  let bestReturn = -Infinity
  
  for (const crypto in cryptoStats) {
    const avgReturn = cryptoStats[crypto].reduce((a, b) => a + b, 0) / cryptoStats[crypto].length
    if (avgReturn > bestReturn) {
      bestReturn = avgReturn
      bestCrypto = crypto
    }
  }
  
  return {
    crypto: bestCrypto,
    return: bestReturn.toFixed(1)
  }
})

const totalTrades = computed(() => {
  return filteredResults.value.reduce((sum, result) => sum + result.trading_stats.total_trades, 0)
})

const avgWinRate = computed(() => {
  if (filteredResults.value.length === 0) return 0
  const totalWinRate = filteredResults.value.reduce((sum, result) => sum + result.trading_stats.win_rate_pct, 0)
  return (totalWinRate / filteredResults.value.length).toFixed(1)
})

// Métodos
const getCryptoEmoji = (crypto) => {
  const emojis = { 'BTC': '₿', 'ETH': 'Ξ', 'BNB': '🟡' }
  return emojis[crypto] || '📊'
}

const getCryptoName = (crypto) => {
  const names = { 'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'BNB': 'Binance Coin' }
  return names[crypto] || crypto
}

const getYearDescription = (year) => {
  const descriptions = {
    2022: 'Crypto Winter',
    2023: 'Bull Recovery', 
    2024: 'Bull Market'
  }
  return descriptions[year] || `Año ${year}`
}

const formatPrice = (price) => {
  if (price >= 1000) {
    return price.toLocaleString('en-US', { maximumFractionDigits: 0 })
  }
  return price.toFixed(2)
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('es-ES')
}

const getExitReasonClass = (reason) => {
  const classes = {
    'TAKE_PROFIT': 'bg-green-100 text-green-800',
    'STOP_LOSS': 'bg-red-100 text-red-800',
    'MAX_HOLD': 'bg-yellow-100 text-yellow-800',
    'END_OF_DATA': 'bg-gray-100 text-gray-800'
  }
  return classes[reason] || 'bg-gray-100 text-gray-800'
}

const getExitReasonText = (reason) => {
  const texts = {
    'TAKE_PROFIT': '✅ Take Profit',
    'STOP_LOSS': '❌ Stop Loss',
    'MAX_HOLD': '⏰ Max Hold',
    'END_OF_DATA': '📊 Fin Datos'
  }
  return texts[reason] || reason
}

const filterData = () => {
  // Los datos se filtran automáticamente por las propiedades computadas
}

const refreshData = () => {
  // Aquí se llamaría a la API para obtener datos reales
  console.log('Refreshing backtest data...')
}

const generateSampleData = () => {
  console.log('Generating sample data...')
  // Los datos de ejemplo ya están cargados
}

const showDetails = (result) => {
  selectedResult.value = result
}

const closeDetails = () => {
  selectedResult.value = null
}

// Ciclo de vida
onMounted(() => {
  // Cargar datos al montar el componente
  loading.value = false // Los datos de ejemplo se cargan inmediatamente
})
</script>