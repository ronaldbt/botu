<template>
  <div class="flex items-center space-x-4">
    <!-- Toggle Switch -->
    <div class="flex items-center bg-slate-100 rounded-lg p-1">
      <button
        @click="setEnvironment('testnet')"
        :class="[
          'px-4 py-2 rounded-md text-sm font-semibold transition-all duration-300 flex items-center space-x-2',
          environment === 'testnet'
            ? 'bg-emerald-500 text-white shadow-lg transform scale-105'
            : 'text-slate-600 hover:text-slate-800 hover:bg-slate-200'
        ]"
      >
        <span class="text-lg">🧪</span>
        <span>TESTNET</span>
        <span v-if="environment === 'testnet'" class="text-xs bg-emerald-600 px-2 py-0.5 rounded-full">ACTIVO</span>
      </button>
      
      <button
        @click="setEnvironment('mainnet')"
        :class="[
          'px-4 py-2 rounded-md text-sm font-semibold transition-all duration-300 flex items-center space-x-2',
          environment === 'mainnet'
            ? 'bg-red-500 text-white shadow-lg transform scale-105'
            : 'text-slate-600 hover:text-slate-800 hover:bg-slate-200'
        ]"
      >
        <span class="text-lg">💰</span>
        <span>MAINNET</span>
        <span v-if="environment === 'mainnet'" class="text-xs bg-red-600 px-2 py-0.5 rounded-full">ACTIVO</span>
      </button>
    </div>

    <!-- Environment Info -->
    <div class="flex items-center space-x-2">
      <div v-if="environment === 'testnet'" class="flex items-center text-emerald-600">
        <span class="text-lg mr-1">✅</span>
        <span class="text-sm font-medium">Entorno de Pruebas</span>
      </div>
      <div v-else class="flex items-center text-red-600">
        <span class="text-lg mr-1">⚠️</span>
        <span class="text-sm font-medium">Dinero Real</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'testnet',
    validator: (value) => ['testnet', 'mainnet'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const environment = ref(props.modelValue)

const setEnvironment = (newEnvironment) => {
  if (newEnvironment === environment.value) return
  
  // Confirmación especial para Mainnet
  if (newEnvironment === 'mainnet') {
    const confirmed = confirm(
      '⚠️ ADVERTENCIA: Estás cambiando a MAINNET\n\n' +
      '💰 Esto significa trading con DINERO REAL\n' +
      '🚨 Asegúrate de haber probado exitosamente en Testnet\n' +
      '💡 Recomendamos empezar con cantidades muy pequeñas\n\n' +
      '¿Estás seguro de continuar?'
    )
    
    if (!confirmed) return
  }
  
  environment.value = newEnvironment
  emit('update:modelValue', newEnvironment)
  emit('change', newEnvironment)
  
  // Persistir en localStorage
  localStorage.setItem('trading-environment', newEnvironment)
}

// Cargar desde localStorage al montar
onMounted(() => {
  const savedEnvironment = localStorage.getItem('trading-environment')
  if (savedEnvironment && ['testnet', 'mainnet'].includes(savedEnvironment)) {
    environment.value = savedEnvironment
    emit('update:modelValue', savedEnvironment)
  }
})
</script>


