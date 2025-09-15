<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg max-w-md w-full p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-slate-900">Agregar API Key</h3>
        <button @click="closeModal" class="text-slate-400 hover:text-slate-600">
          ✕
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">API Key *</label>
          <input 
            type="text" 
            v-model="apiKeyForm.api_key"
            placeholder="Ingresa tu API Key de Binance"
            class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Secret Key *</label>
          <input 
            type="password" 
            v-model="apiKeyForm.secret_key"
            placeholder="Ingresa tu Secret Key de Binance"
            class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
        </div>

        <div class="flex items-center">
          <input 
            type="checkbox" 
            id="testnet" 
            v-model="apiKeyForm.is_testnet"
            class="mr-2"
          >
          <label for="testnet" class="text-sm text-slate-700">
            🧪 Usar Testnet (recomendado para pruebas)
          </label>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Tamaño máximo por posición (USDT)</label>
          <input 
            type="number" 
            v-model="apiKeyForm.max_position_size_usdt"
            min="10"
            max="10000"
            step="10"
            class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
        </div>

        <div class="flex gap-4 pt-4">
          <button 
            type="button" 
            @click="closeModal"
            class="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-700 py-2 px-4 rounded-lg font-medium transition-colors">
            Cancelar
          </button>
          <button 
            type="submit" 
            :disabled="submittingApiKey"
            class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-2 px-4 rounded-lg font-medium transition-colors">
            {{ submittingApiKey ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  show: {
    type: Boolean,
    required: true
  },
  apiKeyForm: {
    type: Object,
    required: true
  },
  submittingApiKey: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['close', 'submit'])

const closeModal = () => {
  emit('close')
}

const handleSubmit = () => {
  emit('submit')
}
</script>