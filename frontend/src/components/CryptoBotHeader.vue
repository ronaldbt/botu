<template>
  <div class="mb-8">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
      <div>
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
          <span class="text-4xl mr-3" :class="getEmojiColor()">{{ config.emoji }}</span>
          {{ config.name }} Bot
        </h1>
        <div class="mt-2 flex items-center space-x-4 text-sm">
          <span 
            v-for="achievement in config.achievements" 
            :key="achievement.label"
            :class="[achievement.bg, achievement.text]"
            class="px-3 py-1 rounded-full font-semibold"
          >
            {{ achievement.label }}
          </span>
        </div>
      </div>
      
      <!-- Status Indicator -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
        <div class="text-center">
          <div class="flex items-center justify-center mb-2">
            <div :class="botStatus.isRunning ? 'bg-emerald-400' : 'bg-slate-400'" class="w-3 h-3 rounded-full mr-2"></div>
            <span class="font-semibold text-slate-700">
              {{ getStatusText() }}
            </span>
          </div>
          <div class="text-xs text-slate-500">{{ botStatus.lastCheck || 'Nunca' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  botStatus: {
    type: Object,
    required: true
  },
  getStatusText: {
    type: Function,
    required: true
  }
})

// Función para obtener colores CSS estáticos
const getEmojiColor = () => {
  switch (props.config.name?.toLowerCase()) {
    case 'bitcoin':
      return 'text-yellow-600'
    case 'ethereum':
      return 'text-purple-600'
    case 'bnb':
      return 'text-yellow-600'
    default:
      return 'text-yellow-600'
  }
}
</script>