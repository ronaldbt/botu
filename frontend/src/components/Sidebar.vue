<template>
    <aside class="fixed top-0 left-0 h-screen w-64 bg-gray-900 text-white flex flex-col z-50">
      <!-- Header -->
      <div class="flex items-center justify-center h-16 border-b border-gray-700 text-2xl font-bold">
        BotU
      </div>
  
      <!-- Menu -->
      <nav class="flex-1 overflow-y-auto">
        <ul class="p-4 space-y-2">
          <li
            v-for="item in menuItems"
            :key="item.path"
          >
            <RouterLink
              :to="item.path"
              class="flex items-center px-3 py-2 rounded hover:bg-gray-700 transition-colors"
              :class="{ 'bg-gray-700': isActive(item.path) }"
            >
              <span>{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>
  
      <!-- Footer -->
      <div class="p-4 border-t border-gray-700 text-xs text-gray-400">
        <div v-if="isLogged">
          Logueado como: <strong>{{ authStore.user?.username }}</strong>
        </div>
        <div v-else>
          No logueado
        </div>
        <div class="mt-1">BotU © 2025</div>
      </div>
    </aside>
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
  