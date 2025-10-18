<!-- components/trading/PaxgPortfolio.vue -->
<template>
  <div class="bg-white rounded-lg border border-slate-200 p-4">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-2">
        <span class="text-yellow-500 text-lg">🥇</span>
        <h3 class="font-semibold text-slate-800">Portfolio PAXG</h3>
      </div>
      <button
        @click="refreshBalances"
        :disabled="loading"
        class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {{ loading ? 'Cargando...' : 'Actualizar' }}
      </button>
    </div>
    
    <!-- Balance Info -->
    <div class="grid grid-cols-2 gap-4 mb-4">
      <div class="text-center">
        <div class="text-2xl font-bold text-slate-900">
          ${{ totalValue.toFixed(2) }}
        </div>
        <div class="text-xs text-slate-500">Valor Total</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold" :class="totalPnL >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ totalPnL >= 0 ? '+' : '' }}${{ totalPnL.toFixed(2) }}
        </div>
        <div class="text-xs text-slate-500">PnL Total</div>
      </div>
    </div>
    
    <!-- Balances Detail -->
    <div class="space-y-2">
      <div v-for="balance in balances" :key="balance.asset" class="flex justify-between items-center py-2 border-b border-slate-100 last:border-b-0">
        <div class="flex items-center space-x-2">
          <span class="text-sm font-medium text-slate-700">{{ balance.asset }}</span>
          <span class="text-xs text-slate-500">{{ balance.free.toFixed(4) }}</span>
        </div>
        <div class="text-right">
          <div class="text-sm font-medium text-slate-900">
            ${{ balance.usd_value.toFixed(2) }}
          </div>
          <div class="text-xs text-slate-500">
            {{ balance.free.toFixed(4) }} {{ balance.asset }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- No balances message -->
    <div v-if="balances.length === 0 && !loading" class="text-center py-4 text-slate-500">
      <div class="text-sm">No hay balances disponibles</div>
      <div class="text-xs mt-1">Verifica tu API key de Binance</div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="text-center py-4">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
      <div class="text-sm text-slate-500 mt-2">Cargando balances...</div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/authStore'
import apiClient from '@/config/api'

export default {
  name: 'PaxgPortfolio',
  props: {
    apiKeyId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const authStore = useAuthStore()
    
    // Estado reactivo
    const balances = ref([])
    const loading = ref(false)
    const currentPaxgPrice = ref(2500) // Precio por defecto
    
    // Computed properties
    const totalValue = computed(() => {
      return balances.value.reduce((total, balance) => total + balance.usd_value, 0)
    })
    
    const totalPnL = computed(() => {
      // Para PAXG, el PnL se calcularía basado en las órdenes de trading
      // Por ahora retornamos 0, pero se podría integrar con el historial de trades
      return 0
    })
    
    // Métodos
    const refreshBalances = async () => {
      if (!props.apiKeyId) return
      
      loading.value = true
      try {
        const response = await apiClient.get(`/trading/balances/${props.apiKeyId}`)
        
        if (response.data.success) {
          const rawBalances = response.data.balances || []
          
          // Filtrar solo balances con valor > 0 y calcular valores en USD
          const filteredBalances = rawBalances
            .filter(balance => parseFloat(balance.free) > 0 || parseFloat(balance.locked) > 0)
            .map(balance => {
              const total = parseFloat(balance.free) + parseFloat(balance.locked)
              let usd_value = 0
              
              if (balance.asset === 'USDT') {
                usd_value = total
              } else if (balance.asset === 'PAXG') {
                usd_value = total * currentPaxgPrice.value
              }
              
              return {
                asset: balance.asset,
                free: parseFloat(balance.free),
                locked: parseFloat(balance.locked),
                total: total,
                usd_value: usd_value
              }
            })
          
          balances.value = filteredBalances
        }
      } catch (error) {
        console.error('Error cargando balances PAXG:', error)
      } finally {
        loading.value = false
      }
    }
    
    const loadCurrentPaxgPrice = async () => {
      try {
        const price = await apiClient.get('/trading/scanner/paxg-mainnet/current-price')
        if (price.data.success) {
          currentPaxgPrice.value = price.data.price
        }
      } catch (error) {
        console.error('Error obteniendo precio PAXG:', error)
      }
    }
    
    // Lifecycle
    onMounted(async () => {
      await loadCurrentPaxgPrice()
      await refreshBalances()
    })
    
    return {
      balances,
      loading,
      totalValue,
      totalPnL,
      refreshBalances
    }
  }
}
</script>
