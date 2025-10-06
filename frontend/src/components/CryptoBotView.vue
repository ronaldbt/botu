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
      <ModeSelector :model-value="unref(cryptoBot.selectedMode)" @update:model-value="handleModeChange" />

      <!-- Configuration Panel -->
      <ConfigurationPanel
        :selected-mode="unref(cryptoBot.selectedMode)"
        :config="cryptoBot.config"
        :bot-config="unref(cryptoBot.botConfig)"
        :bot-status="unref(cryptoBot.botStatus)"
        :loading="unref(cryptoBot.loading)"
        :telegram="telegram"
        :start-bot="cryptoBot.startBot"
        :stop-bot="cryptoBot.stopBot"
        :refresh-status="cryptoBot.refreshStatus"
      />

      <!-- Current Analysis -->
      <CurrentAnalysis
        v-if="unref(cryptoBot.currentAnalysis)"
        :analysis="unref(cryptoBot.currentAnalysis)"
        :config="cryptoBot.config"
        :bot-config="unref(cryptoBot.botConfig)"
        :format-price="cryptoBot.formatPrice"
        :get-pattern-state-class="cryptoBot.getPatternStateClass"
      />

      <!-- Admin Message for non-owners -->
      <div v-if="!authStore.isOwner" class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-8">
        <div class="text-center">
          <div class="text-4xl mb-3">👤</div>
          <h3 class="text-lg font-semibold text-blue-900 mb-2">Usuario Cliente</h3>
          <p class="text-blue-700 mb-4">
            El {{ cryptoBot.config.name }} Bot está controlado por el administrador. Tú recibirás las alertas automáticamente en Telegram cuando se detecten patrones en {{ cryptoBot.config.name }}.
          </p>
          <div class="text-sm text-blue-600">
            <div><strong>Estado del Bot:</strong> {{ cryptoBot.botStatus.isRunning ? '🟢 Activo - Escaneando cada 4h' : '⭕ Inactivo' }}</div>
            <div><strong>Alertas:</strong> {{ cryptoBot.botStatus.alerts_count || 0 }} detectadas en esta sesión</div>
          </div>
        </div>
      </div>

      <!-- Scanner Logs -->
      <ScannerLogs
        :logs="unref(cryptoBot.scannerLogs)"
        :config="cryptoBot.config"
        :bot-status="unref(cryptoBot.botStatus)"
        :next-scan-countdown="unref(cryptoBot.nextScanCountdown)"
        :format-log-time="cryptoBot.formatLogTime"
        :get-log-class="cryptoBot.getLogClass"
        :get-log-text-class="cryptoBot.getLogTextClass"
        :get-log-icon="cryptoBot.getLogIcon"
        :refresh-logs="cryptoBot.fetchLogs"
      />

      <!-- Alerts Panel -->
      <AlertsPanel
        :alerts="unref(cryptoBot.alerts)"
        :config="cryptoBot.config"
        :selected-mode="unref(cryptoBot.selectedMode)"
        :format-price="cryptoBot.formatPrice"
      />

      <!-- Statistics -->
      <StatisticsPanel
        v-if="unref(cryptoBot.statistics)"
        :statistics="unref(cryptoBot.statistics)"
        :config="cryptoBot.config"
        :selected-mode="unref(cryptoBot.selectedMode)"
      />
    </div>

    <!-- Telegram QR Modal -->
    <TelegramQRModal
      :show="unref(telegram.showQRModal)"
      :connection="unref(telegram.qrConnection)"
      :time-left="unref(telegram.tokenTimeLeft)"
      :regenerating-token="unref(telegram.regeneratingToken)"
      :crypto-name="cryptoBot.config.displayName"
      @close="telegram.closeQRModal"
      @regenerate="telegram.regenerateToken"
    />
  </div>
</template>

<script setup>
import { onMounted, watch, unref } from 'vue'
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
  // Debug: Log del modo inicial
  console.log('CryptoBotView: Modo inicial:', cryptoBot.selectedMode.value)
  
  await cryptoBot.refreshStatus()
  await telegram.fetchTelegramStatus()
})

// Función para manejar el cambio de modo
const handleModeChange = (newMode) => {
  console.log('CryptoBotView: handleModeChange llamado con:', newMode)
  console.log('CryptoBotView: selectedMode antes del cambio:', cryptoBot.selectedMode.value)
  cryptoBot.selectedMode.value = newMode
  console.log('CryptoBotView: selectedMode después del cambio:', cryptoBot.selectedMode.value)
}

// Debug: Watch para cambios en el modo
watch(() => cryptoBot.selectedMode.value, (newMode, oldMode) => {
  console.log('CryptoBotView: Modo cambiado de', oldMode, 'a:', newMode)
  console.log('CryptoBotView: cryptoBot.selectedMode:', cryptoBot.selectedMode)
  console.log('CryptoBotView: cryptoBot.selectedMode.value:', cryptoBot.selectedMode.value)
})
</script>