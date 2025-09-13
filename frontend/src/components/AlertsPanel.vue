<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h3 class="text-lg font-semibold text-slate-900 mb-6 flex items-center">
      <span class="text-2xl mr-2">🚨</span>
      Alertas Recientes - {{ config.name }}
    </h3>

    <div v-if="alerts && alerts.length > 0" class="space-y-4">
      <div
        v-for="alert in alerts.slice(0, 10)"
        :key="alert.id"
        class="border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow duration-200"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center mb-2">
              <span class="text-lg mr-2">{{ getAlertIcon(alert.tipo) }}</span>
              <span :class="`font-semibold text-sm ${getAlertTypeClass(alert.tipo)}`">
                {{ alert.tipo?.toUpperCase() || 'ALERT' }}
              </span>
              <span class="text-xs text-slate-500 ml-2">
                {{ formatAlertTime(alert.timestamp || alert.created_at) }}
              </span>
            </div>
            
            <div class="mb-2">
              <span class="font-medium text-slate-900">{{ alert.symbol || config.defaultSymbol }}</span>
              <span v-if="alert.precio" class="text-slate-600 ml-2">
                @ {{ formatPrice(alert.precio) }}
              </span>
            </div>

            <div v-if="alert.mensaje" class="text-sm text-slate-700 bg-slate-50 p-2 rounded leading-relaxed">
              {{ alert.mensaje.split('\n')[0] }}
            </div>

            <!-- Additional alert details -->
            <div v-if="alert.details" class="mt-2 grid grid-cols-2 gap-4 text-xs text-slate-600">
              <div v-if="alert.details.takeProfit">
                <span class="font-medium">Take Profit:</span> {{ formatPrice(alert.details.takeProfit) }}
              </div>
              <div v-if="alert.details.stopLoss">
                <span class="font-medium">Stop Loss:</span> {{ formatPrice(alert.details.stopLoss) }}
              </div>
            </div>
          </div>

          <!-- Alert status indicator -->
          <div class="flex flex-col items-end">
            <div :class="`w-3 h-3 rounded-full ${getAlertStatusColor(alert.status)}`"></div>
            <span class="text-xs text-slate-500 mt-1">{{ alert.status || 'active' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12">
      <div class="text-6xl mb-4">📭</div>
      <h3 class="text-lg font-semibold text-gray-900 mb-2">Sin alertas</h3>
      <p class="text-gray-600">
        {{ selectedMode === 'manual' 
          ? `Las alertas de compra/venta de ${config.name} aparecerán aquí` 
          : `Los trades automáticos de ${config.name} se mostrarán aquí` 
        }}
      </p>
    </div>

    <!-- Stats footer -->
    <div v-if="alerts && alerts.length > 0" class="mt-6 pt-4 border-t border-slate-200">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
        <div>
          <div class="text-2xl font-bold text-blue-600">{{ alerts.length }}</div>
          <div class="text-xs text-slate-600">Total Alertas</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-emerald-600">{{ getBuyAlerts() }}</div>
          <div class="text-xs text-slate-600">Compras</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-red-600">{{ getSellAlerts() }}</div>
          <div class="text-xs text-slate-600">Ventas</div>
        </div>
        <div>
          <div class="text-2xl font-bold text-purple-600">{{ getActiveAlerts() }}</div>
          <div class="text-xs text-slate-600">Activas</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  config: {
    type: Object,
    required: true
  },
  selectedMode: {
    type: String,
    required: true
  },
  formatPrice: {
    type: Function,
    required: true
  }
})

const getAlertIcon = (type) => {
  switch (type?.toLowerCase()) {
    case 'compra':
    case 'buy': return '🟢'
    case 'venta':
    case 'sell': return '🔴'
    case 'info': return 'ℹ️'
    case 'warning': return '⚠️'
    case 'error': return '❌'
    default: return '🚨'
  }
}

const getAlertTypeClass = (type) => {
  switch (type?.toLowerCase()) {
    case 'compra':
    case 'buy': return 'text-emerald-800'
    case 'venta':
    case 'sell': return 'text-red-800'
    case 'info': return 'text-blue-800'
    case 'warning': return 'text-yellow-800'
    case 'error': return 'text-red-800'
    default: return 'text-slate-800'
  }
}

const getAlertStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'active': return 'bg-emerald-400'
    case 'completed': return 'bg-blue-400'
    case 'cancelled': return 'bg-red-400'
    case 'pending': return 'bg-yellow-400'
    default: return 'bg-slate-400'
  }
}

const formatAlertTime = (timestamp) => {
  try {
    return new Date(timestamp).toLocaleTimeString()
  } catch {
    return timestamp
  }
}

const getBuyAlerts = () => {
  return props.alerts.filter(alert => 
    ['compra', 'buy'].includes(alert.tipo?.toLowerCase())
  ).length
}

const getSellAlerts = () => {
  return props.alerts.filter(alert => 
    ['venta', 'sell'].includes(alert.tipo?.toLowerCase())
  ).length
}

const getActiveAlerts = () => {
  return props.alerts.filter(alert => 
    ['active', 'pending'].includes(alert.status?.toLowerCase())
  ).length
}
</script>