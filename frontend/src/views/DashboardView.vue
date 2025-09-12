<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4 md:p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div>
            <h1 class="text-2xl md:text-4xl font-bold text-slate-900 mb-2">
              Dashboard
            </h1>
            <p class="text-slate-600 text-sm md:text-base">Análisis de patrones U y señales de trading</p>
          </div>
          <button 
            @click="logout"
            class="bg-slate-700 hover:bg-slate-800 text-white px-4 md:px-6 py-2 md:py-3 rounded-lg transition-all duration-200 text-sm md:text-base border border-slate-600"
          >
            <svg class="w-4 h-4 md:w-5 md:h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
            </svg>
            Cerrar Sesión
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6 md:mb-8">
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Total Señales</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ signals.length }}</p>
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
              <p class="text-slate-500 text-xs md:text-sm font-medium">Señales Hoy</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ signalsHoy }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg p-4 md:p-6 shadow-sm border border-slate-200">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-500 text-xs md:text-sm font-medium">Tickers Únicos</p>
              <p class="text-xl md:text-3xl font-bold text-slate-900 mt-1 md:mt-2">{{ tickersUnicos }}</p>
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
              <p class="text-slate-500 text-xs md:text-sm font-medium">Última Señal</p>
              <p class="text-sm md:text-lg font-bold text-slate-900 mt-1 md:mt-2">{{ ultimaSeñal }}</p>
            </div>
            <div class="w-8 h-8 md:w-12 md:h-12 bg-slate-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 md:w-6 md:h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Signals List -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 class="text-lg font-semibold text-slate-900">Señales Recientes</h2>
        </div>
        
        <div v-if="signals.length === 0" class="text-center py-12">
          <div class="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
          </div>
          <h3 class="text-base font-semibold text-slate-900 mb-2">No hay señales</h3>
          <p class="text-slate-500 text-sm">El sistema aún no ha detectado patrones U.</p>
        </div>

        <div v-else class="divide-y divide-slate-200">
          <div 
            v-for="signal in signals" 
            :key="signal.id"
            class="p-4 hover:bg-slate-50 transition-colors duration-200"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                </div>
                <div>
                  <div class="flex items-center space-x-2 mb-1">
                    <span class="text-base font-semibold text-slate-900">{{ signal.ticker }}</span>
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-slate-100 text-slate-700">
                      Patrón U
                    </span>
                  </div>
                  <p class="text-xs text-slate-500">
                    {{ formatDate(signal.date) }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-base font-semibold text-slate-900">
                  ${{ signal.precio_cierre }}
                </p>
                <p class="text-xs text-slate-500">Cierre</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/config/api';
import { useAuthStore } from '../stores/authStore';
import { useRouter } from 'vue-router';

const signals = ref([]);
const authStore = useAuthStore();
const router = useRouter();

const signalsHoy = computed(() => {
  const hoy = new Date().toDateString();
  return signals.value.filter(signal => 
    new Date(signal.date).toDateString() === hoy
  ).length;
});

const tickersUnicos = computed(() => {
  const tickers = new Set(signals.value.map(signal => signal.ticker));
  return tickers.size;
});

const ultimaSeñal = computed(() => {
  if (signals.value.length === 0) return 'N/A';
  const ultima = signals.value[0];
  return `${ultima.ticker} - ${formatDate(ultima.date)}`;
});

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('es-ES');
};

const fetchSignals = async () => {
  try {
    const response = await apiClient.get('/signals', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    });
    signals.value = response.data;
  } catch (err) {
    console.error('Error fetching signals:', err);
    if (err.response && err.response.status === 401) {
      authStore.clearAuthData();
      router.push('/login');
    }
  }
};

const logout = () => {
  authStore.clearAuthData();
  router.push('/login');
};

onMounted(() => {
  fetchSignals();
});
</script>