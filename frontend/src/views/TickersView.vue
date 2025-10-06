<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-2xl md:text-4xl font-bold text-slate-900 mb-2">
              Tickers Monitoreados
            </h1>
            <p class="text-slate-600 text-sm md:text-base">Gestiona y monitorea todos los tickers disponibles para trading</p>
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Total Tickers</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ tickers.length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Crypto</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ tickers.filter(t => t.tipo === 'crypto').length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Acciones</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ tickers.filter(t => t.tipo === 'accion').length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Activos</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ tickers.filter(t => t.activo).length }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 md:p-6 mb-6 md:mb-8">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Filtros</h2>
        
        <!-- Filtro por tipo -->
        <div class="mb-4">
          <p class="text-sm font-medium text-slate-700 mb-2">Tipo de Activo</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="filter in filters"
              :key="filter"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-all duration-200',
                activeFilter === filter 
                  ? 'bg-slate-700 text-white' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              ]"
              @click="setActiveFilter(filter)"
            >
              {{ filter }}
            </button>
          </div>
        </div>

        <!-- Filtro por sub-tipo -->
        <div v-if="activeFilter !== 'Todos' && subTipos.length > 1">
          <p class="text-sm font-medium text-slate-700 mb-2">Sub-Tipo</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="sub in subTipos"
              :key="sub"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-all duration-200',
                activeSubTipo === sub 
                  ? 'bg-slate-700 text-white' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              ]"
              @click="setActiveSubTipo(sub)"
            >
              {{ sub }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tickers Table -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 class="text-lg font-semibold text-slate-900">Lista de Tickers</h2>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Ticker</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Nombre</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Tipo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Sub-Tipo</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">País</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="ticker in filteredTickers"
                :key="ticker.ticker"
                class="hover:bg-slate-50 transition-colors duration-200"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm font-semibold text-slate-900">{{ ticker.ticker }}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-900">
                  {{ ticker.nombre || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="{
                          'bg-slate-100 text-slate-800': ticker.tipo === 'crypto',
                          'bg-slate-100 text-slate-800': ticker.tipo === 'accion',
                          'bg-slate-100 text-slate-800': ticker.tipo === 'otro'
                        }">
                    {{ ticker.tipo }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ ticker.sub_tipo || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  {{ ticker.pais || '-' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
                        :class="ticker.activo 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'">
                    <div class="w-2 h-2 rounded-full mr-2"
                         :class="ticker.activo ? 'bg-green-400' : 'bg-red-400'"></div>
                    {{ ticker.activo ? 'Activo' : 'Inactivo' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div v-if="filteredTickers.length === 0" class="text-center py-12">
          <div class="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-slate-900 mb-2">No hay tickers</h3>
          <p class="text-slate-500 text-sm">No se encontraron tickers con los filtros aplicados.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import apiClient from '@/config/api';
import { useAuthStore } from '../stores/authStore';

const tickers = ref([]);
const activeFilter = ref('Todos');
const activeSubTipo = ref('Todos');
const authStore = useAuthStore();

const filters = ['Todos', 'crypto', 'accion', 'otro'];

// Traer tickers de backend
const fetchTickers = async () => {
  try {
    const response = await apiClient.get('/tickers', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });
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