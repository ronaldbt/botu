<template>
    <div class="flex items-center justify-center min-h-screen bg-gray-100">
      <div class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4 w-full max-w-sm">
        <h1 class="text-2xl font-bold mb-6 text-center">BotU - Login</h1>
        <form @submit.prevent="login">
          <div class="mb-4">
            <input
              v-model="username"
              type="text"
              placeholder="Username"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            />
          </div>
          <div class="mb-6">
            <input
              v-model="password"
              type="password"
              placeholder="Password"
              class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            />
          </div>
          <div class="flex items-center justify-between">
            <button
              type="submit"
              class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            >
              Login
            </button>
          </div>
          <p v-if="error" class="text-red-500 text-xs italic mt-4">{{ error }}</p>
        </form>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  import axios from 'axios';
  import { useAuthStore } from '../stores/authStore';
  import { useRouter } from 'vue-router';
  
  const username = ref('');
  const password = ref('');
  const error = ref('');
  const router = useRouter();
  const authStore = useAuthStore();
  
  const login = async () => {
    console.log('👉 Enviando login request con:', {
      username: username.value,
      password: password.value,
    });
  
    try {
      const response = await axios.post('http://localhost:8000/auth/login', {
        username: username.value,
        password: password.value,
      });
  
      console.log('✅ Respuesta exitosa:', response.data);
  
      // Guardar token + user completo
      authStore.setAuthData(response.data.access_token, response.data.user);
  
      console.log('✅ Usuario guardado en authStore:', authStore.user);
  
      router.push('/dashboard');
    } catch (err) {
      console.error('❌ Error completo:', err);
  
      if (err.response) {
        console.error('⚠️ Respuesta del backend:', err.response.status, err.response.data);
      } else if (err.request) {
        console.error('⚠️ No se recibió respuesta, request:', err.request);
      } else {
        console.error('⚠️ Otro error:', err.message);
      }
  
      error.value = 'Login failed: invalid credentials';
    }
  };
  </script>
  