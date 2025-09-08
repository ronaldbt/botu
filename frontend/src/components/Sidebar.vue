<template>
    <!-- Desktop Sidebar -->
    <aside class="hidden md:flex fixed top-0 left-0 h-screen w-64 bg-slate-900 text-white flex-col z-50 shadow-2xl border-r border-slate-700">
      <!-- Header -->
      <div class="flex items-center justify-center h-16 border-b border-slate-700 bg-slate-800">
        <div class="text-center">
          <div class="text-2xl font-bold text-white">
             BotU
          </div>
        </div>
      </div>
  
      <!-- Menu -->
      <nav class="flex-1 overflow-y-auto py-6">
        <ul class="px-4 space-y-3">
          <li
            v-for="item in menuItems"
            :key="item.path"
            class="group"
          >
            <RouterLink
              :to="item.path"
              class="flex items-center px-4 py-3 rounded-lg transition-all duration-200"
              :class="isActive(item.path) 
                ? 'bg-slate-700 text-white border-l-4 border-l-white' 
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
            >
              <div class="flex items-center space-x-3">
                <div class="w-1.5 h-1.5 rounded-full bg-current opacity-70"></div>
                <span class="font-medium">{{ item.label }}</span>
              </div>
            </RouterLink>
          </li>
        </ul>
      </nav>
  
      <!-- Footer -->
      <div class="p-4 border-t border-slate-700 bg-slate-800">
        <div v-if="isLogged" class="space-y-2">
          <div class="flex items-center space-x-3">
            <div class="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-sm font-bold text-white">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="text-sm font-medium text-white">{{ authStore.user?.username }}</div>
              <div class="text-xs text-slate-400">
                {{ isAdmin ? 'Administrador' : 'Usuario' }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-2">
          <div class="text-slate-400 text-sm">No logueado</div>
        </div>
        <div class="mt-3 pt-3 border-t border-slate-600 text-center">
          <div class="text-xs text-slate-500">BotU © 2025</div>
        </div>
      </div>
    </aside>

    <!-- Mobile Bottom Navigation -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 text-white border-t border-slate-700 z-50">
      <div class="flex justify-around items-center py-3">
        <RouterLink
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex flex-col items-center py-2 px-2 rounded-lg transition-all duration-200 min-w-0 flex-1"
          :class="isActive(item.path) 
            ? 'bg-slate-700 text-white' 
            : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <div class="w-2 h-2 rounded-full bg-current opacity-70 mb-1"></div>
          <span class="text-xs font-medium text-center leading-tight">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { useRoute, RouterLink } from 'vue-router';
  import { menuAdmin, menuCliente } from '../data/menu';
  import { useAuthStore } from '../stores/authStore';
  
  const authStore = useAuthStore();
  const route = useRoute();
  
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
  </script>
  
  <style scoped>
  /* Puedes personalizar más el estilo */
  </style>
  