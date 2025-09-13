<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <CryptoBotHeader 
        :config="cryptoBot.config" 
        :bot-status="cryptoBot.botStatus" 
        :get-status-text="cryptoBot.getStatusText" 
      />

      <!-- Mode Selector -->
      <ModeSelector v-model="cryptoBot.selectedMode" />

      <!-- Configuration Panel -->
      <ConfigurationPanel
        :selected-mode="cryptoBot.selectedMode"
        :config="cryptoBot.config"
        :bot-config="cryptoBot.botConfig"
        :bot-status="cryptoBot.botStatus"
        :loading="cryptoBot.loading"
        :telegram="telegram"
        :start-bot="cryptoBot.startBot"
        :stop-bot="cryptoBot.stopBot"
        :refresh-status="cryptoBot.refreshStatus"
      />

      <!-- Current Analysis -->
      <CurrentAnalysis
        v-if="cryptoBot.currentAnalysis"
        :analysis="cryptoBot.currentAnalysis"
        :config="cryptoBot.config"
        :bot-config="cryptoBot.botConfig"
        :format-price="cryptoBot.formatPrice"
        :get-pattern-state-class="cryptoBot.getPatternStateClass"
      />

      <!-- Admin Message for non-owners -->
      <div v-if="!authStore.isOwner" class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-8">
        <div class="text-center">
          <div class="text-4xl mb-3">👤</div>
          <h3 class="text-lg font-semibold text-blue-900 mb-2">Usuario Cliente</h3>
          <p class="text-blue-700 mb-4">
            El {{ cryptoBot.config.name }} Bot está controlado por el administrador. Tú recibirás las alertas automáticamente en Telegram cuando se detecten patrones U en {{ cryptoBot.config.name }}.
          </p>
          <div class="text-sm text-blue-600">
            <div><strong>Estado del Bot:</strong> {{ cryptoBot.botStatus.isRunning ? '🟢 Activo - Escaneando cada 4h' : '⭕ Inactivo' }}</div>
            <div><strong>Alertas:</strong> {{ cryptoBot.botStatus.alerts_count || 0 }} detectadas en esta sesión</div>
          </div>
        </div>
      </div>

      <!-- Scanner Logs -->
      <ScannerLogs
        :logs="cryptoBot.scannerLogs"
        :config="cryptoBot.config"
        :bot-status="cryptoBot.botStatus"
        :format-log-time="cryptoBot.formatLogTime"
        :get-log-class="cryptoBot.getLogClass"
        :get-log-text-class="cryptoBot.getLogTextClass"
        :get-log-icon="cryptoBot.getLogIcon"
        :refresh-logs="cryptoBot.fetchLogs"
      />

      <!-- Alerts Panel -->
      <AlertsPanel
        :alerts="cryptoBot.alerts"
        :config="cryptoBot.config"
        :selected-mode="cryptoBot.selectedMode"
        :format-price="cryptoBot.formatPrice"
      />

      <!-- Statistics -->
      <StatisticsPanel
        v-if="cryptoBot.statistics"
        :statistics="cryptoBot.statistics"
        :config="cryptoBot.config"
        :selected-mode="cryptoBot.selectedMode"
      />
    </div>

    <!-- Telegram QR Modal -->
    <TelegramQRModal
      :show="telegram.showQRModal"
      :connection="telegram.qrConnection"
      :time-left="telegram.tokenTimeLeft"
      :regenerating-token="telegram.regeneratingToken"
      :crypto-name="cryptoBot.config.displayName"
      @close="telegram.closeQRModal"
      @regenerate="telegram.regenerateToken"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useCryptoBot } from '@/composables/useCryptoBot'
import { useTelegram } from '@/composables/useTelegram'

// Components
import CryptoBotHeader from '@/components/CryptoBotHeader.vue'
import ModeSelector from '@/components/ModeSelector.vue'
import ConfigurationPanel from '@/components/ConfigurationPanel.vue'
import CurrentAnalysis from '@/components/CurrentAnalysis.vue'
import ScannerLogs from '@/components/ScannerLogs.vue'
import AlertsPanel from '@/components/AlertsPanel.vue'
import StatisticsPanel from '@/components/StatisticsPanel.vue'
import TelegramQRModal from '@/components/TelegramQRModal.vue'

// Props
const props = defineProps({
  crypto: {
    type: String,
    required: true,
    validator: (value) => ['btc', 'eth', 'bnb'].includes(value)
  }
})

// Stores and composables
const authStore = useAuthStore()
const cryptoBot = useCryptoBot(props.crypto)
const telegram = useTelegram(props.crypto)

// Lifecycle
onMounted(async () => {
  await cryptoBot.refreshStatus()
  await telegram.fetchTelegramStatus()
})
</script>