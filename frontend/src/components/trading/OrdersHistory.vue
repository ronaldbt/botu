<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <h2 class="text-xl font-semibold text-slate-900 flex items-center">
          <span class="text-2xl mr-2">📊</span>
          Historial de Órdenes
        </h2>
        <span v-if="environment === 'testnet'" class="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded-full font-medium">🧪 TESTNET</span>
        <span v-else class="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full font-medium">💰 MAINNET</span>
      </div>
      <button @click="$emit('refresh')" class="text-blue-600 hover:text-blue-700 text-sm font-medium">
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
              <p class="mt-2">No hay órdenes de {{ environment === 'testnet' ? 'Testnet' : 'Mainnet' }} registradas</p>
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
              <span v-if="order.pnl_usdt !== null && order.pnl_usdt !== undefined" 
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
</template>

<script setup>
const props = defineProps({
  orders: {
    type: Array,
    required: true
  },
  formatDate: {
    type: Function,
    required: true
  },
  getStatusColor: {
    type: Function,
    required: true
  },
  getStatusText: {
    type: Function,
    required: true
  },
  environment: {
    type: String,
    required: true,
    validator: (value) => ['testnet', 'mainnet'].includes(value)
  }
})

defineEmits(['refresh'])
</script>