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
                <option value="completed">Completadas</option>
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
              <select 
                v-model="filtroTipo" 
                @change="cargarOrdenes"
                class="appearance-none bg-white border border-slate-300 rounded-xl px-4 py-3 pr-8 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              >
                <option value="">Todos los tipos</option>
                <option value="BUY">Compras</option>
                <option value="SELL">Ventas</option>
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

      <!-- Orders Summary -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- Buy Orders -->
        <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 shadow-lg border border-green-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-green-800">📈 Compras</h3>
            <span class="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
              {{ ordenes.filter(o => o.side === 'BUY').length }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-green-700">Ejecutadas</p>
              <p class="text-lg font-bold text-green-900">
                {{ ordenes.filter(o => o.side === 'BUY' && (o.status === 'FILLED' || o.status === 'completed')).length }}
              </p>
            </div>
            <div>
              <p class="text-xs text-green-700">Pendientes</p>
              <p class="text-lg font-bold text-green-900">
                {{ ordenes.filter(o => o.side === 'BUY' && o.status === 'PENDING').length }}
              </p>
            </div>
          </div>
        </div>

        <!-- Sell Orders -->
        <div class="bg-gradient-to-br from-red-50 to-pink-50 rounded-2xl p-6 shadow-lg border border-red-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-red-800">📉 Ventas</h3>
            <span class="bg-red-200 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
              {{ ordenes.filter(o => o.side === 'SELL').length }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-red-700">Ejecutadas</p>
              <p class="text-lg font-bold text-red-900">
                {{ ordenes.filter(o => o.side === 'SELL' && (o.status === 'FILLED' || o.status === 'completed')).length }}
              </p>
            </div>
            <div>
              <p class="text-xs text-red-700">Pendientes</p>
              <p class="text-lg font-bold text-red-900">
                {{ ordenes.filter(o => o.side === 'SELL' && o.status === 'PENDING').length }}
              </p>
            </div>
          </div>
        </div>

        <!-- Total Orders -->
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 shadow-lg border border-blue-200">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-blue-800">📊 Total</h3>
            <span class="bg-blue-200 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {{ ordenes.length }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-blue-700">Completadas</p>
              <p class="text-lg font-bold text-blue-900">
                {{ ordenes.filter(o => o.status === 'completed').length }}
              </p>
            </div>
            <div>
              <p class="text-xs text-blue-700">Ejecutadas</p>
              <p class="text-lg font-bold text-blue-900">
                {{ ordenes.filter(o => o.status === 'FILLED').length }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Mainnet Stats -->
      <div class="grid grid-cols-1 gap-6 mb-8">
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
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">ID</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Par</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Tipo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Cantidad</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Precio</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Total</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Comisión</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">PnL</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Fecha</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr v-for="orden in ordenes" :key="orden.id" class="hover:bg-slate-50 transition-colors duration-200">
                <!-- ID -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span class="text-xs font-mono text-slate-600">#{{ orden.id }}</span>
                    <span v-if="orden.binance_order_id" class="text-xs font-mono text-slate-400">
                      Binance: {{ orden.binance_order_id }}
                    </span>
                  </div>
                </td>
                
                <!-- Par -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex flex-col">
                    <span class="text-sm font-semibold text-slate-900">{{ orden.symbol }}</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium mt-1 bg-green-100 text-green-800">
                      💰 Mainnet
                    </span>
                  </div>
                </td>
                
                <!-- Tipo -->
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
                
                <!-- Cantidad -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-medium">
                  <div class="flex flex-col">
                    <span>{{ (orden.executed_quantity || orden.quantity || 0).toFixed(8) }}</span>
                    <span v-if="orden.executed_quantity && orden.quantity && orden.executed_quantity !== orden.quantity" 
                          class="text-xs text-slate-500">
                      ({{ orden.quantity.toFixed(8) }})
                    </span>
                  </div>
                </td>
                
                <!-- Precio -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                  <div class="flex flex-col">
                    <span v-if="orden.executed_price" class="font-semibold">
                      ${{ orden.executed_price.toFixed(2) }}
                    </span>
                    <span v-else-if="orden.price" class="text-slate-600">
                      ${{ orden.price.toFixed(2) }}
                    </span>
                    <span v-else class="text-slate-400">-</span>
                    <span class="text-xs text-slate-500">{{ orden.order_type }}</span>
                  </div>
                </td>
                
                <!-- Total -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-medium">
                  <div v-if="orden.executed_price && orden.executed_quantity">
                    ${{ (orden.executed_price * orden.executed_quantity).toFixed(2) }}
                  </div>
                  <div v-else-if="orden.price && orden.quantity">
                    ${{ (orden.price * orden.quantity).toFixed(2) }}
                  </div>
                  <span v-else class="text-slate-400">-</span>
                </td>
                
                <!-- Comisión -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  <div v-if="orden.commission && orden.commission > 0">
                    <span class="font-medium">{{ orden.commission.toFixed(8) }}</span>
                    <span class="text-xs text-slate-500">{{ orden.commission_asset }}</span>
                  </div>
                  <span v-else class="text-slate-400">-</span>
                </td>
                
                <!-- Estado -->
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="{
                          'bg-amber-100 text-amber-800': orden.status === 'PENDING',
                          'bg-green-100 text-green-800': orden.status === 'FILLED',
                          'bg-blue-100 text-blue-800': orden.status === 'completed',
                          'bg-red-100 text-red-800': orden.status === 'CANCELLED' || orden.status === 'REJECTED'
                        }">
                    <div class="w-2 h-2 rounded-full mr-2"
                         :class="{
                           'bg-amber-400': orden.status === 'PENDING',
                           'bg-green-400': orden.status === 'FILLED' || orden.status === 'completed',
                           'bg-red-400': orden.status === 'CANCELLED' || orden.status === 'REJECTED'
                         }"></div>
                    {{ getEstadoText(orden.status) }}
                  </span>
                </td>
                
                <!-- PnL -->
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
                
                <!-- Fecha -->
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  <div class="flex flex-col">
                    <span>{{ formatDate(orden.created_at) }}</span>
                    <span v-if="orden.executed_at && orden.executed_at !== orden.created_at" 
                          class="text-xs text-slate-500">
                      Ejecutado: {{ formatDate(orden.executed_at) }}
                    </span>
                  </div>
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
import apiClient from '@/config/api'

export default {
  name: 'OrdenesView',
  setup() {
    const authStore = useAuthStore()
    const ordenes = ref([])
    const portfolio = ref({})
    const filtroEstado = ref('')
    const filtroTipo = ref('')
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
      console.log('🔄 [OrdenesView] Iniciando carga de datos...')
      console.log('📝 [OrdenesView] Filtros aplicados:', {
        estado: filtroEstado.value,
        tipo: filtroTipo.value,
        ticker: filtroTicker.value
      })
      
      loading.value = true
      try {
        // Construir parámetros de consulta
        const ordenesParams = new URLSearchParams()
        if (filtroEstado.value) ordenesParams.append('status', filtroEstado.value)
        if (filtroTipo.value) ordenesParams.append('side', filtroTipo.value)
        if (filtroTicker.value) ordenesParams.append('symbol', filtroTicker.value)
        
        const ordenesUrl = `/trading/orders${ordenesParams.toString() ? '?' + ordenesParams.toString() : ''}`
        const portfolioUrl = '/trading/portfolio'
        
        console.log('🌐 [OrdenesView] URLs a consultar:', {
          ordenes: ordenesUrl,
          portfolio: portfolioUrl
        })
        
        console.log('🔑 [OrdenesView] Token de autenticación:', authStore.token ? 'Presente' : 'NO PRESENTE')
        
        // Cargar órdenes y portfolio en paralelo
        console.log('📡 [OrdenesView] Realizando peticiones al backend...')
        
        const [ordenesResponse, portfolioResponse] = await Promise.all([
          apiClient.get(ordenesUrl).catch(err => {
            console.error('❌ [OrdenesView] Error en petición de órdenes:', err)
            console.error('❌ [OrdenesView] Detalles del error de órdenes:', {
              message: err.message,
              response: err.response?.data,
              status: err.response?.status,
              config: err.config
            })
            return { error: true, err }
          }),
          apiClient.get(portfolioUrl).catch(err => {
            console.error('❌ [OrdenesView] Error en petición de portfolio:', err)
            console.error('❌ [OrdenesView] Detalles del error de portfolio:', {
              message: err.message,
              response: err.response?.data,
              status: err.response?.status,
              config: err.config
            })
            return { error: true, err }
          })
        ])
        
        console.log('📥 [OrdenesView] Respuestas recibidas del backend')
        
        // Procesar respuesta de órdenes
        if (ordenesResponse && !ordenesResponse.error) {
          console.log('✅ [OrdenesView] Respuesta de órdenes OK')
          console.log('📊 [OrdenesView] Datos de órdenes:', ordenesResponse.data)
          console.log('📊 [OrdenesView] Tipo de datos recibidos:', typeof ordenesResponse.data)
          console.log('📊 [OrdenesView] Es array?:', Array.isArray(ordenesResponse.data))
          console.log('📊 [OrdenesView] Cantidad de órdenes:', Array.isArray(ordenesResponse.data) ? ordenesResponse.data.length : 'No es array')
          
          ordenes.value = ordenesResponse.data
          console.log('✅ [OrdenesView] Órdenes guardadas en state:', ordenes.value)
        } else {
          console.error('❌ [OrdenesView] Error cargando órdenes - respuesta no OK')
          ordenes.value = []
        }
        
        // Procesar respuesta de portfolio
        if (portfolioResponse && !portfolioResponse.error) {
          console.log('✅ [OrdenesView] Respuesta de portfolio OK')
          console.log('💼 [OrdenesView] Datos de portfolio:', portfolioResponse.data)
          portfolio.value = portfolioResponse.data
          console.log('✅ [OrdenesView] Portfolio guardado en state:', portfolio.value)
        } else {
          console.error('❌ [OrdenesView] Error cargando portfolio - respuesta no OK')
          portfolio.value = {}
        }
        
        console.log('📊 [OrdenesView] Estado final:', {
          ordenesCount: ordenes.value.length,
          portfolioKeys: Object.keys(portfolio.value)
        })
        
      } catch (error) {
        console.error('❌ [OrdenesView] Error general capturado:', error)
        console.error('❌ [OrdenesView] Stack trace:', error.stack)
      } finally {
        loading.value = false
        console.log('✅ [OrdenesView] Carga de datos finalizada')
      }
    }

    const cargarOrdenes = cargarDatos

    const cancelarOrden = async (ordenId) => {
      console.log('🚫 [OrdenesView] Intentando cancelar orden:', ordenId)
      
      if (!confirm('¿Estás seguro de que quieres cancelar esta orden?')) {
        console.log('⏭️ [OrdenesView] Cancelación abortada por el usuario')
        return
      }

      try {
        console.log('📡 [OrdenesView] Enviando petición de cancelación al backend...')
        const response = await apiClient.post(`/trading/orders/${ordenId}/cancel`)
        
        console.log('✅ [OrdenesView] Orden cancelada exitosamente:', response.data)
        await cargarOrdenes()
        alert('Orden cancelada exitosamente')
      } catch (error) {
        console.error('❌ [OrdenesView] Error cancelando la orden:', error)
        console.error('❌ [OrdenesView] Detalles del error:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        alert('Error cancelando la orden: ' + (error.response?.data?.detail || error.message))
      }
    }

    const getEstadoText = (status) => {
      const estados = {
        'PENDING': 'Pendiente',
        'FILLED': 'Ejecutada',
        'completed': 'Completada',
        'PARTIALLY_FILLED': 'Parcial',
        'CANCELLED': 'Cancelada',
        'REJECTED': 'Rechazada',
        'FAILED': 'Fallida'
      }
      return estados[status] || status
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('es-ES')
    }

    onMounted(() => {
      console.log('🚀 [OrdenesView] Componente montado, iniciando carga inicial de datos...')
      console.log('👤 [OrdenesView] Usuario autenticado:', authStore.user)
      console.log('🔑 [OrdenesView] Token presente:', !!authStore.token)
      cargarDatos()
    })

    return {
      ordenes,
      portfolio,
      filtroEstado,
      filtroTipo,
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