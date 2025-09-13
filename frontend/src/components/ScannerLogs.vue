<template>
  <div v-if="showLogs" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h3 class="text-lg font-semibold text-slate-900 mb-6 flex items-center justify-between">
      <div class="flex items-center">
        <span class="text-2xl mr-2">📝</span>
        {{ config.name }} Scanner Logs - Tiempo Real
      </div>
      <button
        @click="refreshLogs"
        class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors duration-200"
      >
        🔄 Actualizar
      </button>
    </h3>

    <div class="space-y-3 max-h-80 overflow-y-auto">
      <div
        v-for="log in logs"
        :key="`${log.timestamp}-${log.message}`"
        :class="`p-3 border-l-4 rounded-r-lg ${getLogClass(log.level)}`"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center mb-1">
              <span class="mr-2">{{ getLogIcon(log.level) }}</span>
              <span :class="`font-semibold text-sm ${getLogTextClass(log.level)}`">
                {{ log.level?.toUpperCase() || 'INFO' }}
              </span>
              <span class="text-xs text-slate-500 ml-2">
                {{ formatLogTime(log.timestamp) }}
              </span>
            </div>
            <p :class="`text-sm ${getLogTextClass(log.level)} leading-relaxed`">
              {{ log.message }}
            </p>
            <div v-if="log.details" class="mt-2 text-xs text-slate-600 bg-white bg-opacity-50 p-2 rounded">
              {{ log.details }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="!logs || logs.length === 0" class="text-center py-8">
        <div class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">📝</span>
        </div>
        <h4 class="text-lg font-semibold text-slate-900 mb-2">No hay logs disponibles</h4>
        <p class="text-slate-600">Los logs del scanner aparecerán aquí cuando el bot esté activo.</p>
      </div>
    </div>

    <!-- Mini stats footer -->
    <div v-if="logs && logs.length > 0" class="mt-4 pt-4 border-t border-slate-200">
      <div class="flex items-center justify-between text-xs text-slate-500">
        <span>{{ logs.length }} logs mostrados</span>
        <span>Última actualización: {{ new Date().toLocaleTimeString() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  config: {
    type: Object,
    required: true
  },
  botStatus: {
    type: Object,
    required: true
  },
  formatLogTime: {
    type: Function,
    required: true
  },
  getLogClass: {
    type: Function,
    required: true
  },
  getLogTextClass: {
    type: Function,
    required: true
  },
  getLogIcon: {
    type: Function,
    required: true
  },
  refreshLogs: {
    type: Function,
    required: true
  }
})

const showLogs = computed(() => {
  return props.botStatus.isRunning || (props.logs && props.logs.length > 0)
})
</script>