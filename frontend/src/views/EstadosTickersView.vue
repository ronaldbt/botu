<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-2xl md:text-4xl font-bold text-slate-900 mb-2">
              Estados de Tickers
            </h1>
            <p class="text-slate-600 text-sm md:text-base">Monitorea el estado de detección de patrones U para cada ticker</p>
          </div>
        </div>
      </div>

      <!-- Resumen de Estados -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
        <div 
          v-for="(count, estado) in resumenEstados" 
          :key="estado"
          class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">{{ estado }}</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ count }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <div class="w-3 h-3 md:w-4 md:h-4 rounded-full" :class="getEstadoDotClass(estado)"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filtros -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 md:p-6 mb-6 md:mb-8">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Filtros</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Tipo</label>
            <select 
              v-model="filters.tipo" 
              class="w-full appearance-none bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            >
              <option value="">Todos los tipos</option>
              <option value="crypto">Crypto</option>
              <option value="accion">Acciones</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Estado</label>
            <select 
              v-model="filters.estado_actual" 
              class="w-full appearance-none bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            >
              <option value="">Todos los estados</option>
              <option value="RUPTURA">RUPTURA</option>
              <option value="U_DETECTADO">U_DETECTADO</option>
              <option value="PALO_BAJANDO">PALO_BAJANDO</option>
              <option value="BASE">BASE</option>
              <option value="POST_RUPTURA">POST_RUPTURA</option>
              <option value="NO_U">NO_U</option>
            </select>
          </div>

          <div class="flex items-end">
            <button 
              @click="fetchEstados" 
              class="w-full bg-slate-700 hover:bg-slate-800 text-white px-4 py-2 rounded-lg transition-colors duration-200"
            >
              Aplicar filtros
            </button>
          </div>
        </div>
      </div>

      <!-- Tabla de Estados -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 class="text-lg font-semibold text-slate-900">Estados de Tickers</h2>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Ticker</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Estado</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Último Escaneo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Próximo Escaneo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Nivel Ruptura</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">💰 Precio Compra</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">🎯 Precio Venta</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Slope Left</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Precio Actual</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="estado in estados"
                :key="estado.ticker"
                class="hover:bg-slate-50 transition-colors duration-200"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm font-semibold text-slate-900">{{ estado.ticker }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="getEstadoBadgeClass(estado.estado_actual)">
                    <div class="w-2 h-2 rounded-full mr-2"
                         :class="getEstadoDotClass(estado.estado_actual)"></div>
                    {{ estado.estado_actual }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ estado.ultima_fecha_escaneo || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ estado.proxima_fecha_escaneo || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-medium">
                  {{ estado.nivel_ruptura ? `$${estado.nivel_ruptura.toFixed(4)}` : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold" :class="getBuyPriceClass(estado.estado_actual)">
                  {{ getPrecioCompra(estado) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-green-600">
                  {{ getPrecioVenta(estado) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ estado.slope_left ? estado.slope_left.toFixed(3) : '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-medium">
                  {{ estado.precio_cierre ? `$${estado.precio_cierre.toFixed(4)}` : '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-if="estados.length === 0" class="text-center py-12">
          <div class="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-slate-900 mb-2">No hay estados</h3>
          <p class="text-slate-500 text-sm">No se encontraron estados con los filtros aplicados.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/config/api'
import { useAuthStore } from '../stores/authStore'

const estados = ref([])
const resumenEstados = ref({})
const authStore = useAuthStore()
const filters = ref({
  tipo: '',
  estado_actual: ''
})

const fetchEstados = async () => {
  try {
    let params = {}
    if (filters.value.tipo) params.tipo = filters.value.tipo
    if (filters.value.estado_actual) params.estado_actual = filters.value.estado_actual

    const res = await apiClient.get('/estados_u', { 
      params,
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      }
    })

    estados.value = res.data.estados || []

    // Construir resumen de estados
    const counts = {}
    estados.value.forEach(e => {
      counts[e.estado_actual] = (counts[e.estado_actual] || 0) + 1
    })
    resumenEstados.value = counts

  } catch (err) {
    console.error('Error al cargar estados:', err)
  }
}

const getEstadoBadgeClass = (estado) => {
  switch (estado) {
    case 'RUPTURA': return 'bg-green-100 text-green-800'
    case 'U_DETECTADO': return 'bg-blue-100 text-blue-800'
    case 'PALO_BAJANDO': return 'bg-yellow-100 text-yellow-800'
    case 'BASE': return 'bg-slate-100 text-slate-600'
    case 'POST_RUPTURA': return 'bg-purple-100 text-purple-800'
    case 'NO_U': return 'bg-gray-100 text-gray-800'
    default: return 'bg-slate-100 text-slate-800'
  }
}

const getEstadoDotClass = (estado) => {
  switch (estado) {
    case 'RUPTURA': return 'bg-green-400'
    case 'U_DETECTADO': return 'bg-blue-400'
    case 'PALO_BAJANDO': return 'bg-yellow-400'
    case 'BASE': return 'bg-slate-400'
    case 'POST_RUPTURA': return 'bg-purple-400'
    case 'NO_U': return 'bg-gray-400'
    default: return 'bg-slate-400'
  }
}

const getPrecioCompra = (estado) => {
  // Precio de compra = nivel de ruptura (confirmación del patrón U)
  if (!estado.nivel_ruptura) return '-'
  return `$${estado.nivel_ruptura.toFixed(4)}`
}

const getPrecioVenta = (estado) => {
  // Precio de venta = nivel de ruptura + 10% (profit target)
  if (!estado.nivel_ruptura) return '-'
  const precioVenta = estado.nivel_ruptura * 1.10
  return `$${precioVenta.toFixed(4)}`
}

const getBuyPriceClass = (estado) => {
  // Destacar en verde si está en RUPTURA (listo para comprar)
  if (estado === 'RUPTURA') return 'text-green-600'
  if (estado === 'U_DETECTADO') return 'text-blue-600'
  return 'text-slate-700'
}

onMounted(() => {
  fetchEstados()
})
</script>