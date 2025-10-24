<template>
  <div class="mt-2 pt-6 border-t border-slate-200" v-if="false">
    <div class="rounded-lg p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
      <div class="flex items-center mb-4">
        <div class="text-2xl mr-3">📱</div>
        <div>
          <h4 class="font-semibold text-slate-900">Conexión con Telegram - {{ title }}</h4>
          <p class="text-sm text-slate-600">Recibe alertas de {{ title }} directamente en Telegram</p>
        </div>
      </div>

      <div class="mb-4">
        <div class="flex items-center mb-2">
          <div class="text-lg mr-2">{{ telegram.telegramStatus?.connected ? '✅' : '📱' }}</div>
          <div>
            <div class="font-semibold" :class="telegram.telegramStatus?.connected ? 'text-emerald-800' : 'text-slate-700'">
              {{ telegram.telegramStatus?.connected ? `Conectado a Telegram ${title}` : 'No conectado' }}
            </div>
            <div class="text-sm text-slate-600" v-if="telegram.telegramStatus?.connected">
              Estado: {{ telegram.telegramStatus.subscription_status }} - Las alertas se enviarán automáticamente
            </div>
            <div class="text-sm text-slate-600" v-else>
              Conecta tu Telegram para recibir alertas de {{ title }}
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        <button v-if="!telegram.telegramStatus?.connected"
                @click="telegram.generateTelegramConnection"
                :disabled="telegram.generatingQR?.value"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400">
          <span v-if="!telegram.generatingQR?.value">Conectar Telegram {{ title }}</span>
          <span v-else class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generando...
          </span>
        </button>

        <button v-if="telegram.telegramStatus?.connected"
                @click="telegram.disconnectTelegram"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200">
          Desconectar
        </button>

        <button v-if="telegram.telegramStatus?.connected"
                @click="telegram.sendTestAlert"
                class="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200">
          🧪 Probar
        </button>

        <button @click="telegram.fetchTelegramStatus"
                class="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                title="Refrescar estado de conexión">
          🔄 Estado
        </button>
      </div>

      <!-- Modal -->
      <TelegramQRModal
        v-if="telegram.showQRModal.value"
        :key="telegram.showQRModal.value ? 'open' : 'closed'"
        :show="telegram.showQRModal.value"
        :connection="telegram.qrConnection.value"
        :time-left="telegram.tokenTimeLeft.value"
        :regenerating-token="telegram.regeneratingToken.value"
        :crypto-name="title"
        @close="telegram.closeQRModal"
        @regenerate="telegram.regenerateToken"
      />
    </div>
  </div>
</template>

<script setup>
import TelegramQRModal from '@/components/TelegramQRModal.vue'
import { useTelegram } from '@/composables/useTelegram'

const props = defineProps({
  crypto: { type: String, required: true },
  title: { type: String, default: 'Crypto' }
})

const telegram = useTelegram(props.crypto)
</script>


