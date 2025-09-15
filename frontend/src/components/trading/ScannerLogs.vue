<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mt-8">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold text-slate-900 flex items-center">
        <span class="text-2xl mr-2">📟</span>
        Logs de Scanners (Tiempo real)
      </h2>
      <div class="flex items-center gap-2">
        <button @click="$emit('refresh')" 
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
        <button @click="$emit('update:active-tab', 'btc')" 
                :class="activeScannerTab === 'btc' ? 'border-orange-500 text-orange-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" 
                class="py-2 px-1 border-b-2 font-medium text-sm">₿ BTC</button>
        <button @click="$emit('update:active-tab', 'eth')" 
                :class="activeScannerTab === 'eth' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" 
                class="py-2 px-1 border-b-2 font-medium text-sm">Ξ ETH</button>
        <button @click="$emit('update:active-tab', 'bnb')" 
                :class="activeScannerTab === 'bnb' ? 'border-yellow-500 text-yellow-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'" 
                class="py-2 px-1 border-b-2 font-medium text-sm">🟡 BNB</button>
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
</template>

<script setup>
const props = defineProps({
  activeScannerTab: {
    type: String,
    required: true
  },
  refreshingLogs: {
    type: Boolean,
    required: true
  },
  lastLogsRefresh: {
    type: Number,
    default: null
  },
  getActiveLogs: {
    type: Function,
    required: true
  },
  formatLogTime: {
    type: Function,
    required: true
  },
  getScannerLogTextClass: {
    type: Function,
    required: true
  },
  getScannerLogIcon: {
    type: Function,
    required: true
  }
})

defineEmits(['refresh', 'update:active-tab'])
</script>