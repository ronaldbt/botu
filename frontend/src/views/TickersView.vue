<template>
    <div class="p-4">
      <h1 class="text-2xl font-bold mb-4">📈 Tickers</h1>
  
      <!-- Filtro por tipo -->
      <div class="flex flex-wrap mb-2">
        <button
          v-for="filter in filters"
          :key="filter"
          :class="['px-3 py-1 mr-2 mb-2 rounded', activeFilter === filter ? 'bg-blue-500 text-white' : 'bg-gray-200']"
          @click="setActiveFilter(filter)"
        >
          {{ filter }}
        </button>
      </div>
  
      <!-- Filtro por sub-tipo -->
      <div v-if="activeFilter !== 'Todos'" class="flex flex-wrap mb-4">
        <button
          v-for="sub in subTipos"
          :key="sub"
          :class="['px-3 py-1 mr-2 mb-2 rounded', activeSubTipo === sub ? 'bg-green-500 text-white' : 'bg-gray-200']"
          @click="setActiveSubTipo(sub)"
        >
          {{ sub }}
        </button>
      </div>
  
      <!-- Tabla de tickers -->
      <table class="w-full text-left table-auto border">
        <thead>
          <tr class="bg-gray-100">
            <th class="p-2">Ticker</th>
            <th class="p-2">Nombre</th>
            <th class="p-2">Tipo</th>
            <th class="p-2">Sub-Tipo</th>
            <th class="p-2">País</th>
            <th class="p-2">Activo</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ticker in filteredTickers"
            :key="ticker.ticker"
            class="border-t hover:bg-gray-50"
          >
            <td class="p-2">{{ ticker.ticker }}</td>
            <td class="p-2">{{ ticker.nombre }}</td>
            <td class="p-2">{{ ticker.tipo }}</td>
            <td class="p-2">{{ ticker.sub_tipo }}</td>
            <td class="p-2">{{ ticker.pais }}</td>
            <td class="p-2">{{ ticker.activo ? '✅' : '❌' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted } from 'vue';
  import axios from 'axios';
  
  const tickers = ref([]);
  const activeFilter = ref('Todos');
  const activeSubTipo = ref('Todos');
  
  const filters = ['Todos', 'crypto', 'accion', 'otro'];
  
  // Traer tickers de backend
  const fetchTickers = async () => {
    try {
      const response = await axios.get('http://localhost:8000/tickers');
      tickers.value = response.data;
    } catch (error) {
      console.error('Error fetching tickers:', error);
    }
  };
  
  // Computar lista de sub_tipos según filtro activo
  const subTipos = computed(() => {
    if (activeFilter.value === 'Todos') return [];
    const subTipoSet = new Set(
      tickers.value
        .filter(t => t.tipo === activeFilter.value && t.sub_tipo)
        .map(t => t.sub_tipo)
    );
    return ['Todos', ...Array.from(subTipoSet).sort()];
  });
  
  // Computar tickers filtrados
  const filteredTickers = computed(() => {
    let filtered = tickers.value;
    if (activeFilter.value !== 'Todos') {
      filtered = filtered.filter(t => t.tipo === activeFilter.value);
    }
    if (activeSubTipo.value !== 'Todos') {
      filtered = filtered.filter(t => t.sub_tipo === activeSubTipo.value);
    }
    return filtered;
  });
  
  // Métodos para cambiar filtros
  const setActiveFilter = (filter) => {
    activeFilter.value = filter;
    activeSubTipo.value = 'Todos'; // reset sub tipo al cambiar tipo
  };
  
  const setActiveSubTipo = (sub) => {
    activeSubTipo.value = sub;
  };
  
  // Inicializar
  onMounted(fetchTickers);
  </script>
  