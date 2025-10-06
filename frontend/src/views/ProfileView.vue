<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-bold text-slate-900 mb-2 flex items-center">
          <span class="text-4xl mr-3">👤</span>
          Mi Perfil
        </h1>
        <p class="text-slate-600">Gestiona tu información personal y configuraciones de cuenta</p>
      </div>

      <!-- Profile Info Card -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex items-center mb-6">
          <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-xl font-bold mr-4">
            {{ getInitials(userProfile.username) }}
          </div>
          <div>
            <h2 class="text-xl font-semibold text-slate-900">{{ userProfile.full_name || userProfile.username }}</h2>
            <p class="text-slate-600">{{ userProfile.email || 'Email no configurado' }}</p>
            <div class="flex items-center mt-1">
              <span :class="userProfile.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'" 
                    class="px-2 py-1 rounded text-xs font-medium">
                {{ userProfile.is_admin ? '👑 Administrador' : '👤 Cliente' }}
              </span>
              <span :class="userProfile.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" 
                    class="ml-2 px-2 py-1 rounded text-xs font-medium">
                {{ userProfile.is_active ? '✅ Activo' : '❌ Inactivo' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Profile Form -->
        <form @submit.prevent="updateProfile" class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Full Name -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Nombre Completo</label>
              <input 
                type="text" 
                v-model="profileForm.full_name"
                class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Tu nombre completo"
              >
            </div>

            <!-- Email -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Email</label>
              <input 
                type="email" 
                v-model="profileForm.email"
                class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="tu@email.com"
              >
            </div>

            <!-- Phone -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">Teléfono</label>
              <input 
                type="tel" 
                v-model="profileForm.phone"
                class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="+1234567890"
              >
            </div>

            <!-- Country -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">País</label>
              <select 
                v-model="profileForm.country"
                class="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Seleccionar país</option>
                <option value="ES">España</option>
                <option value="AR">Argentina</option>
                <option value="MX">México</option>
                <option value="CO">Colombia</option>
                <option value="PE">Perú</option>
                <option value="CL">Chile</option>
                <option value="EC">Ecuador</option>
                <option value="VE">Venezuela</option>
                <option value="US">Estados Unidos</option>
                <option value="CA">Canadá</option>
                <option value="BR">Brasil</option>
                <option value="OTHER">Otro</option>
              </select>
            </div>
          </div>

          <!-- Account Info -->
          <div class="border-t border-slate-200 pt-6">
            <h3 class="text-lg font-semibold text-slate-900 mb-4">Información de la Cuenta</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">Usuario</label>
                <input 
                  type="text" 
                  :value="userProfile.username"
                  disabled
                  class="w-full bg-slate-100 border border-slate-300 rounded-lg px-3 py-2 text-slate-500"
                >
                <p class="text-xs text-slate-500 mt-1">El nombre de usuario no se puede cambiar</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-slate-700 mb-2">Fecha de Registro</label>
                <input 
                  type="text" 
                  :value="formatDate(userProfile.created_at)"
                  disabled
                  class="w-full bg-slate-100 border border-slate-300 rounded-lg px-3 py-2 text-slate-500"
                >
              </div>
            </div>
          </div>

          <!-- Update Button -->
          <div class="flex justify-end pt-6 border-t border-slate-200">
            <button
              type="submit"
              :disabled="updating"
              class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors duration-200 disabled:bg-slate-400"
            >
              <span v-if="!updating">💾 Actualizar Perfil</span>
              <span v-else class="flex items-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Actualizando...
              </span>
            </button>
          </div>
        </form>
      </div>

      <!-- Subscription Status Card -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-900">Estado de Suscripción</h3>
          <span :class="getSubscriptionStatusClass()" 
                class="px-3 py-1 rounded-full text-sm font-medium">
            {{ getSubscriptionStatusText() }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div class="text-sm text-slate-600">Plan Actual</div>
            <div class="text-lg font-semibold text-slate-900">{{ getPlanName() }}</div>
          </div>

          <div v-if="userProfile.subscription_start_date">
            <div class="text-sm text-slate-600">Fecha de Inicio</div>
            <div class="text-lg font-semibold text-slate-900">{{ formatDate(userProfile.subscription_start_date) }}</div>
          </div>

          <div v-if="userProfile.subscription_end_date">
            <div class="text-sm text-slate-600">Fecha de Vencimiento</div>
            <div class="text-lg font-semibold text-slate-900">{{ formatDate(userProfile.subscription_end_date) }}</div>
          </div>
        </div>

        <div class="mt-6 pt-6 border-t border-slate-200">
          <router-link 
            to="/subscription" 
            class="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors duration-200"
          >
            💳 Gestionar Suscripción
          </router-link>
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
const updating = ref(false)

const userProfile = reactive({
  username: '',
  full_name: '',
  email: '',
  phone: '',
  country: '',
  is_admin: false,
  is_active: false,
  created_at: '',
  subscription_plan: 'free',
  subscription_status: 'inactive',
  subscription_start_date: null,
  subscription_end_date: null
})

const profileForm = reactive({
  full_name: '',
  email: '',
  phone: '',
  country: ''
})

// Methods
const getInitials = (username) => {
  return username ? username.substring(0, 2).toUpperCase() : 'U'
}

const formatDate = (dateString) => {
  if (!dateString) return 'No disponible'
  return new Date(dateString).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getPlanName = () => {
  const plans = {
    'free': '🆓 Gratuito',
    'basic': '🥉 Básico',
    'premium': '👑 Premium'
  }
  return plans[userProfile.subscription_plan] || 'Plan Desconocido'
}

const getSubscriptionStatusClass = () => {
  const classes = {
    'active': 'bg-green-100 text-green-800',
    'inactive': 'bg-slate-100 text-slate-800',
    'suspended': 'bg-yellow-100 text-yellow-800',
    'expired': 'bg-red-100 text-red-800'
  }
  return classes[userProfile.subscription_status] || 'bg-slate-100 text-slate-800'
}

const getSubscriptionStatusText = () => {
  const texts = {
    'active': '✅ Activo',
    'inactive': '⭕ Inactivo',
    'suspended': '⚠️ Suspendido',
    'expired': '❌ Expirado'
  }
  return texts[userProfile.subscription_status] || 'Estado Desconocido'
}

const fetchProfile = async () => {
  try {
    const response = await apiClient.get('/users/profile', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    Object.assign(userProfile, response.data)
    
    // Copy to form
    profileForm.full_name = userProfile.full_name || ''
    profileForm.email = userProfile.email || ''
    profileForm.phone = userProfile.phone || ''
    profileForm.country = userProfile.country || ''
    
  } catch (error) {
    console.error('Error obteniendo perfil:', error)
  }
}

const updateProfile = async () => {
  updating.value = true
  try {
    const response = await apiClient.put('/users/profile', profileForm, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    // Update local data
    Object.assign(userProfile, response.data)
    
    console.log('Perfil actualizado exitosamente')
    
  } catch (error) {
    console.error('Error actualizando perfil:', error)
  } finally {
    updating.value = false
  }
}

// Lifecycle
onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>