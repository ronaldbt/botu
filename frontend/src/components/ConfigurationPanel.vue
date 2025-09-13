<template>
  <div v-if="selectedMode" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h3 class="text-lg font-semibold text-slate-900 mb-4">
      {{ config.emoji }} Estrategia {{ config.name }} Optimizada - Modo {{ selectedMode === 'manual' ? 'Manual' : 'Automático' }}
    </h3>
    
    <div :class="`bg-gradient-to-r ${config.colors.gradient} ${config.colors.border} rounded-lg p-4 mb-4`">
      <div class="flex items-center mb-2">
        <span class="text-lg mr-2">⚙️</span>
        <h4 class="font-semibold text-slate-800">Parámetros Optimizados por Backtest 2023</h4>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div class="flex items-center">
          <span class="font-medium text-slate-700 mr-2">Timeframe:</span>
          <span class="bg-white px-2 py-1 rounded text-slate-900 font-medium">{{ botConfig.timeframe }}</span>
        </div>
        <div class="flex items-center">
          <span class="font-medium text-slate-700 mr-2">Take Profit:</span>
          <span class="text-emerald-700 font-semibold">{{ botConfig.takeProfit }}%</span>
        </div>
        <div class="flex items-center">
          <span class="font-medium text-slate-700 mr-2">Stop Loss:</span>
          <span class="text-red-700 font-semibold">{{ botConfig.stopLoss }}%</span>
        </div>
      </div>
      
      <div class="mt-3 text-xs text-slate-600">
        <p>
          <strong>Patrón U:</strong> Detecta caídas del 5% seguidas de recuperación del 12% en ventanas de 4h.
          {{ selectedMode === 'automatic' 
            ? 'El bot ejecutará trades automáticamente en Testnet.' 
            : 'Solo recibirás notificaciones para ejecutar manualmente.'
          }}
        </p>
      </div>
    </div>

    <!-- Telegram Integration (Manual Mode Only) -->
    <div v-if="selectedMode === 'manual'" class="mt-6 pt-6 border-t border-slate-200">
      <div :class="`bg-gradient-to-br ${config.colors.gradient} ${config.colors.border} rounded-lg p-6`">
        <div class="flex items-center mb-4">
          <div class="text-2xl mr-3">📱</div>
          <div>
            <h4 class="font-semibold text-slate-900">Conexión con Telegram - {{ config.name }}</h4>
            <p class="text-sm text-slate-600">Recibe alertas de {{ config.name }} directamente en Telegram</p>
          </div>
        </div>

        <!-- Status Section -->
        <div class="mb-4">
          <div class="flex items-center mb-2">
            <div class="text-lg mr-2">{{ telegram.telegramStatus?.connected ? '✅' : '📱' }}</div>
            <div>
              <div class="font-semibold" :class="telegram.telegramStatus?.connected ? 'text-emerald-800' : 'text-slate-700'">
                {{ telegram.telegramStatus?.connected ? `Conectado a Telegram ${config.name}` : 'No conectado' }}
              </div>
              <div class="text-sm text-slate-600" v-if="telegram.telegramStatus?.connected">
                Estado: {{ telegram.telegramStatus.subscription_status }} - Las alertas de {{ config.name }} se enviarán automáticamente
              </div>
              <div class="text-sm text-slate-600" v-else>
                Conecta tu Telegram para recibir alertas de patrones U de {{ config.name }}
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center space-x-3">
          <button
            v-if="!telegram.telegramStatus?.connected"
            @click="telegram.generateTelegramConnection"
            :disabled="telegram.generatingQR"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
          >
            <span v-if="!telegram.generatingQR">Conectar Telegram {{ config.name }}</span>
            <span v-else class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generando...
            </span>
          </button>

          <button
            v-if="telegram.telegramStatus?.connected"
            @click="telegram.disconnectTelegram"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
          >
            Desconectar
          </button>

          <button
            v-if="telegram.telegramStatus?.connected"
            @click="telegram.sendTestAlert"
            class="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
          >
            🧪 Probar
          </button>
        </div>
      </div>
    </div>

    <!-- Bot Controls -->
    <div class="mt-6 pt-6 border-t border-slate-200">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h4 class="font-semibold text-slate-900 mb-1">Control del {{ config.name }} Bot</h4>
          <p class="text-sm text-slate-600">
            {{ selectedMode === 'manual' 
              ? 'El bot escaneará patrones y enviará alertas. No ejecutará trades automáticamente.'
              : 'El bot ejecutará trades automáticamente cuando detecte patrones en Testnet.'
            }}
          </p>
        </div>
        
        <div class="flex space-x-3">
          <button
            v-if="!botStatus.isRunning"
            @click="startBot"
            :disabled="loading"
            class="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
          >
            {{ loading ? 'Iniciando...' : `Iniciar ${config.name} Bot` }}
          </button>
          
          <button
            v-if="botStatus.isRunning"
            @click="stopBot"
            :disabled="loading"
            class="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
          >
            {{ loading ? 'Deteniendo...' : `Detener ${config.name} Bot` }}
          </button>
          
          <button
            @click="refreshStatus"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
          >
            🔄
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedMode: {
    type: String,
    required: true
  },
  config: {
    type: Object,
    required: true
  },
  botConfig: {
    type: Object,
    required: true
  },
  botStatus: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    required: true
  },
  telegram: {
    type: Object,
    required: true
  },
  startBot: {
    type: Function,
    required: true
  },
  stopBot: {
    type: Function,
    required: true
  },
  refreshStatus: {
    type: Function,
    required: true
  }
})
</script>