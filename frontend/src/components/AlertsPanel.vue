<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h3 class="text-lg font-semibold text-slate-900 mb-6 flex items-center">
      <span class="text-2xl mr-2">🚨</span>
      Alertas Recientes - {{ config.name }}
    </h3>

    <div v-if="alerts && alerts.length > 0" class="max-h-80 overflow-y-auto space-y-3">
      <div
        v-for="alert in alerts.slice(0, 50)"
        :key="alert.id"
        class="border border-slate-200 rounded-lg p-3 hover:shadow-sm transition-shadow duration-200 bg-white"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center">
                <div :class="`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getAlertBadgeClass(alert.type || alert.tipo_alerta)}`">
                  <span class="text-lg mr-2">{{ getAlertIcon(alert.type || alert.tipo_alerta) }}</span>
                  {{ getAlertDisplayText(alert.type || alert.tipo_alerta) }}
                </div>
              </div>
              <div class="text-xs text-slate-500 flex flex-col items-end">
                <span>{{ formatAlertDate(alert.timestamp || alert.formatted_date) }}</span>
                <span class="font-medium">{{ formatAlertTime(alert.timestamp || alert.date_time) }}</span>
              </div>
            </div>
            
            <div class="mb-3 p-2 bg-slate-50 rounded-lg">
              <div class="flex items-center justify-between">
                <span class="font-bold text-lg text-slate-900">{{ alert.symbol || alert.crypto_symbol || config.defaultSymbol }}</span>
                <div class="text-right">
                  <div v-if="(alert.type || alert.tipo_alerta) === 'BUY' && (alert.entry_price || alert.precio_entrada)" class="text-lg font-bold text-green-600">
                    COMPRA: ${{ formatPrice(alert.entry_price || alert.precio_entrada) }}
                  </div>
                  <div v-if="(alert.type || alert.tipo_alerta) === 'SELL' && (alert.exit_price || alert.precio_salida)" class="text-lg font-bold text-red-600">
                    VENTA: ${{ formatPrice(alert.exit_price || alert.precio_salida) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="alert.message || alert.mensaje" class="text-sm text-slate-700 bg-slate-50 p-2 rounded leading-relaxed mb-2">
              {{ (alert.message || alert.mensaje)?.split('\n')[0] }}
            </div>

            <!-- Información detallada de la alerta -->
            <div class="space-y-2">
              <!-- Para alertas de COMPRA -->
              <div v-if="(alert.type || alert.tipo_alerta) === 'BUY'" class="grid grid-cols-2 gap-2 text-xs">
                <div v-if="alert.rupture_level || alert.nivel_ruptura" class="bg-blue-50 p-2 rounded border-l-4 border-blue-400">
                  <span class="font-medium text-blue-800">Nivel Ruptura:</span><br>
                  <span class="text-blue-900 font-bold">${{ formatPrice(alert.rupture_level || alert.nivel_ruptura) }}</span>
                </div>
                <div class="bg-green-50 p-2 rounded border-l-4 border-green-400">
                  <span class="font-medium text-green-800">Estado:</span><br>
                  <span class="text-green-900 font-bold">ESPERANDO VENTA</span>
                </div>
              </div>
              
              <!-- Para alertas de VENTA -->
              <div v-if="(alert.type || alert.tipo_alerta) === 'SELL'" class="grid grid-cols-2 gap-2 text-xs">
                <div v-if="alert.entry_price || alert.precio_entrada" class="bg-green-50 p-2 rounded border-l-4 border-green-400">
                  <span class="font-medium text-green-800">Precio Compra:</span><br>
                  <span class="text-green-900 font-bold">${{ formatPrice(alert.entry_price || alert.precio_entrada) }}</span>
                </div>
                <div v-if="alert.profit_percentage !== undefined && alert.profit_percentage !== null" class="p-2 rounded border-l-4" :class="getResultClass(alert.profit_percentage)">
                  <span class="font-medium">Resultado:</span><br>
                  <span class="font-bold">
                    {{ alert.profit_percentage >= 0 ? '+' : '' }}{{ alert.profit_percentage?.toFixed(2) }}%
                  </span>
                  <div v-if="alert.profit_usd" class="text-xs mt-1">
                    {{ alert.profit_usd >= 0 ? '+' : '' }}${{ alert.profit_usd?.toFixed(2) }}
                  </div>
                </div>
              </div>
              
              <!-- Para otros tipos de alerta -->
              <div v-if="!['BUY', 'SELL'].includes(alert.type || alert.tipo_alerta)" class="bg-gray-50 p-2 rounded border-l-4 border-gray-400">
                <span class="font-medium text-gray-800">Info:</span><br>
                <span class="text-gray-900">{{ alert.message || alert.mensaje }}</span>
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
  switch (type?.toUpperCase()) {
    case 'COMPRA':
    case 'BUY': return '📈'
    case 'VENTA':
    case 'SELL': return '📉'
    case 'INFO': return 'ℹ️'
    case 'WARNING': return '⚠️'
    case 'ERROR': return '❌'
    default: return '🚨'
  }
}

const getAlertDisplayText = (type) => {
  switch (type?.toUpperCase()) {
    case 'COMPRA':
    case 'BUY': return 'COMPRA'
    case 'VENTA':
    case 'SELL': return 'VENTA'
    case 'INFO': return 'INFO'
    case 'WARNING': return 'ADVERTENCIA'
    case 'ERROR': return 'ERROR'
    default: return 'ALERTA'
  }
}

const getAlertBadgeClass = (type) => {
  switch (type?.toUpperCase()) {
    case 'COMPRA':
    case 'BUY': return 'bg-green-100 text-green-800 border border-green-200'
    case 'VENTA':
    case 'SELL': return 'bg-red-100 text-red-800 border border-red-200'
    case 'INFO': return 'bg-blue-100 text-blue-800 border border-blue-200'
    case 'WARNING': return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    case 'ERROR': return 'bg-red-100 text-red-800 border border-red-200'
    default: return 'bg-slate-100 text-slate-800 border border-slate-200'
  }
}

const getResultClass = (profitPercentage) => {
  if (profitPercentage >= 0) {
    return 'bg-green-50 border-green-400 text-green-800'
  } else {
    return 'bg-red-50 border-red-400 text-red-800'
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
    if (timestamp?.includes('UTC')) {
      return timestamp
    }
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      timeZone: 'UTC',
      timeZoneName: 'short'
    })
  } catch {
    return timestamp || 'N/A'
  }
}

const formatAlertDate = (timestamp) => {
  try {
    if (timestamp?.includes('/')) {
      return timestamp.split(' ')[0]
    }
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      timeZone: 'UTC'
    })
  } catch {
    return 'N/A'
  }
}

const getBuyAlerts = () => {
  return props.alerts.filter(alert => 
    ['COMPRA', 'BUY'].includes((alert.type || alert.tipo_alerta)?.toUpperCase())
  ).length
}

const getSellAlerts = () => {
  return props.alerts.filter(alert => 
    ['VENTA', 'SELL'].includes((alert.type || alert.tipo_alerta)?.toUpperCase())
  ).length
}

const getActiveAlerts = () => {
  return props.alerts.filter(alert => 
    ['active', 'pending'].includes(alert.status?.toLowerCase())
  ).length
}
</script>