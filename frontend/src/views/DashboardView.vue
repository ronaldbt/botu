<template>
    <div class="min-h-screen bg-gray-100 p-8">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Dashboard - Señales U</h1>
        <button @click="logout"
                class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">
          Logout
        </button>
      </div>
  
      <div v-if="signals.length === 0" class="text-gray-600">
        No hay señales.
      </div>
  
      <ul class="space-y-2">
        <li v-for="signal in signals" :key="signal.id"
            class="bg-white p-4 rounded shadow flex justify-between items-center">
          <div>
            <p class="font-semibold">📅 {{ signal.date }} - {{ signal.ticker }}</p>
            <p class="text-sm text-gray-600">Close: {{ signal.precio_cierre }}</p>
          </div>
        </li>
      </ul>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import axios from 'axios';
  import { useAuthStore } from '../stores/authStore';
  import { useRouter } from 'vue-router';
  
  const signals = ref([]);
  const authStore = useAuthStore();
  const router = useRouter();
  
  const fetchSignals = async () => {
    try {
      const response = await axios.get('http://localhost:8000/signals/', {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
        },
      });
      signals.value = response.data;
    } catch (err) {
      console.error('Error fetching signals:', err);
      if (err.response && err.response.status === 401) {
        authStore.clearAuthData(); // ✅ Usar clearAuthData
        router.push('/login');
      }
    }
  };
  
  const logout = () => {
    authStore.clearAuthData(); // ✅ Usar clearAuthData
    router.push('/login');
  };
  
  onMounted(() => {
    fetchSignals();
  });
  </script>
  