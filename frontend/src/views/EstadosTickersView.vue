<!-- src/views/EstadosTickersView.vue -->

<template>
    <div class="p-6">
      <h1 class="text-3xl font-bold mb-4">📊 Estados Tickers</h1>
  
      <!-- RESUMEN -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div v-for="(count, estado) in resumenEstados" :key="estado"
             :class="getEstadoClass(estado)"
             class="p-4 rounded shadow text-white font-bold text-center text-xl">
          {{ estado }}: {{ count }}
        </div>
      </div>
  
      <!-- FILTROS -->
      <div class="flex flex-wrap gap-4 mb-4">
        <select v-model="filters.tipo" class="p-2 border rounded">
          <option value="">Todos los tipos</option>
          <option value="acciones">Acciones</option>
          <option value="crypto">Crypto</option>
        </select>
  
        <select v-model="filters.pais" class="p-2 border rounded">
  <option value="">Todos los países</option>
  <option value="USA">USA</option>
  <option value="Chile">Chile</option>
  <option value="Brasil">Brasil</option>
  <option value="Argentina">Argentina</option>
</select>

  
        <select v-model="filters.estado_actual" class="p-2 border rounded">
          <option value="">Todos los estados</option>
          <option value="RUPTURA">RUPTURA</option>
          <option value="PALO_BAJANDO">PALO_BAJANDO</option>
          <option value="BASE">BASE</option>
          <option value="POST_RUPTURA">POST_RUPTURA</option>
        </select>
  
        <button @click="fetchEstados" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          🔍 Aplicar filtros
        </button>
      </div>
  
      <!-- TABLA -->
      <div class="overflow-x-auto">
        <table class="w-full table-auto border-collapse border border-gray-300">
          <thead class="bg-gray-100">
            <tr>
              <th class="border px-3 py-2">Ticker</th>
              <th class="border px-3 py-2">Estado Actual</th>
              <th class="border px-3 py-2">Tipo</th>
              <th class="border px-3 py-2">Sub-Tipo</th>
              <th class="border px-3 py-2">País</th>
              <th class="border px-3 py-2">Última Fecha Escaneo</th>
              <th class="border px-3 py-2">Próxima Fecha Escaneo</th>
              <th class="border px-3 py-2">Nivel Ruptura</th>
              <th class="border px-3 py-2">Slope Left</th>
              <th class="border px-3 py-2">Precio Cierre</th>
            </tr>
          </thead>
          <tbody>
            <tr
  v-for="estado in estados"
  :key="estado.ticker"
  :class="[
    estado.estado_actual === 'RUPTURA' ? 'bg-green-600 text-white' : 'hover:bg-gray-50'
  ]"
>

              <td class="border px-3 py-2 font-bold">{{ estado.ticker }}</td>
              <td class="border px-3 py-2">{{ estado.estado_actual }}</td>
              <td class="border px-3 py-2">{{ estado.tipo }}</td>
              <td class="border px-3 py-2">{{ estado.sub_tipo }}</td>
              <td class="border px-3 py-2">{{ estado.pais }}</td>
              <td class="border px-3 py-2">{{ estado.ultima_fecha_escaneo }}</td>
              <td class="border px-3 py-2">{{ estado.proxima_fecha_escaneo }}</td>
              <td class="border px-3 py-2">{{ estado.nivel_ruptura?.toFixed(2) }}</td>
              <td class="border px-3 py-2">{{ estado.slope_left?.toFixed(2) }}</td>
              <td class="border px-3 py-2">{{ estado.precio_cierre?.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  
  const estados = ref([])
  const resumenEstados = ref({})
  const filters = ref({
  tipo: '',
  sub_tipo: '',
  pais: '', 
  estado_actual: ''
})

  
  const fetchEstados = async () => {
    try {
      let params = {}
      if (filters.value.tipo) params.tipo = filters.value.tipo
      if (filters.value.sub_tipo) params.sub_tipo = filters.value.sub_tipo
      if (filters.value.estado_actual) params.estado_actual = filters.value.estado_actual
      if (filters.value.pais) params.pais = filters.value.pais

  
      console.log('👉 Fetching estados con params:', params)
  
      const res = await axios.get('http://localhost:8000/estados_u', { params })
  
      console.log('👉 Respuesta de /api/estados-u:', res)
  
      estados.value = res.data.estados || []
      console.log('👉 Estados asignados:', estados.value)
  
      // Construir resumen de estados
      const counts = {}
      estados.value.forEach(e => {
        counts[e.estado_actual] = (counts[e.estado_actual] || 0) + 1
      })
      resumenEstados.value = counts
  
      console.log('👉 Resumen de estados:', resumenEstados.value)
  
    } catch (err) {
      console.error('❌ Error al cargar estados:', err)
    }
  }
  
  const getEstadoClass = (estado) => {
    switch (estado) {
      case 'RUPTURA': return 'bg-green-600'
      case 'PALO_BAJANDO': return 'bg-yellow-600'
      case 'BASE': return 'bg-blue-600'
      case 'POST_RUPTURA': return 'bg-gray-600'
      default: return 'bg-gray-400'
    }
  }
  
  onMounted(() => {
    fetchEstados()
  })
  </script>
  
  <style scoped>
  /* Personalizado si quieres bordes más redondeados o efectos */
  </style>
  