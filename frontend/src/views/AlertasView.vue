<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              🔔 Alertas del Sistema
            </h1>
            <p class="text-slate-600">Mantente informado sobre todas las actividades del bot</p>
          </div>
          <div class="flex items-center space-x-4">
            <div class="relative">
              <select 
                v-model="filtroTipo" 
                @change="cargarAlertas"
                class="appearance-none bg-white border border-slate-300 rounded-xl px-4 py-3 pr-8 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              >
                <option value="">Todos los tipos</option>
                <option value="PATRON_U">Patrón U</option>
                <option value="ORDEN_EJECUTADA">Orden Ejecutada</option>
                <option value="ERROR">Error</option>
              </select>
              <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
            <div class="relative">
              <input 
                v-model="filtroTicker" 
                @input="cargarAlertas"
                placeholder="Filtrar por ticker..."
                class="w-64 bg-white border border-slate-300 rounded-xl px-4 py-3 pl-10 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
              />
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
              </div>
            </div>
            <button 
              v-if="alertasNoLeidas.length > 0"
              @click="marcarTodasComoLeidas" 
              class="bg-gradient-to-r from-amber-500 to-orange-500 text-white px-6 py-3 rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              Marcar todas como leídas
            </button>
            <button 
              @click="cargarAlertas" 
              class="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Total Alertas</p>
              <p class="text-3xl font-bold text-slate-900 mt-2">{{ alertas.length }}</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM4.828 7l2.586 2.586a2 2 0 002.828 0L12.828 7H4.828z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200" :class="alertasNoLeidas.length > 0 ? 'ring-2 ring-amber-300 bg-amber-50' : ''">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">No Leídas</p>
              <p class="text-3xl font-bold text-amber-600 mt-2">{{ alertasNoLeidas.length }}</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Patrones U</p>
              <p class="text-3xl font-bold text-green-600 mt-2">{{ alertas.filter(a => a.tipo_alerta === 'PATRON_U').length }}</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-600 text-sm font-medium">Órdenes Ejecutadas</p>
              <p class="text-3xl font-bold text-blue-600 mt-2">{{ alertas.filter(a => a.tipo_alerta === 'ORDEN_EJECUTADA').length }}</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Alertas List -->
      <div class="space-y-4">
        <div 
          v-for="alerta in alertas" 
          :key="alerta.id" 
          :class="[
            'bg-white rounded-2xl shadow-lg border transition-all duration-300 cursor-pointer hover:shadow-xl transform hover:scale-[1.02]',
            alerta.leida 
              ? 'border-slate-200 opacity-75' 
              : 'border-l-4 border-l-red-500 bg-red-50/30'
          ]"
          @click="toggleLeida(alerta)"
        >
          <div class="p-6">
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center space-x-4">
                <div class="flex-shrink-0">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center" 
                       :class="{
                         'bg-gradient-to-r from-green-500 to-emerald-500': alerta.tipo_alerta === 'PATRON_U',
                         'bg-gradient-to-r from-blue-500 to-indigo-500': alerta.tipo_alerta === 'ORDEN_EJECUTADA',
                         'bg-gradient-to-r from-red-500 to-pink-500': alerta.tipo_alerta === 'ERROR'
                       }">
                    <svg v-if="alerta.tipo_alerta === 'PATRON_U'" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                    <svg v-else-if="alerta.tipo_alerta === 'ORDEN_EJECUTADA'" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <svg v-else class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center space-x-3 mb-2">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                          :class="{
                            'bg-green-100 text-green-800': alerta.tipo_alerta === 'PATRON_U',
                            'bg-blue-100 text-blue-800': alerta.tipo_alerta === 'ORDEN_EJECUTADA',
                            'bg-red-100 text-red-800': alerta.tipo_alerta === 'ERROR'
                          }">
                      {{ getTipoAlertaText(alerta.tipo_alerta) }}
                    </span>
                    <span class="text-lg font-bold text-slate-900">{{ alerta.ticker }}</span>
                    <span class="text-sm text-slate-500">{{ formatDate(alerta.fecha_creacion) }}</span>
                  </div>
                  <p class="text-slate-700 text-base leading-relaxed">{{ alerta.mensaje }}</p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <div v-if="!alerta.leida" class="w-3 h-3 bg-red-500 rounded-full"></div>
                <button 
                  @click.stop="eliminarAlerta(alerta.id)"
                  class="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors duration-200"
                  title="Eliminar alerta"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div v-if="alerta.nivel_ruptura || alerta.precio_actual" class="flex items-center space-x-6 pt-4 border-t border-slate-200">
              <div v-if="alerta.nivel_ruptura" class="flex items-center space-x-2">
                <span class="text-sm font-medium text-slate-600">Nivel de Ruptura:</span>
                <span class="text-sm font-bold text-slate-900">${{ alerta.nivel_ruptura.toFixed(2) }}</span>
              </div>
              <div v-if="alerta.precio_actual" class="flex items-center space-x-2">
                <span class="text-sm font-medium text-slate-600">Precio Actual:</span>
                <span class="text-sm font-bold text-slate-900">${{ alerta.precio_actual.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="alertas.length === 0" class="text-center py-12">
        <div class="w-16 h-16 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-5 5v-5zM4.828 7l2.586 2.586a2 2 0 002.828 0L12.828 7H4.828z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-slate-900 mb-2">No hay alertas</h3>
        <p class="text-slate-600">No se encontraron alertas con los filtros aplicados.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'

export default {
  name: 'AlertasView',
  setup() {
    const authStore = useAuthStore()
    const alertas = ref([])
    const filtroTipo = ref('')
    const filtroTicker = ref('')
    const loading = ref(false)

    const alertasNoLeidas = computed(() => {
      return alertas.value.filter(alerta => !alerta.leida)
    })

    const cargarAlertas = async () => {
      loading.value = true
      try {
        const params = new URLSearchParams()
        if (filtroTipo.value) params.append('tipo_alerta', filtroTipo.value)
        if (filtroTicker.value) params.append('ticker', filtroTicker.value)
        
        const response = await fetch(`/api/v1/alertas/?${params}`, {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })
        
        if (response.ok) {
          alertas.value = await response.json()
        } else {
          console.error('Error cargando alertas')
        }
      } catch (error) {
        console.error('Error:', error)
      } finally {
        loading.value = false
      }
    }

    const toggleLeida = async (alerta) => {
      try {
        const response = await fetch(`/api/v1/alertas/${alerta.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify({
            leida: !alerta.leida
          })
        })
        
        if (response.ok) {
          alerta.leida = !alerta.leida
        }
      } catch (error) {
        console.error('Error:', error)
      }
    }

    const marcarTodasComoLeidas = async () => {
      const alertasNoLeidasIds = alertasNoLeidas.value.map(a => a.id)
      
      if (alertasNoLeidasIds.length === 0) return

      try {
        const response = await fetch('/api/v1/alertas/marcar-leidas/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify(alertasNoLeidasIds)
        })
        
        if (response.ok) {
          alertas.value.forEach(alerta => {
            if (alertasNoLeidasIds.includes(alerta.id)) {
              alerta.leida = true
            }
          })
        }
      } catch (error) {
        console.error('Error:', error)
      }
    }

    const eliminarAlerta = async (alertaId) => {
      if (!confirm('¿Estás seguro de que quieres eliminar esta alerta?')) {
        return
      }

      try {
        const response = await fetch(`/api/v1/alertas/${alertaId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })
        
        if (response.ok) {
          alertas.value = alertas.value.filter(a => a.id !== alertaId)
        } else {
          alert('Error eliminando la alerta')
        }
      } catch (error) {
        console.error('Error:', error)
        alert('Error eliminando la alerta')
      }
    }

    const getTipoAlertaText = (tipo) => {
      const tipos = {
        'PATRON_U': '🚀 Patrón U',
        'ORDEN_EJECUTADA': '✅ Orden Ejecutada',
        'ERROR': '❌ Error'
      }
      return tipos[tipo] || tipo
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('es-ES')
    }

    onMounted(() => {
      cargarAlertas()
    })

    return {
      alertas,
      filtroTipo,
      filtroTicker,
      loading,
      alertasNoLeidas,
      cargarAlertas,
      toggleLeida,
      marcarTodasComoLeidas,
      eliminarAlerta,
      getTipoAlertaText,
      formatDate
    }
  }
}
</script>

<style scoped>
/* Estilos adicionales si es necesario */
</style>