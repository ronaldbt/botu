<template>
  <div class="min-h-screen bg-slate-900 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Título -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">
          BotU
        </h1>
      </div>

      <!-- Formulario de login -->
      <div class="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-8">
        <h2 class="text-xl font-semibold text-white text-center mb-6">Iniciar Sesión</h2>
        
        <form @submit.prevent="login" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">Usuario</label>
            <input
              v-model="username"
              type="text"
              placeholder="Ingresa tu usuario"
              class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">Contraseña</label>
            <input
              v-model="password"
              type="password"
              placeholder="Ingresa tu contraseña"
              class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-slate-700 hover:bg-slate-600 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!loading">Iniciar Sesión</span>
            <span v-else class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Iniciando...
            </span>
          </button>

          <div v-if="error" class="bg-red-900/50 border border-red-700 rounded-lg p-4">
            <div class="flex items-center">
              <svg class="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
              <span class="text-red-300 text-sm">{{ error }}</span>
            </div>
          </div>
        </form>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import apiClient from '@/config/api';
import { useAuthStore } from '../stores/authStore';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);
const router = useRouter();
const authStore = useAuthStore();

const login = async () => {
  loading.value = true;
  error.value = '';
  
  console.log('👉 Enviando login request con:', {
    username: username.value,
    password: password.value,
  });

  try {
    const response = await apiClient.post('/auth/login', {
      username: username.value,
      password: password.value,
    });

    console.log('✅ Respuesta exitosa:', response.data);

    // Guardar token + user completo
    authStore.setAuthData(response.data.access_token, response.data.user);

    console.log('✅ Usuario guardado en authStore:', authStore.user);

    router.push('/btc-4h-mainnet');
  } catch (err) {
    console.error('❌ Error completo:', err);

    if (err.response) {
      console.error('⚠️ Respuesta del backend:', err.response.status, err.response.data);
    } else if (err.request) {
      console.error('⚠️ No se recibió respuesta, request:', err.request);
    } else {
      console.error('⚠️ Otro error:', err.message);
    }

    error.value = 'Credenciales inválidas. Intenta nuevamente.';
  } finally {
    loading.value = false;
  }
};
</script>