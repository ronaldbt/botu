<template>
    <!-- Desktop Sidebar -->
    <aside class="hidden md:flex fixed top-0 left-0 h-screen w-64 bg-slate-900 text-white flex-col z-50 shadow-2xl border-r border-slate-700">
      <!-- Header -->
      <div class="flex items-center justify-center h-20 border-b border-slate-700 bg-gradient-to-r from-slate-800 to-slate-900">
        <div class="text-center">
          <div class="text-3xl font-bold text-white mb-1">
            BotU
          </div>
          <div class="text-xs text-slate-400 font-medium tracking-wider">
            TRADING BOT
          </div>
        </div>
      </div>
  
      <!-- Menu -->
      <nav class="flex-1 overflow-y-auto py-8">
        <ul class="px-6 space-y-2">
          <li
            v-for="item in menuItems"
            :key="item.path"
            class="group"
          >
            <RouterLink
              :to="item.path"
              class="flex items-center px-4 py-4 rounded-xl transition-all duration-300 group-hover:scale-105"
              :class="isActive(item.path) 
                ? 'bg-gradient-to-r from-slate-700 to-slate-600 text-white shadow-lg border-l-4 border-l-blue-400 transform scale-105' 
                : 'text-slate-300 hover:bg-slate-800 hover:text-white hover:shadow-md'"
            >
              <div class="flex items-center space-x-4 w-full">
                <span class="font-semibold text-sm tracking-wide">{{ item.label }}</span>
                <div v-if="isActive(item.path)" class="ml-auto">
                  <div class="w-1 h-1 rounded-full bg-blue-400"></div>
                </div>
              </div>
            </RouterLink>
          </li>
        </ul>
      </nav>
  
      <!-- User Info & Logout -->
      <div class="p-6 border-t border-slate-700 bg-gradient-to-r from-slate-800 to-slate-900">
        <div v-if="isLogged" class="space-y-4">
          <!-- User Profile -->
          <div class="flex items-center space-x-4 p-3 rounded-xl bg-slate-700/50 backdrop-blur-sm">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-sm font-bold text-white shadow-lg">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold text-white truncate">{{ authStore.user?.username }}</div>
              <div class="text-xs text-slate-400 font-medium">
                {{ isAdmin ? 'Administrador' : 'Usuario' }}
              </div>
            </div>
          </div>
          
          <!-- Logout Button -->
          <button
            @click="handleLogout"
            class="w-full flex items-center justify-center space-x-3 px-4 py-3 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white font-semibold rounded-xl transition-all duration-300 hover:shadow-lg hover:scale-105 active:scale-95"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
            </svg>
            <span class="text-sm">Cerrar Sesión</span>
          </button>
        </div>
        <div v-else class="text-center py-4">
          <div class="text-slate-400 text-sm font-medium">No logueado</div>
        </div>
        
        <!-- Footer -->
        <div class="mt-6 pt-4 border-t border-slate-600 text-center">
          <div class="text-xs text-slate-500 font-medium">BotU © 2025</div>
        </div>
      </div>
    </aside>

    <!-- Mobile Bottom Navigation -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-gradient-to-r from-slate-900 to-slate-800 text-white border-t border-slate-700 z-50 shadow-2xl">
      <div class="flex overflow-x-auto py-4 px-4 scrollbar-hide snap-x snap-mandatory">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center py-3 px-4 rounded-xl transition-all duration-300 min-w-max whitespace-nowrap mx-1 snap-start hover:scale-105"
          :class="isActive(item.path) 
            ? 'bg-gradient-to-r from-slate-700 to-slate-600 text-white shadow-lg border border-slate-500' 
            : 'text-slate-300 hover:bg-slate-800 hover:text-white hover:border hover:border-slate-600 hover:shadow-md'"
        >
          <span class="text-xs font-semibold text-center leading-tight px-1">{{ item.label }}</span>
        </RouterLink>
        
        <!-- Mobile Logout Button -->
        <button
          v-if="isLogged"
          @click="handleLogout"
          class="flex flex-col items-center py-3 px-4 rounded-xl transition-all duration-300 min-w-max whitespace-nowrap mx-1 snap-start bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white hover:scale-105 active:scale-95"
        >
          <svg class="w-4 h-4 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
          </svg>
          <span class="text-xs font-semibold text-center leading-tight">Salir</span>
        </button>
      </div>
    </nav>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { useRoute, RouterLink, useRouter } from 'vue-router';
  import { menuAdmin, menuCliente } from '../data/menu';
  import { useAuthStore } from '../stores/authStore';
  
  const authStore = useAuthStore();
  const route = useRoute();
  const router = useRouter();
  
  const isLogged = computed(() => !!authStore.user);
  const isAdmin = computed(() => authStore.user?.is_admin);
  
  const menuItems = computed(() => {
    if (isLogged.value) {
      return isAdmin.value ? menuAdmin : menuCliente;
    } else {
      return []; // Si no hay public menu, vacío
    }
  });
  
  const isActive = (path) => {
    return route.path.startsWith(path);
  };
  
  const handleLogout = () => {
    authStore.clearAuthData();
    router.push('/login');
  };
  </script>
  
  <style scoped>
  /* Ocultar scrollbar en móvil pero mantener funcionalidad de scroll */
  .scrollbar-hide {
    -ms-overflow-style: none;  /* Internet Explorer 10+ */
    scrollbar-width: none;  /* Firefox */
  }
  
  .scrollbar-hide::-webkit-scrollbar {
    display: none;  /* Safari and Chrome */
  }
  
  /* Suave scroll horizontal */
  .scrollbar-hide {
    scroll-behavior: smooth;
  }
  </style>
  