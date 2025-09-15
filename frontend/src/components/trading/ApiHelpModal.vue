<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg w-full max-w-4xl max-h-screen overflow-y-auto">
      <!-- Header fijo -->
      <div class="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 rounded-t-lg">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-semibold text-slate-900 flex items-center">
            🔑 Cómo obtener API Keys de Binance
          </h3>
          <button
            @click="$emit('close')"
            class="text-slate-400 hover:text-slate-600 transition-colors duration-200"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Contenido scrolleable -->
      <div class="px-6 py-6">
        <!-- Tabs -->
        <div class="mb-6">
          <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
              <button
                @click="activeTab = 'testnet'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm',
                  activeTab === 'testnet'
                    ? 'border-emerald-500 text-emerald-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                🧪 Testnet (Recomendado)
              </button>
              <button
                @click="activeTab = 'mainnet'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm',
                  activeTab === 'mainnet'
                    ? 'border-red-500 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                💰 Mainnet (Expertos)
              </button>
              <button
                @click="activeTab = 'security'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm',
                  activeTab === 'security'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                🔒 Seguridad
              </button>
            </nav>
          </div>
        </div>

        <!-- Testnet Content -->
        <div v-if="activeTab === 'testnet'" class="space-y-6">
          <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <div class="flex items-center mb-2">
              <span class="text-2xl mr-2">✅</span>
              <h4 class="font-semibold text-emerald-800">Testnet - Entorno de Pruebas (RECOMENDADO)</h4>
            </div>
            <p class="text-emerald-700 text-sm">Usa dinero virtual para aprender y probar estrategias sin riesgo. Perfecto para principiantes y para probar nuevas configuraciones.</p>
          </div>

          <div class="space-y-6">
            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg flex items-center mb-4">
                <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">1</span>
                Crear cuenta en Binance Testnet
              </h4>
              <div class="space-y-3">
                <p class="text-gray-700">Ve a la página oficial de Binance Testnet y crea una cuenta gratuita:</p>
                <div class="bg-gray-50 p-4 rounded-lg">
                  <a 
                    href="https://testnet.binance.vision/" 
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                  >
                    🔗 Abrir Binance Testnet
                    <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                    </svg>
                  </a>
                </div>
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p class="text-blue-800 text-sm"><strong>Nota:</strong> La cuenta de testnet es completamente separada de tu cuenta real de Binance. No necesitas tener una cuenta real.</p>
                </div>
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg flex items-center mb-4">
                <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">2</span>
                Crear API Keys en Testnet
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-3">
                  <div class="flex items-start">
                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.1</span>
                    <div>
                      <p class="font-medium">Accede a API Management</p>
                      <p class="text-sm text-gray-600">Una vez logueado, ve a tu perfil (esquina superior derecha) > API Management</p>
                    </div>
                  </div>
                  <div class="flex items-start">
                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.2</span>
                    <div>
                      <p class="font-medium">Crear nueva API Key</p>
                      <p class="text-sm text-gray-600">Haz clic en "Create API" y elige un nombre descriptivo como "BotU-Trading"</p>
                    </div>
                  </div>
                  <div class="flex items-start">
                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.3</span>
                    <div>
                      <p class="font-medium">Configurar permisos</p>
                      <div class="text-sm text-gray-600 space-y-1">
                        <p>✓ <strong>Enable Spot & Margin Trading</strong> (REQUERIDO)</p>
                        <p class="text-red-600">⚠️ NO actives: Futures, Withdrawals, Internal Transfer</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="space-y-3">
                  <div class="flex items-start">
                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.4</span>
                    <div>
                      <p class="font-medium">Copiar las keys</p>
                      <p class="text-sm text-gray-600">Guarda tanto la API Key como la Secret Key</p>
                      <p class="text-xs text-orange-600">⚠️ La Secret Key solo se muestra UNA vez</p>
                    </div>
                  </div>
                  <div class="flex items-start">
                    <span class="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs font-medium mr-3 mt-1">2.5</span>
                    <div>
                      <p class="font-medium">Verificación</p>
                      <p class="text-sm text-gray-600">Puedes necesitar verificar por email o 2FA</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg flex items-center mb-4">
                <span class="bg-emerald-100 text-emerald-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">3</span>
                Obtener fondos virtuales
              </h4>
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start">
                  <span class="text-2xl mr-3">💰</span>
                  <div>
                    <p class="font-medium text-blue-900 mb-2">Faucet de Testnet</p>
                    <p class="text-blue-800 text-sm">En Testnet puedes obtener BTC, ETH, BNB y USDT virtuales GRATIS desde el "Faucet" en tu wallet. ¡Perfecto para probar el bot sin riesgo!</p>
                    <p class="text-xs text-blue-600 mt-2">Ubicación: Wallet > Spot > Faucet (en la barra lateral)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Mainnet Content -->
        <div v-if="activeTab === 'mainnet'" class="space-y-6">
          <div class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-center mb-2">
              <span class="text-2xl mr-2">⚠️</span>
              <h4 class="font-semibold text-red-800">Mainnet - Trading con Dinero Real (SOLO EXPERTOS)</h4>
            </div>
            <p class="text-red-700 text-sm">Requiere experiencia previa y puede resultar en pérdidas reales de dinero. Usa solo si ya probaste exitosamente en Testnet.</p>
          </div>

          <div class="space-y-6">
            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg flex items-center mb-4">
                <span class="bg-red-100 text-red-800 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">1</span>
                Cuenta verificada en Binance
              </h4>
              <div class="space-y-3">
                <p class="text-gray-700">Debes tener una cuenta completamente verificada en Binance:</p>
                <div class="bg-gray-50 p-4 rounded-lg">
                  <a 
                    href="https://www.binance.com/" 
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors duration-200"
                  >
                    🔗 Binance.com
                    <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                    </svg>
                  </a>
                </div>
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p class="text-yellow-800 text-sm"><strong>Requisitos:</strong> Verificación de identidad completa, activación de 2FA, y experiencia previa en trading.</p>
                </div>
              </div>
            </div>

            <div class="bg-red-100 border border-red-300 rounded-lg p-4">
              <h4 class="font-semibold text-red-800 mb-3 flex items-center">
                🚨 ADVERTENCIAS CRÍTICAS
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ul class="text-sm text-red-700 space-y-1">
                  <li>• NUNCA compartas tus API Keys con nadie</li>
                  <li>• Solo usa fondos que puedes permitirte perder</li>
                  <li>• Empieza con cantidades muy pequeñas (&lt;$50)</li>
                  <li>• Monitorea constantemente las operaciones</li>
                </ul>
                <ul class="text-sm text-red-700 space-y-1">
                  <li>• El trading automático SIEMPRE tiene riesgos</li>
                  <li>• Practica primero en Testnet por semanas</li>
                  <li>• Nunca dejes el bot sin supervisión</li>
                  <li>• Ten un plan de salida de emergencia</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Security Content -->
        <div v-if="activeTab === 'security'" class="space-y-6">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center mb-2">
              <span class="text-2xl mr-2">🔒</span>
              <h4 class="font-semibold text-blue-800">Mejores Prácticas de Seguridad</h4>
            </div>
            <p class="text-blue-700 text-sm">Protege tus API Keys y fondos con estas medidas de seguridad esenciales.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg mb-4 flex items-center">
                <span class="text-2xl mr-2">🔑</span>
                Configuración de API Keys
              </h4>
              <div class="space-y-3">
                <div class="flex items-center">
                  <span class="text-green-600 text-lg mr-2">✓</span>
                  <span class="text-sm">Solo habilita <strong>"Spot Trading"</strong></span>
                </div>
                <div class="flex items-center">
                  <span class="text-red-600 text-lg mr-2">✗</span>
                  <span class="text-sm">NUNCA habilites <strong>"Withdrawals"</strong></span>
                </div>
                <div class="flex items-center">
                  <span class="text-red-600 text-lg mr-2">✗</span>
                  <span class="text-sm">NUNCA habilites <strong>"Futures"</strong></span>
                </div>
                <div class="flex items-center">
                  <span class="text-green-600 text-lg mr-2">✓</span>
                  <span class="text-sm">Usar restricciones de IP</span>
                </div>
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg mb-4 flex items-center">
                <span class="text-2xl mr-2">📱</span>
                Autenticación de Dos Factores (2FA)
              </h4>
              <div class="space-y-3">
                <p class="text-sm text-gray-700">Activar 2FA es <strong>OBLIGATORIO</strong> para:</p>
                <ul class="text-sm text-gray-600 space-y-1 ml-4">
                  <li>• Crear API Keys</li>
                  <li>• Modificar API Keys</li>
                  <li>• Realizar withdrawals</li>
                  <li>• Acceder desde nuevos dispositivos</li>
                </ul>
                <div class="bg-green-50 p-3 rounded">
                  <p class="text-green-800 text-xs"><strong>Recomendación:</strong> Usa Google Authenticator o Authy como app de 2FA.</p>
                </div>
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg mb-4 flex items-center">
                <span class="text-2xl mr-2">🔐</span>
                Almacenamiento Seguro
              </h4>
              <div class="space-y-3">
                <div class="space-y-2">
                  <div class="flex items-center">
                    <span class="text-green-600 text-lg mr-2">✓</span>
                    <span class="text-sm">Guarda las keys en un gestor de contraseñas</span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-red-600 text-lg mr-2">✗</span>
                    <span class="text-sm">NUNCA las compartas por WhatsApp/Telegram</span>
                  </div>
                  <div class="flex items-center">
                    <span class="text-red-600 text-lg mr-2">✗</span>
                    <span class="text-sm">NUNCA las guardes en archivos sin cifrar</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-lg p-6">
              <h4 class="font-semibold text-lg mb-4 flex items-center">
                <span class="text-2xl mr-2">🚨</span>
                En caso de compromiso
              </h4>
              <ol class="text-sm text-red-700 space-y-1">
                <li><strong>1.</strong> Elimina INMEDIATAMENTE la API Key en Binance</li>
                <li><strong>2.</strong> Revisa tu historial de trades y balance</li>
                <li><strong>3.</strong> Cambia tu contraseña de Binance</li>
                <li><strong>4.</strong> Contacta al soporte de Binance</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-lg">
        <div class="flex justify-between items-center">
          <div class="text-sm text-gray-600">
            📚 <strong>Recomendación:</strong> Siempre prueba primero en Testnet durante al menos 1-2 semanas
          </div>
          <button
            @click="$emit('close')"
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
import { ref } from 'vue'

defineProps({
  show: {
    type: Boolean,
    required: true
  }
})

defineEmits(['close'])

const activeTab = ref('testnet')
</script>