<template>
  <!-- QR Code Modal -->
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg w-full max-w-md max-h-screen overflow-y-auto">
      <!-- Header fijo -->
      <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">
            Conectar con Telegram {{ cryptoName }}
          </h3>
          <button
            @click="handleClose"
            class="text-slate-400 hover:text-slate-600 transition-colors duration-200"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Contenido scrolleable -->
      <div class="px-6 py-4 space-y-4">
        <div v-if="connection" class="text-center">
          <!-- QR Code -->
          <div class="bg-white p-4 rounded-lg border-2 border-slate-200 mb-4">
            <img 
              :src="`data:image/png;base64,${connection.qr_code_base64}`" 
              :alt="`QR Code Telegram ${cryptoName}`"
              class="mx-auto max-w-full h-auto"
            />
          </div>
          
          <!-- Token Manual -->
          <div class="bg-slate-50 p-4 rounded-lg mb-4">
            <p class="text-sm text-slate-600 mb-2">O copia este link:</p>
            <div class="text-xs break-all font-mono text-slate-700 bg-white p-2 rounded border">
              {{ connection.telegram_link }}
            </div>
          </div>

          <!-- Instrucciones -->
          <div class="text-left space-y-2 text-sm text-slate-600 mb-4">
            <p><strong>Instrucciones:</strong></p>
            <p>1. Abre Telegram en tu teléfono</p>
            <p>2. Escanea el código QR o haz clic en "Abrir en Telegram"</p>
            <p>3. El bot te conectará automáticamente</p>
            <p>4. ¡Listo! Recibirás las alertas de {{ cryptoName }}</p>
          </div>

          <!-- Enlace directo -->
          <div class="mb-4">
            <a 
              :href="connection.telegram_link" 
              target="_blank"
              class="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors duration-200"
            >
              <span class="mr-2">📱</span>
              Abrir en Telegram
            </a>
          </div>

          <!-- Tiempo de expiración con contador y barra de progreso -->
          <div class="text-xs text-slate-500 mb-4">
            <div v-if="timeLeft > 0" class="space-y-2">
              <!-- Contador -->
              <div class="flex items-center justify-center space-x-2">
                <div class="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
                <span class="font-mono">Expira en: {{ formatTimeLeft(timeLeft) }}</span>
              </div>
              
              <!-- Barra de progreso -->
              <div class="w-full bg-slate-200 rounded-full h-2">
                <div 
                  class="bg-gradient-to-r from-green-500 to-orange-500 h-2 rounded-full transition-all duration-1000"
                  :style="{ width: `${(timeLeft / 180) * 100}%` }"
                ></div>
              </div>
              
              <!-- Porcentaje -->
              <div class="text-xs text-slate-400">
                {{ Math.round((timeLeft / 180) * 100) }}% tiempo restante
              </div>
            </div>
            <div v-else class="text-red-500 font-semibold">
              ⚠️ Token expirado - Genera uno nuevo
            </div>
          </div>

          <!-- Botón Regenerar Token -->
          <div class="mb-4">
            <button
              @click="handleRegenerate"
              :disabled="regeneratingToken"
              class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              <span v-if="!regeneratingToken">🔄 Generar Nuevo Token {{ cryptoName }}</span>
              <span v-else class="flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generando...
              </span>
            </button>
          </div>
        </div>

        <!-- Loading state -->
        <div v-else class="text-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p class="text-slate-600">Generando código QR...</p>
        </div>
      </div>

      <!-- Footer fijo -->
      <div class="sticky bottom-0 bg-white border-t border-slate-200 px-6 py-4 rounded-b-lg">
        <div class="text-center">
          <button
            @click="handleClose"
            class="px-6 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  connection: {
    type: Object,
    default: null
  },
  timeLeft: {
    type: Number,
    default: 0
  },
  regeneratingToken: {
    type: Boolean,
    default: false
  },
  cryptoName: {
    type: String,
    default: 'Bitcoin'
  }
})

// Emits
const emit = defineEmits(['close', 'regenerate'])

// Computed
const formatTimeLeft = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// Handlers
const handleClose = () => {
  emit('close')
}

const handleRegenerate = () => {
  emit('regenerate')
}
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>