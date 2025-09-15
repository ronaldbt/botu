<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2">
          Suscripción Premium
        </h1>
        <p class="text-slate-600">Elige el plan que mejor se adapte a tus necesidades de trading</p>
      </div>

      <!-- Current Subscription Status -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-slate-900">Tu Suscripción Actual</h2>
          <span :class="getSubscriptionStatusClass()" 
                class="px-3 py-1 rounded-full text-sm font-medium">
            {{ getSubscriptionStatusText() }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <div class="text-sm text-slate-600">Plan Actual</div>
            <div class="text-xl font-bold text-slate-900">{{ getPlanName() }}</div>
          </div>

          <div v-if="subscription.start_date">
            <div class="text-sm text-slate-600">Fecha de Inicio</div>
            <div class="text-lg font-semibold text-slate-900">{{ formatDate(subscription.start_date) }}</div>
          </div>

          <div v-if="subscription.end_date">
            <div class="text-sm text-slate-600">Vencimiento</div>
            <div class="text-lg font-semibold text-slate-900">{{ formatDate(subscription.end_date) }}</div>
          </div>

          <div v-if="subscription.last_payment_date">
            <div class="text-sm text-slate-600">Último Pago</div>
            <div class="text-lg font-semibold text-slate-900">{{ formatDate(subscription.last_payment_date) }}</div>
          </div>
        </div>
      </div>

      <!-- Pricing Plans -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <!-- Alerts Plan -->
        <div class="bg-white rounded-lg shadow-sm border border-blue-200 p-6 relative">
          <div class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <span class="bg-blue-600 text-white px-3 py-1 rounded-full text-xs font-medium">
              ALERTAS
            </span>
          </div>

          <div class="text-center mb-6">
            <h3 class="text-xl font-bold text-slate-900 mb-2">🚨 Plan Alertas</h3>
            <div class="text-2xl font-bold text-blue-600 mb-1">Alertas Telegram</div>
            <div class="text-lg font-semibold text-blue-600">BTC, ETH y BNB</div>
          </div>

          <ul class="space-y-3 mb-6">
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Alertas Telegram para BTC, ETH y BNB
            </li>
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Histórico completo de señales
            </li>
            <li class="flex items-center text-sm">
              <span class="text-red-500 mr-2">❌</span>
              Sin trading automático
            </li>
          </ul>

          <button 
            v-if="subscription.plan !== 'alerts'" 
            @click="showPaymentModal('alerts')"
            class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
          >
            Suscribirme - $20/mes
          </button>
          <div v-else class="w-full py-3 px-4 bg-blue-100 text-blue-800 rounded-lg text-center font-medium">
            Plan Actual
          </div>
        </div>

        <!-- Trading Plan -->
        <div class="bg-white rounded-lg shadow-lg border border-emerald-200 p-6 relative transform scale-105">
          <div class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <span class="bg-emerald-600 text-white px-3 py-1 rounded-full text-xs font-medium">
              RECOMENDADO
            </span>
          </div>

          <div class="text-center mb-6">
            <h3 class="text-xl font-bold text-slate-900 mb-2">🤖 Plan Trading</h3>
            <div class="text-3xl font-bold text-emerald-600 mb-1">15%</div>
            <div class="text-slate-600">de ganancias</div>
          </div>

          <ul class="space-y-3 mb-6">
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Trading automático BTC, ETH y BNB
            </li>
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Ejecución automática de órdenes
            </li>
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Stop loss y take profit automático
            </li>
            <li class="flex items-center text-sm">
              <span class="text-green-500 mr-2">✅</span>
              Soporte prioritario 24/7
            </li>
            <li class="flex items-center text-sm">
              <span class="text-emerald-600 mr-2">💡</span>
              Solo pagas cuando el bot gana dinero
            </li>
          </ul>

          <button 
            v-if="subscription.plan !== 'trading'" 
            @click="showPaymentModal('trading')"
            class="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors duration-200 font-medium"
          >
            Activar Trading - 15% ganancias
          </button>
          <div v-else class="w-full py-3 px-4 bg-emerald-100 text-emerald-800 rounded-lg text-center font-medium">
            Plan Actual
          </div>
        </div>
      </div>

      <!-- Payment History -->
      <div v-if="paymentHistory.length > 0" class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h3 class="text-lg font-semibold text-slate-900 mb-4">Historial de Pagos</h3>
        
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200">
                <th class="text-left py-3 px-4">Fecha</th>
                <th class="text-left py-3 px-4">Plan</th>
                <th class="text-left py-3 px-4">Monto</th>
                <th class="text-left py-3 px-4">Estado</th>
                <th class="text-left py-3 px-4">ID PayPal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="payment in paymentHistory" :key="payment.id" class="border-b border-slate-100">
                <td class="py-3 px-4">{{ formatDate(payment.date) }}</td>
                <td class="py-3 px-4">{{ getPlanName(payment.plan) }}</td>
                <td class="py-3 px-4 font-semibold">${{ payment.amount }}</td>
                <td class="py-3 px-4">
                  <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                    {{ payment.status }}
                  </span>
                </td>
                <td class="py-3 px-4 font-mono text-xs">{{ payment.paypal_id }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-semibold text-slate-900">Pago con PayPal</h3>
          <button @click="closeModal" class="text-slate-400 hover:text-slate-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>

        <div class="mb-6">
          <div class="text-center p-6 bg-slate-50 rounded-lg mb-4">
            <div class="text-2xl font-bold text-slate-900 mb-2">
              {{ selectedPlan === 'alerts' ? '$20/mes' : '15% ganancias' }}
            </div>
            <div class="text-slate-600">
              Plan {{ selectedPlan === 'alerts' ? 'Alertas' : 'Trading' }}
            </div>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div class="flex items-start">
              <div class="text-blue-600 mr-3">ℹ️</div>
              <div>
                <h4 class="font-semibold text-blue-900 mb-2">Instrucciones de Pago</h4>
                <div v-if="selectedPlan === 'alerts'">
                  <ol class="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                    <li>Haz clic en "Pagar con PayPal" para suscribirte por $20/mes</li>
                    <li>Serás redirigido a PayPal para completar el pago</li>
                    <li>Contáctanos para activar tu suscripción</li>
                    <li>Recibirás acceso completo a alertas Telegram</li>
                  </ol>
                </div>
                <div v-else>
                  <ol class="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                    <li>Contáctanos por email para configurar el plan trading</li>
                    <li>Solo pagas 15% cuando el bot genera ganancias</li>
                    <li>Sin pagos fijos mensuales</li>
                    <li>Acceso completo al trading automático</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          <div class="text-center">
            <a 
              :href="getPayPalLink()"
              target="_blank"
              :class="selectedPlan === 'alerts' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-emerald-600 hover:bg-emerald-700'"
              class="inline-flex items-center px-6 py-3 text-white rounded-lg font-medium transition-colors duration-200"
            >
              <span class="mr-2">{{ selectedPlan === 'alerts' ? '💳' : '📧' }}</span>
              {{ selectedPlan === 'alerts' ? 'Pagar con PayPal' : 'Contactar para Trading' }}
            </a>
          </div>

          <div class="mt-4 text-center">
            <p class="text-xs text-slate-500">
              Al proceder, aceptas nuestros términos de servicio y política de privacidad
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

// Reactive data
const showModal = ref(false)
const selectedPlan = ref('')

const subscription = reactive({
  plan: 'inactive', // 'inactive', 'alerts', 'trading'
  status: 'inactive',
  start_date: null,
  end_date: null,
  last_payment_date: null
})

const paymentHistory = ref([])

// PayPal configuration - CONFIGURAR CON TUS PROPIOS LINKS DE PAYPAL
const paypalLinks = {
  alerts: 'https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-PLAN_ALERTAS_20USD',
  trading: 'mailto:admin@botu.com?subject=Activar Plan Trading - 15% Ganancias&body=Hola, quiero activar el Plan Trading con 15% de comisión sobre ganancias. Mi usuario es: [TU_USUARIO]'
}

// Methods
const formatDate = (dateString) => {
  if (!dateString) return 'No disponible'
  return new Date(dateString).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const getPlanName = (plan = null) => {
  const planToCheck = plan || subscription.plan
  const plans = {
    'inactive': '❌ Sin Suscripción',
    'alerts': '🚨 Plan Alertas',
    'trading': '🤖 Plan Trading'
  }
  return plans[planToCheck] || 'Plan Desconocido'
}

const getSubscriptionStatusClass = () => {
  const classes = {
    'active': 'bg-green-100 text-green-800',
    'inactive': 'bg-slate-100 text-slate-800',
    'suspended': 'bg-yellow-100 text-yellow-800',
    'expired': 'bg-red-100 text-red-800'
  }
  return classes[subscription.status] || 'bg-slate-100 text-slate-800'
}

const getSubscriptionStatusText = () => {
  const texts = {
    'active': '✅ Activo',
    'inactive': '⭕ Inactivo',
    'suspended': '⚠️ Suspendido',
    'expired': '❌ Expirado'
  }
  return texts[subscription.status] || 'Estado Desconocido'
}

const showPaymentModal = (plan) => {
  selectedPlan.value = plan
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedPlan.value = ''
}

const getPayPalLink = () => {
  return paypalLinks[selectedPlan.value] || paypalLinks.basic
}

// Función removida - ya no hay plan gratuito

const fetchSubscription = async () => {
  try {
    const response = await apiClient.get('/users/subscription', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    Object.assign(subscription, response.data)
    
  } catch (error) {
    console.error('Error obteniendo suscripción:', error)
  }
}

const fetchPaymentHistory = async () => {
  try {
    const response = await apiClient.get('/users/payments', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    paymentHistory.value = response.data
    
  } catch (error) {
    console.error('Error obteniendo historial de pagos:', error)
    // No mostrar error si no hay historial
    paymentHistory.value = []
  }
}

// Lifecycle
onMounted(() => {
  fetchSubscription()
  fetchPaymentHistory()
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>