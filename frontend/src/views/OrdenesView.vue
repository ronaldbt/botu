<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              📊 Órdenes de Trading
            </h1>
            <p class="text-slate-600">Monitorea y gestiona todas tus operaciones de trading</p>
          </div>
          <div class="flex items-center space-x-4">
            <div class="relative">
              <select 
                v-model="filtroEstado" 
                @change="cargarOrdenes"
                class="appearance-none bg-white border border-slate-300 rounded-xl px-4 py-3 pr-8 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              >
                <option value="">Todos los estados</option>
                <option value="PENDING">Pendientes</option>
                <option value="FILLED">Ejecutadas</option>
                <option value="CANCELLED">Canceladas</option>
                <option value="FAILED">Fallidas</option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
            <div class="relative">
              <input 
                v-model="filtroTicker" 
                @input="cargarOrdenes"
                placeholder="Filtrar por ticker..."
                class="w-64 bg-white border border-slate-300 rounded-xl px-4 py-3 pl-10 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              />
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </div>
            </div>
            <button 
              @click="cargarOrdenes" 
              class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Portfolio Overview -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Balance Total -->
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Balance Total</p>
              <p class="text-3xl font-bold text-slate-900 mt-2">${{ portfolio.total_balance_usdt?.toFixed(2) || '0.00' }}</p>
              <p class="text-xs text-slate-500 mt-1">USDT</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Fondos Disponibles -->
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Disponible</p>
              <p class="text-3xl font-bold text-emerald-600 mt-2">${{ portfolio.available_balance_usdt?.toFixed(2) || '0.00' }}</p>
              <p class="text-xs text-slate-500 mt-1">
                Bloqueado: ${{ portfolio.locked_balance_usdt?.toFixed(2) || '0.00' }}
              </p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-emerald-500 to-green-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <!-- PnL Total -->
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">PnL Total</p>
              <p class="text-3xl font-bold mt-2" :class="portfolio.total_pnl_usdt >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ portfolio.total_pnl_usdt >= 0 ? '+' : '' }}${{ portfolio.total_pnl_usdt?.toFixed(2) || '0.00' }}
              </p>
              <p class="text-xs" :class="portfolio.total_pnl_percentage >= 0 ? 'text-green-500' : 'text-red-500'">
                {{ portfolio.total_pnl_percentage >= 0 ? '+' : '' }}{{ portfolio.total_pnl_percentage?.toFixed(2) || '0' }}%
              </p>
            </div>
            <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="portfolio.total_pnl_usdt >= 0 ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-red-500 to-pink-500'">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <!-- Trading Stats -->
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Win Rate</p>
              <p class="text-3xl font-bold text-blue-600 mt-2">{{ portfolio.win_rate?.toFixed(1) || '0' }}%</p>
              <p class="text-xs text-slate-500 mt-1">
                {{ portfolio.winning_trades || 0 }}W / {{ portfolio.losing_trades || 0 }}L
              </p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Environment Breakdown -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- Testnet Stats -->
        <div class="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl p-6 shadow-lg border border-orange-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-orange-800">🧪 Testnet</h3>
            <span class="bg-orange-200 text-orange-800 px-2 py-1 rounded-full text-xs font-medium">PRUEBAS</span>
          </div>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <p class="text-xs text-orange-700">Balance</p>
              <p class="text-lg font-bold text-orange-900">${{ portfolio.by_environment?.testnet?.balance_usdt?.toFixed(2) || '0.00' }}</p>
            </div>
            <div>
              <p class="text-xs text-orange-700">PnL</p>
              <p class="text-lg font-bold" :class="portfolio.by_environment?.testnet?.pnl_usdt >= 0 ? 'text-green-700' : 'text-red-700'">
                {{ portfolio.by_environment?.testnet?.pnl_usdt >= 0 ? '+' : '' }}${{ portfolio.by_environment?.testnet?.pnl_usdt?.toFixed(2) || '0.00' }}
              </p>
            </div>
            <div>
              <p class="text-xs text-orange-700">Trades</p>
              <p class="text-lg font-bold text-orange-900">{{ portfolio.by_environment?.testnet?.trades || 0 }}</p>
            </div>
          </div>
        </div>

        <!-- Mainnet Stats -->
        <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 shadow-lg border border-green-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-green-800">💰 Mainnet</h3>
            <span class="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-medium">REAL</span>
          </div>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <p class="text-xs text-green-700">Balance</p>
              <p class="text-lg font-bold text-green-900">${{ portfolio.by_environment?.mainnet?.balance_usdt?.toFixed(2) || '0.00' }}</p>
            </div>
            <div>
              <p class="text-xs text-green-700">PnL</p>
              <p class="text-lg font-bold" :class="portfolio.by_environment?.mainnet?.pnl_usdt >= 0 ? 'text-green-700' : 'text-red-700'">
                {{ portfolio.by_environment?.mainnet?.pnl_usdt >= 0 ? '+' : '' }}${{ portfolio.by_environment?.mainnet?.pnl_usdt?.toFixed(2) || '0.00' }}
              </p>
            </div>
            <div>
              <p class="text-xs text-green-700">Trades</p>
              <p class="text-lg font-bold text-green-900">{{ portfolio.by_environment?.mainnet?.trades || 0 }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Ticker</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Tipo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Red</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Cantidad</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Precio</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">PnL</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Fecha</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr v-for="orden in ordenes" :key="orden.id" class="hover:bg-slate-50 transition-colors duration-200">
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm font-semibold text-slate-900">{{ orden.symbol }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium" 
                        :class="orden.side === 'BUY' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'">
                    <div class="w-2 h-2 rounded-full mr-2" 
                         :class="orden.side === 'BUY' ? 'bg-green-400' : 'bg-red-400'"></div>
                    {{ orden.side }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium" 
                        :class="orden.is_testnet 
                          ? 'bg-orange-100 text-orange-800' 
                          : 'bg-green-100 text-green-800'">
                    {{ orden.is_testnet ? '🧪 Testnet' : '💰 Mainnet' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-medium">
                  {{ orden.quantity ? orden.quantity.toFixed(6) : '0.000000' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                  <span v-if="orden.executed_price" class="font-semibold">
                    ${{ orden.executed_price.toFixed(4) }}
                  </span>
                  <span v-else-if="orden.price" class="text-slate-600">
                    ${{ orden.price.toFixed(4) }}
                  </span>
                  <span v-else class="text-slate-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="{
                          'bg-amber-100 text-amber-800': orden.status === 'PENDING',
                          'bg-green-100 text-green-800': orden.status === 'FILLED',
                          'bg-red-100 text-red-800': orden.status === 'CANCELLED' || orden.status === 'REJECTED'
                        }">
                    <div class="w-2 h-2 rounded-full mr-2"
                         :class="{
                           'bg-amber-400': orden.status === 'PENDING',
                           'bg-green-400': orden.status === 'FILLED',
                           'bg-red-400': orden.status === 'CANCELLED' || orden.status === 'REJECTED'
                         }"></div>
                    {{ getEstadoText(orden.status) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <div v-if="orden.pnl_usdt !== null && orden.pnl_usdt !== undefined">
                    <span class="font-semibold" :class="orden.pnl_usdt >= 0 ? 'text-green-600' : 'text-red-600'">
                      {{ orden.pnl_usdt >= 0 ? '+' : '' }}${{ orden.pnl_usdt.toFixed(2) }}
                    </span>
                    <div class="text-xs" :class="orden.pnl_percentage >= 0 ? 'text-green-500' : 'text-red-500'">
                      {{ orden.pnl_percentage >= 0 ? '+' : '' }}{{ orden.pnl_percentage?.toFixed(2) || '0' }}%
                    </div>
                  </div>
                  <span v-else class="text-slate-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ formatDate(orden.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                  <button 
                    v-if="orden.status === 'PENDING'" 
                    @click="cancelarOrden(orden.id)"
                    class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-lg text-xs font-medium transition-colors duration-200"
                  >
                    Cancelar
                  </button>
                  <span v-else class="text-slate-400 text-xs">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-if="ordenes.length === 0" class="text-center py-12">
          <div class="w-16 h-16 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay órdenes</h3>
          <p class="text-slate-600">No se encontraron órdenes con los filtros aplicados.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'

export default {
  name: 'OrdenesView',
  setup() {
    const authStore = useAuthStore()
    const ordenes = ref([])
    const portfolio = ref({})
    const filtroEstado = ref('')
    const filtroTicker = ref('')
    const loading = ref(false)

    const gananciaTotal = computed(() => {
      return ordenes.value.reduce((total, orden) => {
        if (orden.status === 'FILLED' && orden.side === 'SELL' && orden.pnl_usdt) {
          return total + orden.pnl_usdt
        }
        return total
      }, 0)
    })

    const cargarDatos = async () => {
      loading.value = true
      try {
        const headers = { 'Authorization': `Bearer ${authStore.token}` }
        
        // Cargar órdenes
        const ordenesParams = new URLSearchParams()
        if (filtroEstado.value) ordenesParams.append('status', filtroEstado.value)
        if (filtroTicker.value) ordenesParams.append('symbol', filtroTicker.value)
        
        const [ordenesResponse, portfolioResponse] = await Promise.all([
          fetch(`/trading/orders?${ordenesParams}`, { headers }),
          fetch('/trading/portfolio', { headers })
        ])
        
        if (ordenesResponse.ok) {
          ordenes.value = await ordenesResponse.json()
        } else {
          console.error('Error cargando órdenes')
        }
        
        if (portfolioResponse.ok) {
          portfolio.value = await portfolioResponse.json()
        } else {
          console.error('Error cargando portfolio')
        }
        
      } catch (error) {
        console.error('Error:', error)
      } finally {
        loading.value = false
      }
    }

    const cargarOrdenes = cargarDatos

    const cancelarOrden = async (ordenId) => {
      if (!confirm('¿Estás seguro de que quieres cancelar esta orden?')) {
        return
      }

      try {
        const response = await fetch(`/trading/orders/${ordenId}/cancel`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authStore.token}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (response.ok) {
          await cargarOrdenes()
          alert('Orden cancelada exitosamente')
        } else {
          alert('Error cancelando la orden')
        }
      } catch (error) {
        console.error('Error:', error)
        alert('Error cancelando la orden')
      }
    }

    const getEstadoText = (status) => {
      const estados = {
        'PENDING': 'Pendiente',
        'FILLED': 'Ejecutada',
        'PARTIALLY_FILLED': 'Parcial',
        'CANCELLED': 'Cancelada',
        'REJECTED': 'Rechazada'
      }
      return estados[status] || status
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('es-ES')
    }

    onMounted(() => {
      cargarDatos()
    })

    return {
      ordenes,
      portfolio,
      filtroEstado,
      filtroTicker,
      loading,
      gananciaTotal,
      cargarOrdenes,
      cancelarOrden,
      getEstadoText,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>