<template>
  <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
    <h2 class="text-xl font-semibold text-slate-900 mb-4">Seleccionar Modo de Operación</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Manual Mode -->
      <div class="relative">
        <input type="radio" id="manual" :value="'manual'" :checked="currentMode === 'manual'" @change="changeMode('manual')" class="sr-only">
        <label for="manual" :class="[
          'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 relative',
          currentMode === 'manual' 
            ? 'border-blue-500 bg-blue-50 shadow-lg ring-2 ring-blue-200' 
            : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
        ]">
          <!-- Indicador de selección -->
          <div v-if="currentMode === 'manual'" class="absolute top-3 right-3">
            <div class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
            </div>
          </div>
          <div class="flex items-center mb-3">
            <div class="text-2xl mr-3">👁️</div>
            <div>
              <div class="font-semibold text-slate-900">Modo Manual</div>
              <div class="text-sm text-slate-600">Solo alertas - Trading manual</div>
            </div>
          </div>
          <ul class="text-sm text-slate-600 space-y-1">
            <li>• API pública de Binance</li>
            <li>• Solo notificaciones de compra/venta</li>
            <li>• Tú ejecutas las órdenes manualmente</li>
            <li>• Sin riesgo - Solo análisis</li>
          </ul>
        </label>
      </div>

      <!-- Automatic Mode -->
      <div class="relative">
        <input type="radio" id="automatic" :value="'automatic'" :checked="currentMode === 'automatic'" @change="changeMode('automatic')" class="sr-only">
        <label for="automatic" :class="[
          'block p-6 border-2 rounded-lg cursor-pointer transition-all duration-200 relative',
          currentMode === 'automatic' 
            ? 'border-emerald-500 bg-emerald-50 shadow-lg ring-2 ring-emerald-200' 
            : 'border-slate-200 hover:border-slate-300 hover:shadow-sm'
        ]">
          <!-- Indicador de selección -->
          <div v-if="currentMode === 'automatic'" class="absolute top-3 right-3">
            <div class="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
              </svg>
            </div>
          </div>
          <div class="flex items-center mb-3">
            <div class="text-2xl mr-3">🤖</div>
            <div>
              <div class="font-semibold text-slate-900">Modo Automático</div>
              <div class="text-sm text-slate-600">Trading automático - Testnet</div>
            </div>
          </div>
          <ul class="text-sm text-slate-600 space-y-1">
            <li>• Binance Testnet (dinero virtual)</li>
            <li>• Ejecuta trades automáticamente</li>
            <li>• Stop loss y take profit</li>
            <li>• Aprendizaje sin riesgo real</li>
          </ul>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { watch, unref, computed } from 'vue'

// Props y emits explícitos
const props = defineProps({
  modelValue: {
    type: String,
    default: 'manual'
  }
})

const emit = defineEmits(['update:modelValue'])

// Computed para el valor actual
const currentMode = computed(() => props.modelValue)

// Debug: Log cuando cambia el modo
watch(() => props.modelValue, (newMode) => {
  console.log('ModeSelector: Modo cambiado a:', newMode)
}, { immediate: true })

// Función para cambiar el modo
const changeMode = (mode) => {
  console.log('ModeSelector: Intentando cambiar a:', mode)
  console.log('ModeSelector: modelValue antes del cambio:', props.modelValue)
  console.log('ModeSelector: currentMode.value antes del cambio:', currentMode.value)
  
  emit('update:modelValue', mode)
  
  console.log('ModeSelector: Emitido update:modelValue con:', mode)
  console.log('ModeSelector: Después del emit - modelValue:', props.modelValue)
  console.log('ModeSelector: Después del emit - currentMode.value:', currentMode.value)
}
</script>